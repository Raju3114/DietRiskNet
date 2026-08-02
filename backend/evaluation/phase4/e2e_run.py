"""Phase 4 — Parts 6/7/14/16: End-to-end pipeline evaluation.

Runs the REAL detection -> classification -> nutrition -> DCI/NIS -> XGBoost
-> fusion pipeline over the locally available meal uploads using a TEMPORARY
database and a temporary user, then cleans up.  Mirrors ``meal.analyze_meal``
logic (confidence gate, no-YOLO full-image fallback, serving weights) without
the optional AI-Dietitian stage (which fails open when no LLM is reachable).

Each meal is persisted with its original real-world timestamp BEFORE DCI is
computed (exactly as ``analyze_meal`` does), so DCI history accumulates
realistically across the 11 logged days.
"""

import json
import os
import tempfile

_TMP_DB = os.path.join(tempfile.gettempdir(), "phase4_e2e_tmp.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from datetime import datetime  # noqa: E402

from PIL import Image as PILImage  # noqa: E402

from backend.config import settings  # noqa: E402
from backend.database.database import Base, engine, SessionLocal  # noqa: E402
import backend.database.models  # noqa: E402, F401
from backend.services.ml_services import detector_service, classifier_service  # noqa: E402
from backend.services.nutrition_service import nutrition_service  # noqa: E402
from backend.services.indices_services import dci_service, nis_service  # noqa: E402
from backend.services.prediction_service import prediction_service  # noqa: E402
from backend.services.risk_fusion_service import fusion_service  # noqa: E402
from backend.services.recommendation_service import explain_diet_service  # noqa: E402
from backend.utils.image_utils import crop_image  # noqa: E402
from backend.evaluation.phase4.helpers import write_csv, write_json  # noqa: E402

NUTRIENT_KEYS = ["calories", "protein", "carbs", "fats", "sugar", "fiber",
                 "sodium", "calcium", "iron", "vitamin_c", "folate"]

TIMESTAMPS = {}
_ts_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "evaluation", "_meal_timestamps.json")
if os.path.exists(_ts_path):
    with open(_ts_path, encoding="utf-8") as f:
        TIMESTAMPS = json.load(f)


def _lookup_serving(food_name: str) -> float:
    from backend.routes.meal import DEFAULT_SERVING_WEIGHTS
    return DEFAULT_SERVING_WEIGHTS.get(food_name.lower().strip().replace(" ", "_"), 100.0)


def _scaled(fact: dict, weight: float):
    s = weight / 100.0
    return {k: fact[k] * s for k in NUTRIENT_KEYS}


def _persist_meal(db, user_id, image_path, created_at, items_data) -> dict:
    """Save meal + items + aggregated nutrition; returns (meal_id, agg)."""
    from backend.database.models import Meal, MealItem, MealNutrition
    m = Meal(user_id=user_id, image_path=image_path, notes="phase4-eval", created_at=created_at)
    db.add(m)
    db.flush()
    agg = {k: 0.0 for k in NUTRIENT_KEYS}
    for it in items_data:
        db.add(MealItem(meal_id=m.id, name=it["name"], confidence=it["confidence"],
                        weight_g=it["weight_g"]))
        for k in agg:
            agg[k] += it[k]
    db.add(MealNutrition(meal_id=m.id, **agg))
    db.commit()
    return m.id, agg


