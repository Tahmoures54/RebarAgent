"""Independent physical validation for labeled cutting plans.

This module deliberately does not trust a solver's status. It checks that the
returned plan covers the requested piece lengths exactly and that every bar
respects its physical capacity after kerf.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List, Sequence, Tuple


def validate_labeled_cutting_plans(
    plans: Sequence[dict],
    requested_items: Iterable[Tuple[float, dict]],
    *,
    kerf_m: float = 0.0,
    tolerance: float = 1e-6,
) -> List[str]:
    """Return validation errors; an empty list means the plan passed.

    plans uses the optimizer's labeled shape: each plan has bar_length and
    bin containing (piece_length, label) pairs. Demand is compared by length
    multiplicity (labels are metadata and are not assumed unique). Kerf is
    conservatively charged once per cut piece, matching the optimizer's
    effective-length convention.
    """
    errors: List[str] = []
    if not math.isfinite(kerf_m) or kerf_m < 0:
        return ["kerf_m must be a finite non-negative number"]
    if not math.isfinite(tolerance) or tolerance <= 0:
        return ["tolerance must be a finite positive number"]

    requested: List[float] = []
    for item in requested_items:
        try:
            length = float(item[0])
        except (TypeError, ValueError, IndexError):
            errors.append("requested item has an invalid length")
            continue
        if not math.isfinite(length) or length <= 0:
            errors.append(f"requested piece length must be finite and positive: {length}")
            continue
        requested.append(length)

    planned: List[float] = []
    for index, plan in enumerate(plans or []):
        if not isinstance(plan, dict):
            errors.append(f"plan {index + 1} is not a mapping")
            continue
        try:
            capacity = float(plan["bar_length"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"plan {index + 1} has no valid bar_length")
            continue
        if not math.isfinite(capacity) or capacity <= 0:
            errors.append(f"plan {index + 1} bar_length must be finite and positive")
            continue
        bin_items = plan.get("bin")
        if not isinstance(bin_items, (list, tuple)):
            errors.append(f"plan {index + 1} bin must be a list")
            continue

        effective_used = 0.0
        for piece_index, item in enumerate(bin_items):
            try:
                length = float(item[0])
            except (TypeError, ValueError, IndexError):
                errors.append(f"plan {index + 1} piece {piece_index + 1} has invalid length")
                continue
            if not math.isfinite(length) or length <= 0:
                errors.append(f"plan {index + 1} piece lengths must be finite and positive")
                continue
            planned.append(length)
            effective_used += length + kerf_m

        if effective_used > capacity + tolerance:
            errors.append(
                f"plan {index + 1} exceeds bar capacity: "
                f"uses {effective_used:.6f} m of {capacity:.6f} m"
            )

    def bucket(length: float) -> int:
        return int(round(length / tolerance))

    expected_counts = Counter(bucket(length) for length in requested)
    actual_counts = Counter(bucket(length) for length in planned)
    if expected_counts != actual_counts:
        missing = expected_counts - actual_counts
        extra = actual_counts - expected_counts
        if missing:
            errors.append(f"plan is missing requested piece length bucket(s): {dict(missing)}")
        if extra:
            errors.append(f"plan contains unrequested/duplicate piece length bucket(s): {dict(extra)}")
    return errors
