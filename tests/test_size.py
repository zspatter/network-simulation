import random

from organflow.clinical.size import SIZE_TOLERANCE, body_size, size_compatible
from organflow.compatibility_markers import OrganType


def test_body_size_in_plausible_adult_range():
    rng = random.Random(0)
    sizes = [body_size(rng) for _ in range(1000)]
    assert all(40.0 <= s <= 130.0 for s in sizes)
    # not a constant
    assert len(set(sizes)) > 100


def test_size_compatible_within_and_outside_tolerance():
    tol = SIZE_TOLERANCE[OrganType.Heart]
    assert size_compatible(80.0, 80.0, OrganType.Heart) is True
    assert size_compatible(80.0 * (1 + tol - 0.01), 80.0, OrganType.Heart) is True
    assert size_compatible(80.0 * (1 + tol + 0.05), 80.0, OrganType.Heart) is False
    assert size_compatible(80.0 * (1 - tol - 0.05), 80.0, OrganType.Heart) is False


def test_size_unconstrained_for_non_thoracic_organs():
    # a wild size mismatch is still fine for a kidney (no size gate)
    assert size_compatible(40.0, 130.0, OrganType.Kidney) is True
    assert size_compatible(40.0, 130.0, OrganType.Liver) is True


def test_size_skipped_when_unknown():
    assert size_compatible(None, 80.0, OrganType.Heart) is True
    assert size_compatible(80.0, None, OrganType.Lungs) is True


def test_lung_tolerance_tighter_than_heart():
    assert SIZE_TOLERANCE[OrganType.Lungs] < SIZE_TOLERANCE[OrganType.Heart]
