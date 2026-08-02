"""Phase 4 — Part 5 (confidence analysis) + Part 15 (robustness matrix).

Confidence analysis
  - Aggregates the confidence of every accepted classifier output recorded in
    the Phase 4 E2E run (docs/evaluation/e2e_evaluation.csv).
  - Measures the classifier's confidence on deliberately non-food inputs
    (solid colours, gradients, noise, blank) and on a real food control, to
    confirm the 0.45 acceptance threshold separates them.

Robustness matrix
  - Pushes a controlled set of inputs (real food, non-food, solid colour,
    gradient, noise, dark, blur, tiny, corrupt bytes) through the SAME
    detection -> classification gate used by ``analyze_meal`` and records the
    outcome.  No thresholds are changed.

Outputs:
  - docs/evaluation/classifier_confidence.json
  - docs/evaluation/confidence_distribution.png
  - docs/evaluation/robustness_matrix.csv
"""

import csv
import json
import io
import os
import ast
import statistics

_TMP_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_robust_tmp.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

import numpy as np  # noqa: E402
from PIL import Image as PILImage  # noqa: E402

from backend.config import settings  # noqa: E402
from backend.services.ml_services import detector_service, classifier_service  # noqa: E402
from backend.utils.image_utils import crop_image  # noqa: E402
from backend.evaluation.phase4.helpers import out_path, write_csv, write_json  # noqa: E402

# Baseline colour for the histogram (validated sequential blue, step 450).
BAR_COLOR = "#2a78d6"


def _img_bytes(im: PILImage.Image) -> bytes:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _solid(rgb, size=(256, 256)) -> bytes:
    im = PILImage.new("RGB", size, rgb)
    return _img_bytes(im)


def _gradient(size=(256, 256)) -> bytes:
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    for x in range(size[0]):
        arr[:, x] = (int(255 * x / size[0]),) * 3
    return _img_bytes(PILImage.fromarray(arr))


def _noise(size=(256, 256)) -> bytes:
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    return _img_bytes(PILImage.fromarray(arr))


def _run_pipeline(img_bytes: bytes) -> dict:
    """Mirror analyze_meal's detection -> gate -> fallback logic on bytes."""
    row = {"input": "", "yolo_boxes": None, "outcome": "", "classifier_conf": "", "classifier_class": ""}
    try:
        detections = detector_service.detect(img_bytes)
    except Exception as e:
        row["outcome"] = "error"
        row["classifier_class"] = str(e)[:60]
        return row
    row["yolo_boxes"] = len(detections)
    if not detections:
        # full-image fallback (analyze_meal behaviour)
        try:
            classification = classifier_service.classify(img_bytes)
            row["classifier_conf"] = round(classification["confidence"], 4)
            row["classifier_class"] = classification["class_name"]
            if classification["confidence"] >= settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
                row["outcome"] = "recognized_fallback"
            else:
                row["outcome"] = "no_food_recognized"
        except Exception as e:
            row["outcome"] = "error"
            row["classifier_class"] = str(e)[:60]
        return row
    # For robustness we only need the detection-level outcome; classify first crop
    try:
        d0 = detections[0]
        x1, y1, x2, y2 = d0["box"]
        crop = crop_image(img_bytes, (int(x1), int(y1), int(x2), int(y2)))
        cls = classifier_service.classify(crop)
        row["classifier_conf"] = round(cls["confidence"], 4)
        row["classifier_class"] = cls["class_name"]
        row["outcome"] = "recognized" if cls["confidence"] >= settings.CLASSIFIER_CONFIDENCE_THRESHOLD else "low_confidence_rejected"
    except Exception as e:
        row["outcome"] = "error"
        row["classifier_class"] = str(e)[:60]
    return row


def collect_nonfood_confidences():
    """Confidence the classifier assigns to clearly non-food inputs."""
    probes = {
        "solid_red": _solid((255, 0, 0)),
        "solid_green": _solid((0, 128, 0)),
        "solid_blue": _solid((0, 0, 255)),
        "solid_white": _solid((255, 255, 255)),
        "solid_black": _solid((0, 0, 0)),
        "gradient": _gradient(),
        "gaussian_noise": _noise(),
    }
    results = {}
    for name, data in probes.items():
        try:
            c = classifier_service.classify(data)
            results[name] = {"confidence": round(c["confidence"], 4), "class": c["class_name"]}
        except Exception as e:
            results[name] = {"confidence": None, "class": f"error:{str(e)[:40]}"}
    return results


