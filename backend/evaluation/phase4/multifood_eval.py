"""Phase 4 — Part 7: Multi-food / multi-object evaluation.

This module evaluates whether the YOLO food detector can localise MULTIPLE
distinct food regions in a single meal photo.

Two complementary parts, both purely functional (no model modification):

A) Upload scan — run raw YOLO inference and the production ``detect()``
   service over every locally available meal upload, recording image
   dimensions, raw box count, post-dedup box count, box coordinates,
   confidences, and the pairwise IoU of the raw boxes.

B) Controlled synthetic probes — compose images with KNOWN ground truth
   by tiling distinct real food crops side by side (2, 3 and 4 distinct
   foods, plus a same-food-twice control).  The ground-truth object count
   is known by construction (it is the number of tiles), so YOLO's
   multi-object recall can be measured without any dataset annotations.

Every result is written under docs/evaluation/multifood/.  No model
weights or thresholds are changed; the production ``detect()`` service is
used for the functional numbers.
"""

import json
import os
import sys

_TMP_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_multifood_tmp.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

import io  # noqa: E402

from PIL import Image as PILImage  # noqa: E402

from backend.config import settings  # noqa: E402
from backend.services.ml_services import detector_service, classifier_service  # noqa: E402
from backend.utils.image_utils import crop_image  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "evaluation", "multifood")
os.makedirs(OUT, exist_ok=True)

TILE = 320  # px per tile in the synthetic probes
GAP = 40    # px gutter between tiles
BG = (240, 240, 240)


def _iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def _dims(path):
    with PILImage.open(path) as im:
        return im.size


def scan_upload(fname: str) -> dict:
    path = os.path.join(settings.UPLOAD_DIR, fname)
    row = {
        "filename": fname,
        "source": "backend/uploads",
        "width": None,
        "height": None,
        "raw_yolo_boxes": None,
        "service_yolo_boxes": None,
        "box_coords": "",
        "confidences": "",
        "max_pairwise_iou": "",
        "note": "",
    }
    try:
        w, h = _dims(path)
        row["width"], row["height"] = w, h
    except Exception as e:
        row["note"] = f"dims_error:{str(e)[:60]}"
        return row

    # raw inference (all boxes YOLO emits at its default conf/NMS settings)
    raw = detector_service.model.predict(path, verbose=False)[0]
    boxes = [(float(b.xyxy[0][0]), float(b.xyxy[0][1]),
              float(b.xyxy[0][2]), float(b.xyxy[0][3]),
              float(b.conf[0])) for b in raw.boxes]
    boxes.sort(key=lambda b: -b[4])
    row["raw_yolo_boxes"] = len(boxes)
    row["box_coords"] = ";".join(
        f"{round(b[0])},{round(b[1])},{round(b[2])},{round(b[3])}" for b in boxes)
    row["confidences"] = ";".join(f"{round(b[4], 3)}" for b in boxes)
    if len(boxes) >= 2:
        row["max_pairwise_iou"] = round(max(
            _iou(boxes[i][:4], boxes[j][:4])
            for i in range(len(boxes)) for j in range(i + 1, len(boxes))), 3)
    try:
        dets = detector_service.detect(path)
        row["service_yolo_boxes"] = len(dets)
        if len(boxes) >= 2 and row["service_yolo_boxes"] == 1:
            row["note"] = "dedup collapsed overlapping food boxes"
        elif len(boxes) >= 2 and row["service_yolo_boxes"] >= 2:
            row["note"] = "multiple DISTINCT non-overlapping food boxes"
    except Exception as e:
        row["note"] = f"service_error:{str(e)[:60]}"
    return row


# Source images chosen from the E2E run where the classifier recognised a
# specific food with high confidence.  They are the *best available* proxy
# for single-food meal photos; each tile region in the probe is a distinct
# food by construction (the tiles are separate source images).
PROBE_SOURCES = {
    "idli": ["e6b5b0c1-84f6-4909-a54f-cd872ad61910.jpg", "c66f4d6a-8dd9-401f-861b-e8d8f047a75e.jpg", "ff52cb41-0142-452b-8a70-1c05a3f4cde2.jpg"],
    "pizza": ["44a1b635-eec4-4bc8-a6c0-c8dca350b9ae.jpg", "189fed7c-933f-48e0-9f5f-2a16b61b9e66.jpg", "d4835ffa-3c85-4eee-8158-f5c9740e9ee6.jpg"],
    "samosa": ["41d15f13-7a5a-4099-8cf5-bb8f2ca68d9d.jpg", "cec3c4d9-b6e5-49cc-a256-7615f7d7f822.jpg"],
    "fried_rice": ["0ba3810f-aa9b-4679-b21f-9f654c15a30b.jpg", "d3726f31-e3cd-44bc-9261-3475a9d81ebf.jpg"],
    "masala_dosa": ["6ae041e1-f146-4943-bbc8-76719d032791.jpg", "5eacf75c-5ea1-4673-848a-540a26144335.jpg"],
    "chapati": ["f0c1ff69-bf5a-4678-8bb9-9f4ca542085a.jpg", "b9f0992b-b57d-409e-88e8-b31f0ef524f9.jpg"],
}


