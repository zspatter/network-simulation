import random

from organflow.BloodType import BloodType
from organflow.clinical import retransplant
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Patient import Patient

_O_POS = BloodType(BloodTypeLetter.O, BloodTypePolarity.POS)


def _recipient(organ: OrganType, pid_suffix: int) -> Patient:
    return Patient(patient_name=f'r{pid_suffix}', illness='n/a', organ_needed=organ,
                   blood_type=_O_POS, priority=50, location=1)


def _registry(organ: OrganType, n: int) -> list:
    return [_recipient(organ, i) for i in range(n)]


def test_per_round_graft_failure_prob_is_a_small_positive_probability():
    p = retransplant.per_round_graft_failure_prob(retransplant.GRAFT_FAILURE_ANNUAL_RATE)
    # one week of a ~5.5%/yr hazard is a small per-round probability
    assert 0.0 < p < 0.01


def test_patient_defaults_to_not_a_retransplant():
    assert _recipient(OrganType.Kidney, 0).is_retransplant is False


def test_prepare_relist_marks_resets_and_sensitizes():
    patient = _recipient(OrganType.Kidney, 0)
    patient.rounds_waited = 40
    assert patient.cpra == 0.0

    retransplant.prepare_relist(patient, random.Random(0))

    assert patient.is_retransplant is True
    assert patient.rounds_waited == 0
    assert patient.organ_needed is OrganType.Kidney  # still needs the same organ
    # a prior graft raises sensitization, so cPRA can only go up (harder to match)
    assert patient.cpra > 0.0
    assert len(patient.unacceptable_antigens) >= retransplant.RELIST_SENSITIZATION_MIN


def test_simulate_graft_failures_partitions_the_registry():
    grafts = _registry(OrganType.Kidney, 5000)
    relisted, deaths, survivors = retransplant.simulate_graft_failures(grafts, random.Random(1))

    # every graft ends the round as exactly one of: relisted, post-transplant death, recipient
    # exit (dropped), or survivor - so the accounted-for count never exceeds the registry
    assert len(relisted) + deaths + len(survivors) <= len(grafts)
    # most grafts survive a single week; a minority fail
    assert len(survivors) > len(relisted) + deaths
    assert relisted  # some failures relist
    assert all(p.is_retransplant for p in relisted)


def test_kidney_failures_relist_far_more_than_heart():
    # a failed kidney bridges on dialysis (nearly all relist); a failed heart is usually fatal
    assert (retransplant.GRAFT_FAILURE_RELIST_FRACTION[OrganType.Kidney]
            > retransplant.GRAFT_FAILURE_RELIST_FRACTION[OrganType.Heart])

    kidney_relisted, _, _ = retransplant.simulate_graft_failures(
            _registry(OrganType.Kidney, 8000), random.Random(2))
    heart_relisted, _, _ = retransplant.simulate_graft_failures(
            _registry(OrganType.Heart, 8000), random.Random(2))
    assert len(kidney_relisted) > len(heart_relisted)


def test_recipient_exit_competes_so_not_every_graft_relists():
    # run the same registry many rounds; recipients keep exiting with functioning grafts, so the
    # cumulative relisted stays a bounded minority rather than eventually reaching everyone
    grafts = _registry(OrganType.Kidney, 6000)
    rng = random.Random(3)
    total_relisted = 0
    for _ in range(52 * 5):  # five years of weekly rounds
        relisted, _deaths, grafts = retransplant.simulate_graft_failures(grafts, rng)
        total_relisted += len(relisted)
    # if graft failure were the only exit, ~90% of these kidneys would eventually relist; the
    # competing recipient-exit hazard bounds it well below the whole registry
    assert total_relisted < 0.6 * 6000


def test_simulate_graft_failures_is_deterministic_under_seed():
    a = retransplant.simulate_graft_failures(_registry(OrganType.Liver, 2000), random.Random(7))
    b = retransplant.simulate_graft_failures(_registry(OrganType.Liver, 2000), random.Random(7))
    assert (len(a[0]), a[1], len(a[2])) == (len(b[0]), b[1], len(b[2]))
