"""Tests for YOLO duplicate detection removal.

Covers:
- IoU computation (identical, no overlap, partial, containment)
- Same-class duplicate suppression with confidence ordering
- Different-class overlap (must both remain)
- Empty and single-element inputs
- Threshold boundary behaviour (just above / just below 0.6)
- Very small detections
- Equal confidence scores
- Two legitimate same-class objects (must both remain)
"""

from backend.services.ml_services import FoodDetectionService


# ── IoU computation ──────────────────────────────────────────────────────────

class TestIoU:
    def test_identical_boxes(self):
        """IoU = 1.0 for two identical boxes."""
        iou = FoodDetectionService._compute_iou(
            (10, 10, 100, 100), (10, 10, 100, 100)
        )
        assert iou == 1.0

    def test_no_overlap(self):
        """IoU = 0.0 for completely separated boxes."""
        iou = FoodDetectionService._compute_iou(
            (10, 10, 50, 50), (100, 100, 150, 150)
        )
        assert iou == 0.0

    def test_partial_overlap(self):
        """IoU between 0 and 1 for partially overlapping boxes.

        Box A: (10, 10, 100, 100)  area=8100
        Box B: (60, 60, 150, 150)  area=8100
        Intersection: (60, 60, 100, 100)  area=1600
        Union: 8100 + 8100 - 1600 = 14600
        IoU: 1600 / 14600 = 0.1096
        """
        iou = FoodDetectionService._compute_iou(
            (10, 10, 100, 100), (60, 60, 150, 150)
        )
        assert abs(iou - 0.1096) < 0.001

    def test_one_box_inside_another(self):
        """Inner box fully contained — IoU equals inner/outer ratio.

        Outer: (0, 0, 100, 100)  area=10000
        Inner: (20, 20, 80, 80)   area=3600
        Intersection = inner area = 3600
        Union = outer area = 10000
        IoU = 3600 / 10000 = 0.36
        """
        iou = FoodDetectionService._compute_iou(
            (0, 0, 100, 100), (20, 20, 80, 80)
        )
        assert abs(iou - 0.36) < 0.001

    def test_touching_boxes(self):
        """Boxes that share an edge but have zero intersection area."""
        iou = FoodDetectionService._compute_iou(
            (0, 0, 50, 50), (50, 0, 100, 50)
        )
        assert iou == 0.0

    def test_zero_area_box(self):
        """A degenerate box with zero area produces IoU 0.0."""
        iou = FoodDetectionService._compute_iou(
            (10, 10, 10, 50), (10, 10, 100, 100)
        )
        assert iou == 0.0


# ── Duplicate removal ────────────────────────────────────────────────────────