def main():
    classifier_service.load_model()
    detector_service.load_model()

    # ── Part 1: confidence distribution from E2E accepted items ──────────────
    e2e_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                            "docs", "evaluation", "e2e_evaluation.csv")
    confs = []
    low_conf_rejected_total = 0
    fallback_confs = []
    with open(e2e_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("items"):
                try:
                    # items is a Python-literal list (True/False booleans), not strict JSON
                    items = ast.literal_eval(r["items"])
                    for it in items:
                        if "conf" in it:
                            confs.append(float(it["conf"]))
                except Exception:
                    pass
            if r.get("low_conf_rejected"):
                try:
                    low_conf_rejected_total += int(r["low_conf_rejected"])
                except ValueError:
                    pass
            if r.get("classifier_fallback"):
                try:
                    val = r["classifier_fallback"].split("@")[-1]
                    fallback_confs.append(float(val))
                except (ValueError, IndexError):
                    pass

    pct = lambda xs, p: (sorted(xs)[min(len(xs) - 1, int(len(xs) * p))] if xs else None)
    confidence_stats = {
        "accepted_items": len(confs),
        "mean": round(statistics.mean(confs), 4) if confs else None,
        "median": round(statistics.median(confs), 4) if confs else None,
        "min": round(min(confs), 4) if confs else None,
        "max": round(max(confs), 4) if confs else None,
        "p25": round(pct(confs, 0.25), 4) if confs else None,
        "p75": round(pct(confs, 0.75), 4) if confs else None,
        "p95": round(pct(confs, 0.95), 4) if confs else None,
        "low_conf_rejected_total_e2e": low_conf_rejected_total,
        "fallback_confidences_no_food_cases": fallback_confs,
    }

    # ── Part 2: non-food confidence probe ────────────────────────────────────
    nonfood = collect_nonfood_confidences()
    # Real food control
    with open("datasets/sample_meal.png", "rb") as f:
        food_control = classifier_service.classify(f.read())
    nonfood["real_food_control(sample_meal)"] = {
        "confidence": round(food_control["confidence"], 4), "class": food_control["class_name"]}

    # ── Part 3: robustness matrix ────────────────────────────────────────────
    real_food_bytes = open("datasets/sample_meal.png", "rb").read()
    corrupt_bytes = b"\xff\xd8\xff\xe0 not really a jpeg at all ........."
    tiny_bytes = _solid((70, 130, 180), size=(8, 8))
    dark = _solid((12, 12, 12))
    # blur a real food image
    from PIL import ImageFilter
    with PILImage.open("datasets/sample_meal.png") as im:
        blur_im = im.convert("RGB").resize((320, 320)).filter(ImageFilter.GaussianBlur(12))
    blur_bytes = _img_bytes(blur_im)

    cases = [
        ("real_food_sample_meal", real_food_bytes),
        ("solid_color_red", _solid((255, 0, 0))),
        ("solid_color_blue", _solid((0, 0, 255))),
        ("solid_color_white", _solid((255, 255, 255))),
        ("solid_color_black", _solid((0, 0, 0))),
        ("gradient", _gradient()),
        ("gaussian_noise", _noise()),
        ("dark_image", dark),
        ("tiny_8x8", tiny_bytes),
        ("blurred_real_food", blur_bytes),
        ("corrupt_bytes", corrupt_bytes),
    ]
    matrix = []
    for name, data in cases:
        row = _run_pipeline(data)
        row["input"] = name
        matrix.append(row)

    # Cleanup: unload heavy models
    classifier_service.unload()
    detector_service.unload()

    # ── Write outputs ────────────────────────────────────────────────────────
    summary = {
        "confidence_threshold": settings.CLASSIFIER_CONFIDENCE_THRESHOLD,
        "confidence_stats": confidence_stats,
        "nonfood_confidence_probe": nonfood,
        "note": "Formal Top-1/Top-3/Top-5 and precision/recall require a labelled held-out split; none exists in the repository, so those are reported as N/A in the final report. This JSON records functional confidence evidence only.",
    }
    write_json("classifier_confidence.json", summary)

    write_csv("robustness_matrix.csv", matrix)

    # ── Confidence distribution plot ─────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
        ax.hist(confs, bins=20, range=(0.0, 1.0), color=BAR_COLOR, edgecolor="#ffffff", alpha=0.92)
        ax.axvline(settings.CLASSIFIER_CONFIDENCE_THRESHOLD, color="#d03b3b", linestyle="--", linewidth=1.6)
        ax.text(settings.CLASSIFIER_CONFIDENCE_THRESHOLD + 0.01, ax.get_ylim()[1] * 0.95,
                f"threshold {settings.CLASSIFIER_CONFIDENCE_THRESHOLD}", color="#d03b3b", fontsize=8, va="top")
        # non-food probe confidences as ticks
        for name, v in nonfood.items():
            if isinstance(v, dict) and isinstance(v.get("confidence"), (int, float)):
                ax.plot([v["confidence"]], [0], marker="v", color="#898781", markersize=6)
        ax.set_xlim(0.0, 1.0)
        ax.set_xlabel("Classifier confidence (accepted items)")
        ax.set_ylabel("Number of items")
        ax.set_title("EfficientNet-B3 confidence of accepted meal items")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e1e0d9", linewidth=0.6, alpha=0.6)
        fig.tight_layout()
        fig.savefig(out_path("confidence_distribution.png"))
        plt.close(fig)
        print("saved confidence_distribution.png")
    except Exception as e:
        print("plot skipped:", e)

    print(json.dumps(summary, indent=2, default=str))
    print("\nRobustness matrix:")
    for r in matrix:
        print(f"  {r['input']:<28} yolo={r['yolo_boxes']} outcome={r['outcome']} conf={r['classifier_conf']} class={r['classifier_class']}")
    return summary


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            classifier_service.unload()
        except Exception:
            pass
        try:
            detector_service.unload()
        except Exception:
            pass
        if os.path.exists(_TMP_DB):
            try:
                os.remove(_TMP_DB)
            except PermissionError:
                pass