def _load_tile(fname):
    path = os.path.join(settings.UPLOAD_DIR, fname)
    im = PILImage.open(path).convert("RGB")
    im = im.resize((TILE, TILE), PILImage.LANCZOS)
    return im


def compose_probe(food_list: list) -> PILImage.Image:
    """Place one tile per food side-by-side; returns the composite."""
    n = len(food_list)
    W = n * TILE + (n + 1) * GAP
    H = TILE + 2 * GAP
    canvas = PILImage.new("RGB", (W, H), BG)
    for i, (food, fname) in enumerate(food_list):
        x = GAP + i * (TILE + GAP)
        canvas.paste(_load_tile(fname), (x, GAP))
    return canvas


def run_probe(probe_id: str, food_list: list) -> dict:
    """Run detection + per-crop classification on a composed probe."""
    im = compose_probe(food_list)
    tmp = os.path.join(OUT, f"_{probe_id}_probe.png")
    im.save(tmp)
    row = {
        "probe_id": probe_id,
        "gt_object_count": len(food_list),
        "gt_foods": ",".join(f for f, _ in food_list),
        "service_yolo_boxes": None,
        "service_confidences": "",
        "per_crop_classifier": "",
        "detect_matched_gt": "",
        "note": "",
    }
    try:
        dets = detector_service.detect(tmp)
    except Exception as e:
        row["note"] = f"detect_error:{str(e)[:80]}"
        return row
    row["service_yolo_boxes"] = len(dets)
    row["service_confidences"] = ";".join(f"{round(d['confidence'], 3)}" for d in dets)
    crops = []
    for i, d in enumerate(dets):
        x1, y1, x2, y2 = d["box"]
        try:
            crop = crop_image(tmp, (int(x1), int(y1), int(x2), int(y2)))
            cls = classifier_service.classify(crop)
            crops.append(f"crop{i}:{cls['class_name']}@{round(cls['confidence'], 3)}")
        except Exception as e:
            crops.append(f"crop{i}:error:{str(e)[:40]}")
    row["per_crop_classifier"] = ";".join(crops)
    row["detect_matched_gt"] = "YES" if len(dets) == len(food_list) else "NO"
    return row


def main():
    uploads = sorted(os.listdir(settings.UPLOAD_DIR))
    detector_service.load_model()

    # Part A — upload scan
    rows = [scan_upload(f) for f in uploads]
    with open(os.path.join(OUT, "upload_detection_scan.csv"), "w", encoding="utf-8", newline="") as fh:
        import csv
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    multi_upload = [r for r in rows if (r["raw_yolo_boxes"] or 0) >= 2]
    distinct_multi = [r for r in rows if "DISTINCT" in r["note"]]

    # Part B — synthetic probes with known ground truth
    probes = [
        ("P2_idli_pizza", [("idli", PROBE_SOURCES["idli"][0]), ("pizza", PROBE_SOURCES["pizza"][0])]),
        ("P3_idli_pizza_samosa", [("idli", PROBE_SOURCES["idli"][0]), ("pizza", PROBE_SOURCES["pizza"][0]), ("samosa", PROBE_SOURCES["samosa"][0])]),
        ("P4_four_distinct", [("idli", PROBE_SOURCES["idli"][0]), ("pizza", PROBE_SOURCES["pizza"][0]), ("samosa", PROBE_SOURCES["samosa"][0]), ("fried_rice", PROBE_SOURCES["fried_rice"][0])]),
        ("P2_same_idli_twice", [("idli", PROBE_SOURCES["idli"][0]), ("idli", PROBE_SOURCES["idli"][1])]),
        ("P2_dosa_chapati", [("masala_dosa", PROBE_SOURCES["masala_dosa"][0]), ("chapati", PROBE_SOURCES["chapati"][0])]),
    ]
    probe_rows = [run_probe(pid, flist) for pid, flist in probes]
    with open(os.path.join(OUT, "synthetic_probes.csv"), "w", encoding="utf-8", newline="") as fh:
        import csv
        writer = csv.DictWriter(fh, fieldnames=list(probe_rows[0].keys()))
        writer.writeheader()
        writer.writerows(probe_rows)

    summary = {
        "uploads_scanned": len(uploads),
        "uploads_with_2_or_more_raw_boxes": len(multi_upload),
        "uploads_with_2_or_more_service_boxes": sum(1 for r in rows if (r["service_yolo_boxes"] or 0) >= 2),
        "uploads_with_distinct_non_overlapping_food_boxes": len(distinct_multi),
        "all_multi_uploads_were_overlapping_duplicates": all(
            (r.get("max_pairwise_iou") or 0) > 0.6 for r in multi_upload),
        "synthetic_probes": probe_rows,
        "ground_truth_note": ("No dataset annotations exist in the repository (datasets/ holds only sample_meal.png). "
                              "Synthetic probes provide known ground truth by construction. "
                              "Upload regions were NOT visually verified in the current provider session."),
        "yolo_class_count": len(detector_service.model.names),
        "yolo_classes": detector_service.model.names,
    }
    with open(os.path.join(OUT, "multifood_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    try:
        main()
    finally:
        detector_service.unload()
        classifier_service.unload()
        if os.path.exists(_TMP_DB):
            try:
                os.remove(_TMP_DB)
            except PermissionError:
                pass
