"""Shared helpers for the Phase 4 evaluation harness.

Provides path constants, CSV/JSON writers, and lazy service singletons so
each evaluation module stays small and reproducible.
"""

import csv
import json
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs", "evaluation")

_services = {}


def out_path(name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


def write_csv(name: str, rows: list, fieldnames: list | None = None):
    path = out_path(name)
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return path
    # Union of keys so rows with sparse/optional fields still serialise.
    fieldnames = fieldnames or list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return path


def write_json(name: str, data: dict):
    path = out_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def service(name: str):
    """Lazily build a service singleton so modules can import cheaply."""
    if name not in _services:
        if name == "nutrition":
            from backend.services.nutrition_service import nutrition_service
            _services[name] = nutrition_service
        elif name == "nis":
            from backend.services.indices_services import nis_service
            _services[name] = nis_service
        elif name == "dci":
            from backend.services.indices_services import dci_service
            _services[name] = dci_service
        elif name == "fusion":
            from backend.services.risk_fusion_service import fusion_service
            _services[name] = fusion_service
        elif name == "prediction":
            from backend.services.prediction_service import prediction_service
            _services[name] = prediction_service
        elif name == "recommendation":
            from backend.services.recommendation_service import explain_diet_service
            _services[name] = explain_diet_service
        elif name == "classifier":
            from backend.services.ml_services import classifier_service
            _services[name] = classifier_service
        elif name == "detector":
            from backend.services.ml_services import detector_service
            _services[name] = detector_service
        else:
            raise KeyError(name)
    return _services[name]


def timing(fn):
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000.0
