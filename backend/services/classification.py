"""Threshold-based score classification.

Why threshold classification?
-----------------------------
The previous implementation used interval ranges::

    {"High Consistency": [0.85, 1.0], "Moderate Consistency": [0.7, 0.85]}

Adjacent intervals always share a boundary value (0.85 appears in both
ranges).  With ``low <= score <= high`` as the comparison, a score of
0.85 satisfies **both** ranges.  Which level "won" depended on JSON key
iteration order — fragile and implicit.

A threshold is a *point*, not an interval::

    thresholds:  [0.85, 0.70, 0.50]  (strictly descending)
    match when:  score >= 0.85  →  High Consistency
                 score >= 0.70  →  Moderate Consistency
                 score >= 0.50  →  Low Consistency
                 otherwise      →  Very Low Consistency (catch-all)

Every score compared to a point via a single inequality can satisfy at
most one threshold.  The loop breaks on first match.  The catch-all
entry (a level with no ``value``) always matches if reached, ensuring
zero gaps.  The result is mathematically provable and deterministic.

Reuse
-----
Future threshold-based metrics (e.g. a hydration index) create a JSON
config with a ``levels`` array, then::

    config = ThresholdConfig.from_file(path, higher_is_better=True, name="my_metric")
    level = config.classify(some_score)

The classifier is generic — it has no knowledge of DCI, NIS, or any
specific metric.
"""

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Threshold:
    """A single classification threshold.

    Attributes:
        label: Level name returned when this threshold matches.
        value: Numeric cutoff.  ``None`` means catch-all (always matches).
    """
    label: str
    value: float | None = None


@dataclass
class ThresholdConfig:
    """Validated threshold configuration for score classification.

    Usage::

        config = ThresholdConfig.from_file(
            "path/to/config.json",
            higher_is_better=True,
            name="DCI",
        )
        level = config.classify(0.75)
    """

    levels: list[Threshold]
    higher_is_better: bool
    name: str

    def __post_init__(self) -> None:
        """Validate configuration immediately after construction."""
        self._validate()

    # ── public API ───────────────────────────────────────────────────────

    def classify(self, score: float) -> str:
        """Classify *score* into a level.

        The first matching threshold wins.  The catch-all level
        (``value`` is ``None``) always matches if reached, so this
        method always returns a valid label for a valid config.

        Raises
        ------
        RuntimeError
            If the config has no catch-all entry (programming error —
            validation should have caught this).
        """
        for t in self.levels:
            if t.value is None:
                return t.label  # catch-all
            if self.higher_is_better:
                if score >= t.value:
                    return t.label
            else:
                if score < t.value:
                    return t.label
        raise RuntimeError(
            f"Threshold config '{self.name}': classify() reached end of "
            f"levels without a match.  The validator requires a catch-all "
            f"entry as the last level — this code should be unreachable."
        )

    # ── factories ────────────────────────────────────────────────────────

    @staticmethod
    def from_file(
        path: str,
        higher_is_better: bool,
        name: str,
    ) -> "ThresholdConfig":
        """Load and validate a threshold configuration from a JSON file.

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError:        if the configuration data is invalid.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Threshold config '{name}' not found at {path}"
            )
        with open(path, "r") as f:
            data = json.load(f)
        return ThresholdConfig.from_dict(data, higher_is_better, name)

    @staticmethod
    def from_dict(
        data: dict,
        higher_is_better: bool,
        name: str,
    ) -> "ThresholdConfig":
        """Create a ``ThresholdConfig`` from a parsed JSON dictionary.

        Values are type-checked *before* conversion so that malformed
        entries produce descriptive error messages.
        Validation runs automatically via ``__post_init__``.
        """
        levels_data = data.get("levels", [])
        levels: list[Threshold] = []

        for i, entry in enumerate(levels_data):
            label = entry.get("label", "")

            raw = entry.get("value", None)
            if raw is not None:
                # bool is a subclass of int — must be checked separately.
                if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                    raise ValueError(
                        f"Threshold config '{name}': entry {i} 'value' "
                        f"must be a number, got {type(raw).__name__}"
                    )
                value = float(raw)
            else:
                value = None

            levels.append(Threshold(label=label, value=value))

        return ThresholdConfig(
            levels=levels,
            higher_is_better=higher_is_better,
            name=name,
        )

    # ── validation ───────────────────────────────────────────────────────

    def _validate(self) -> None:
        name = self.name

        if not self.levels:
            raise ValueError(
                f"Threshold config '{name}': 'levels' list must not be empty"
            )

        catch_all_count = 0
        seen_labels: set = set()
        seen_values: set = set()

        for i, t in enumerate(self.levels):
            # --- label ---
            if not isinstance(t.label, str) or not t.label.strip():
                raise ValueError(
                    f"Threshold config '{name}': entry {i} 'label' must be "
                    f"a non-empty string, got {type(t.label).__name__}"
                )
            if t.label in seen_labels:
                raise ValueError(
                    f"Threshold config '{name}': duplicate level label "
                    f"'{t.label}' at entry {i}"
                )
            seen_labels.add(t.label)

            # --- value ---
            if t.value is None:
                catch_all_count += 1
            else:
                if t.value in seen_values:
                    raise ValueError(
                        f"Threshold config '{name}': duplicate threshold "
                        f"value {t.value} at entry {i}"
                    )
                seen_values.add(t.value)

        # --- catch-all ---
        if catch_all_count == 0:
            raise ValueError(
                f"Threshold config '{name}': missing catch-all entry "
                f"(a level with no 'value').  Add one as the last level "
                f"to cover scores below the lowest threshold."
            )
        if catch_all_count > 1:
            raise ValueError(
                f"Threshold config '{name}': at most one catch-all entry "
                f"(no 'value') allowed, found {catch_all_count}"
            )

        # The catch-all must be the last level.
        if self.levels[-1].value is not None:
            raise ValueError(
                f"Threshold config '{name}': the catch-all entry (no 'value') "
                f"must be the last entry in 'levels'"
            )

        # --- ordering ---
        values = [t.value for t in self.levels if t.value is not None]

        if len(values) >= 2:
            if self.higher_is_better:
                for i in range(len(values) - 1):
                    if values[i] <= values[i + 1]:
                        raise ValueError(
                            f"Threshold config '{name}': thresholds must be "
                            f"strictly descending (higher_is_better=True), "
                            f"but {values[i]} <= {values[i + 1]} at position {i}"
                        )
            else:
                for i in range(len(values) - 1):
                    if values[i] >= values[i + 1]:
                        raise ValueError(
                            f"Threshold config '{name}': thresholds must be "
                            f"strictly ascending (higher_is_better=False), "
                            f"but {values[i]} >= {values[i + 1]} at position {i}"
                        )