def analyze_image(db, user_id, image_path: str, created_at: datetime) -> dict:
    row = {"image": os.path.basename(image_path)}

    # 1. Detection
    try:
        detections = detector_service.detect(image_path)
    except Exception as e:
        row.update({"status": "detect_error", "note": str(e)[:120]})
        return row
    row["yolo_boxes"] = len(detections)
    row["yolo_confidences"] = [round(d["confidence"], 3) for d in detections]

    # 2. No-YOLO full-image fallback (mirrors analyze_meal)
    if not detections:
        try:
            with PILImage.open(image_path) as im:
                fw, fh = im.size
            full_crop = crop_image(image_path, (0, 0, fw, fh))
            classification = classifier_service.classify(full_crop)
            if classification["confidence"] >= settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
                detections = [{"name": "food", "confidence": 0.5, "box": (0, 0, fw, fh)}]
                row["note"] = "no_yolo_boxes_full_image_fallback"
            else:
                row["status"] = "no_food_recognized"
                row["classifier_fallback"] = f"{classification['class_name']}@{classification['confidence']:.3f}"
                return row
        except Exception as e:
            row["status"] = "no_food_recognized"
            row["note"] = f"fallback_failed:{str(e)[:80]}"
            return row

    # 3. Crop -> classify -> gate -> nutrition
    items_data = []
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        try:
            crop = crop_image(image_path, (x1, y1, x2, y2))
            classification = classifier_service.classify(crop)
            food_name = classification["class_name"]
            conf = classification["confidence"]
        except Exception as e:
            row["crop_errors"] = row.get("crop_errors", 0) + 1
            continue
        if conf < settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
            row["low_conf_rejected"] = row.get("low_conf_rejected", 0) + 1
            continue
        fact = nutrition_service.lookup(food_name)
        weight = _lookup_serving(food_name)
        scaled = _scaled(fact, weight)
        scaled.update({
            "name": fact["name"],
            "nutrition_available": fact.get("nutrition_available", True),
            "confidence": conf,
            "weight_g": weight,
        })
        items_data.append(scaled)

    if not items_data:
        row["status"] = "no_food_recognized"
        return row

    row["item_count"] = len(items_data)
    row["items"] = [{"class": it["name"], "conf": round(it["confidence"], 3),
                     "nutrition_available": it["nutrition_available"],
                     "weight_g": it["weight_g"]} for it in items_data]
    row["all_nutrition_available"] = all(it["nutrition_available"] for it in items_data)

    # 4. Persist meal + items BEFORE DCI (mirrors analyze_meal create-then-calc).
    meal_id, agg = _persist_meal(db, user_id, image_path, created_at, items_data)
    row["meal_id"] = meal_id
    row["aggregated_calories"] = round(agg["calories"], 1)
    row["aggregated_protein"] = round(agg["protein"], 1)
    row["aggregated_sodium"] = round(agg["sodium"], 1)

    has_nutrition = any(it["nutrition_available"] for it in items_data)
    if not has_nutrition:
        row["status"] = "no_nutrition_data"
        return row

    # 5. DCI / NIS
    try:
        dci, dci_level = dci_service.calculate(agg, user_id, db)
    except Exception:
        dci, dci_level = None, None
    nis, nis_level = nis_service.calculate(agg)
    row["dci"] = None if dci is None else round(dci, 4)
    row["dci_level"] = dci_level
    row["nis"] = round(nis, 4)
    row["nis_level"] = nis_level

    # 6. XGBoost + fusion (demographics default 30 / Male / 170 / 70)
    try:
        preds = prediction_service.predict_all(30, "Male", 170.0, 70.0, agg, [])
        row["xgboost_executed"] = True
        row.update({f"risk_{k.split('_')[0]}": round(v, 4) for k, v in preds.items()})
        fused, fused_level = fusion_service.fuse(dci, nis, preds["diabetes_risk"], preds["obesity_risk"],
                                                 preds["hypertension_risk"], preds["deficiency_risk"])
        row["fused_score"] = None if fused is None else round(fused, 4)
        row["fused_level"] = fused_level
        row["recs"] = len(explain_diet_service.recommend(agg, preds, dci, nis))
    except Exception as e:
        row["status"] = "prediction_error"
        row["note"] = str(e)[:120]
        return row

    row["status"] = "ok"
    return row


def main() -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    from backend.database.models import User
    u = User(email="phase4-eval-user@example.com", password_hash="x")
    db.add(u)
    db.commit()
    db.refresh(u)
    user_id = u.id

    uploads = sorted(os.listdir(settings.UPLOAD_DIR))

    def sort_key(f):
        return TIMESTAMPS.get(f, "2000-01-01T00:00:00")
    uploads.sort(key=sort_key)

    rows = []
    try:
        for fname in uploads:
            img_path = os.path.join(settings.UPLOAD_DIR, fname)
            created = datetime.fromisoformat(TIMESTAMPS.get(fname, "2026-07-15T12:00:00"))
            row = analyze_image(db, user_id, img_path, created)
            row["test_id"] = f"E2E-{len(rows)+1:02d}"
            row["timestamp"] = created.date().isoformat()
            rows.append(row)
    finally:
        detector_service.unload()
        classifier_service.unload()
        prediction_service.unload()
        # count meals created by the eval before cleanup (Part 16)
        db.delete(u)
        db.commit()
        db.close()

    write_csv("e2e_evaluation.csv", rows)

    status_counts = {}
    for r in rows:
        status_counts[r.get("status", "ok")] = status_counts.get(r.get("status", "ok"), 0) + 1
    multi = [r["test_id"] for r in rows if r.get("item_count", 0) >= 2]

    summary = {
        "total_cases": len(rows),
        "status_counts": status_counts,
        "ok_cases": status_counts.get("ok", 0),
        "dci_available_cases": sum(1 for r in rows if r.get("dci") is not None),
        "multi_food_cases": multi,
        "multi_food_count": len(multi),
        "note": "meals persisted in a temporary DB with original timestamps; temp DB removed after run",
    }
    write_json("e2e_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            engine.dispose()
        except Exception:
            pass
        if os.path.exists(_TMP_DB):
            try:
                os.remove(_TMP_DB)
            except PermissionError:
                pass