class TestRemoveDuplicates:
    def test_empty_input(self):
        """Empty list → empty result."""
        assert FoodDetectionService._remove_duplicate_detections([]) == []

    def test_single_detection(self):
        """Single detection is always kept."""
        dets = [{"name": "idli", "confidence": 0.95, "box": (10, 10, 100, 100)}]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1
        assert result[0]["name"] == "idli"

    def test_same_class_high_overlap_removes_duplicate(self):
        """Same class with IoU > 0.6 → lower-confidence detection removed."""
        dets = [
            {"name": "pav_bhaji", "confidence": 0.92, "box": (10, 10, 100, 100)},
            # IoU with #1 ≈ 0.79 (> 0.6) → duplicate
            {"name": "pav_bhaji", "confidence": 0.80, "box": (15, 15, 95, 95)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.92

    def test_same_class_low_overlap_both_kept(self):
        """Same class with IoU < 0.6 → both kept (legitimate two items)."""
        dets = [
            {"name": "samosa", "confidence": 0.90, "box": (10, 10, 60, 60)},
            # IoU with #1 ≈ 0.0 (separate) → not a duplicate
            {"name": "samosa", "confidence": 0.85, "box": (120, 10, 170, 70)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 2

    def test_different_classes_high_overlap_both_kept(self):
        """Different classes with identical boxes → both kept."""
        dets = [
            {"name": "rice", "confidence": 0.90, "box": (10, 10, 100, 100)},
            {"name": "curry", "confidence": 0.85, "box": (10, 10, 100, 100)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 2

    def test_highest_confidence_always_wins(self):
        """Among same-class duplicates, the highest-confidence box survives."""
        dets = [
            {"name": "idli", "confidence": 0.70, "box": (10, 10, 100, 100)},
            {"name": "idli", "confidence": 0.95, "box": (10, 10, 100, 100)},
            {"name": "idli", "confidence": 0.80, "box": (10, 10, 100, 100)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.95

    def test_equal_confidence_both_kept_if_low_overlap(self):
        """Equal confidence, low overlap → both kept."""
        dets = [
            {"name": "chapati", "confidence": 0.85, "box": (10, 10, 60, 60)},
            {"name": "chapati", "confidence": 0.85, "box": (100, 10, 150, 60)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 2

    def test_equal_confidence_high_overlap_keeps_first(self):
        """Equal confidence, high overlap → only first (input order) kept.

        Python's sort is stable, so when confidences are equal the
        original input order is preserved.
        """
        dets = [
            {"name": "idli", "confidence": 0.90, "box": (10, 10, 100, 100)},
            {"name": "idli", "confidence": 0.90, "box": (15, 15, 95, 95)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1
        assert result[0] is dets[0]  # same object, not just equal

    def test_contained_box_removed(self):
        """A box fully inside another of the same class is a duplicate."""
        dets = [
            {"name": "idli", "confidence": 0.95, "box": (0, 0, 100, 100)},
            # IoU = 0.36 (< 0.6) — wait, containment IoU can be low
            # because the inner box is much smaller than the outer one.
            # Let's use boxes where IoU exceeds 0.6.
            # Box (10,10,90,90) inside (0,0,100,100):
            #   Inner area=6400, outer=10000, inter=6400
            #   IoU = 6400 / (10000+6400-6400) = 6400/10000 = 0.64 > 0.6
            {"name": "idli", "confidence": 0.80, "box": (10, 10, 90, 90)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.95

    def test_very_small_detections_scaled_correctly(self):
        """IoU calculation scales correctly for small boxes."""
        dets = [
            {"name": "berry", "confidence": 0.90, "box": (100, 100, 110, 110)},
            # IoU ≈ 0.64 with #1 (> 0.6) → duplicate
            {"name": "berry", "confidence": 0.80, "box": (102, 102, 110, 110)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 1


# ── Threshold boundary ───────────────────────────────────────────────────────

class TestThresholdBoundary:
    def test_iou_just_below_threshold(self):
        """IoU = 0.59 → NOT a duplicate (strict > comparison)."""
        # Use a box pair that gives exactly ~0.588 IoU
        # Box A: width=100, height=100, area=10000
        # Box B: shifted right by 28px
        # Intersection width = 100-28 = 72
        # Intersection height = 100, area = 7200
        # Area B = 10000
        # Union = 10000 + 10000 - 7200 = 12800
        # IoU = 7200 / 12800 = 0.5625
        dets = [
            {"name": "test", "confidence": 0.90, "box": (0, 0, 100, 100)},
            {"name": "test", "confidence": 0.80, "box": (28, 0, 128, 100)},
        ]
        # IoU ≈ 0.5625 < 0.6 → both kept
        result = FoodDetectionService._remove_duplicate_detections(
            dets, iou_threshold=0.6
        )
        assert len(result) == 2

    def test_iou_just_above_threshold(self):
        """IoU = 0.62 → duplicate removed (strict > comparison)."""
        # Shift right by 24px
        # Intersection width = 100-24 = 76
        # Intersection area = 76 * 100 = 7600
        # Area B = 10000
        # Union = 10000 + 10000 - 7600 = 12400
        # IoU = 7600 / 12400 = 0.6129
        dets = [
            {"name": "test", "confidence": 0.90, "box": (0, 0, 100, 100)},
            {"name": "test", "confidence": 0.80, "box": (24, 0, 124, 100)},
        ]
        # IoU ≈ 0.6129 > 0.6 → duplicate removed
        result = FoodDetectionService._remove_duplicate_detections(
            dets, iou_threshold=0.6
        )
        assert len(result) == 1

    def test_iou_exactly_at_threshold_not_removed(self):
        """IoU exactly 0.6 → NOT a duplicate (uses > not >=)."""
        # Box A: (0,0,100,100) area=10000
        # We want IoU = 0.600 exactly.
        # IoU = inter / (area_a + area_b - inter)
        # Solve for width of intersection:
        # Let w = intersection width. Height stays 100.
        # inter = 100*w, area_b = 100*100 = 10000
        # IoU = 100w / (10000 + 10000 - 100w) = 100w / (20000 - 100w)
        # Set IoU = 0.6: 100w = 0.6(20000 - 100w) = 12000 - 60w
        # 160w = 12000, w = 75
        # So Box B starts at x=25 (100-75) and ends at x=125
        dets = [
            {"name": "test", "confidence": 0.90, "box": (0, 0, 100, 100)},
            {"name": "test", "confidence": 0.80, "box": (25, 0, 125, 100)},
        ]
        # IoU = 0.6 exactly → > 0.6 is false → not a duplicate
        result = FoodDetectionService._remove_duplicate_detections(
            dets, iou_threshold=0.6
        )
        assert len(result) == 2


# ── Multiple items, mixed classes ────────────────────────────────────────────

class TestMixedScenarios:
    def test_two_legitimate_same_class_items_separate(self):
        """Two identical items that are far apart → both kept."""
        dets = [
            {"name": "samosa", "confidence": 0.92, "box": (10, 10, 70, 70)},
            {"name": "samosa", "confidence": 0.88, "box": (150, 10, 210, 70)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 2

    def test_three_classes_with_mixed_overlaps(self):
        """Multiple classes processing in order — interleaving works."""
        dets = [
            {"name": "rice",     "confidence": 0.90, "box": (10, 10, 100, 100)},
            {"name": "rice",     "confidence": 0.85, "box": (15, 15, 95, 95)},
            {"name": "curry",    "confidence": 0.88, "box": (10, 10, 100, 100)},
            {"name": "curry",    "confidence": 0.82, "box": (15, 15, 95, 95)},
            {"name": "chapati",  "confidence": 0.75, "box": (200, 200, 250, 250)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        # rice: 2 → 1 (high overlap), curry: 2 → 1 (high overlap), chapati: 1 → 1
        assert len(result) == 3
        names = [d["name"] for d in result]
        assert names == ["rice", "curry", "chapati"]

    def test_lower_confidence_kept_if_no_overlap(self):
        """Lower-confidence detection kept when not overlapping higher one."""
        dets = [
            {"name": "idli", "confidence": 0.95, "box": (10, 10, 60, 60)},
            # IoU ≈ 0.0 — different area entirely
            {"name": "idli", "confidence": 0.90, "box": (200, 200, 260, 260)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 2

    def test_realistic_meal_scenario(self):
        """A typical meal with multiple items and one duplicate."""
        dets = [
            {"name": "rice",     "confidence": 0.95, "box": (50, 100, 200, 280)},
            {"name": "sambar",   "confidence": 0.92, "box": (220, 50, 380, 250)},
            {"name": "rice",     "confidence": 0.65, "box": (55, 110, 195, 270)},
            # duplicate of rice (IoU ≈ 0.79 > 0.6)
            {"name": "papad",    "confidence": 0.88, "box": (10, 10, 80, 80)},
            {"name": "chutney",  "confidence": 0.85, "box": (390, 300, 450, 400)},
        ]
        result = FoodDetectionService._remove_duplicate_detections(dets)
        assert len(result) == 4  # rice duplicate removed
        # Rice should be the highest-confidence one
        rice_entries = [d for d in result if d["name"] == "rice"]
        assert len(rice_entries) == 1
        assert rice_entries[0]["confidence"] == 0.95
