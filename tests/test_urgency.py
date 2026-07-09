import random

from organflow.clinical import urgency
from organflow.compatibility_markers import OrganType


def test_initial_raw_urgency_in_native_ranges():
    rng = random.Random(0)
    for _ in range(500):
        assert 6 <= urgency.initial_raw_urgency(OrganType.Liver, rng) <= 40
        assert 0 <= urgency.initial_raw_urgency(OrganType.Lungs, rng) <= 100
        assert 1 <= urgency.initial_raw_urgency(OrganType.Heart, rng) <= 6
        assert urgency.initial_raw_urgency(OrganType.Kidney, rng) == 0.0


def test_to_acuity_within_bounds_and_floored():
    for organ in OrganType:
        for raw in (0, 5, 20, 50, 100):
            a = urgency.to_acuity(organ, raw)
            assert urgency.ACUITY_FLOOR <= a <= 1.0


def test_to_acuity_monotonic_for_liver_and_inverted_for_heart():
    # liver: higher MELD -> higher acuity
    assert urgency.to_acuity(OrganType.Liver, 10) < urgency.to_acuity(OrganType.Liver, 30)
    # heart: LOWER status number is more urgent -> higher acuity
    assert urgency.to_acuity(OrganType.Heart, 1) > urgency.to_acuity(OrganType.Heart, 6)


def test_progress_raises_liver_and_lung_but_not_kidney():
    rng = random.Random(1)
    assert urgency.progress(OrganType.Liver, 20.0, 0, rng) >= 20.0
    assert urgency.progress(OrganType.Lungs, 40.0, 0, rng) >= 40.0
    assert urgency.progress(OrganType.Kidney, 0.0, 5, rng) == 0.0


def test_progress_caps_at_native_maximum():
    rng = random.Random(2)
    assert urgency.progress(OrganType.Liver, 40.0, 0, rng) == 40.0
    assert urgency.progress(OrganType.Lungs, 100.0, 0, rng) == 100.0


def test_heart_progression_only_escalates_toward_more_urgent():
    rng = random.Random(3)
    # over many draws, heart status never rises (never gets less urgent); it
    # may only fall to a more urgent tier
    results = [urgency.progress(OrganType.Heart, 4.0, 0, rng) for _ in range(200)]
    assert all(r in (3.0, 4.0) for r in results)
    assert any(r == 3.0 for r in results)  # some escalate
    # status 1 (most urgent) cannot escalate further
    assert all(urgency.progress(OrganType.Heart, 1.0, 0, rng) == 1.0 for _ in range(50))
