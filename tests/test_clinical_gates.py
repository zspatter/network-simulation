from organflow.BloodType import BloodType
from organflow.clinical.gates import GATES_BY_ORGAN, crossmatch_gate, size_gate
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Organ import Organ
from organflow.Patient import Patient

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _patient(organ_type, **kwargs):
    return Patient('p', 'n/a', organ_type, o_neg, 100, 1, **kwargs)


def _organ(organ_type, **kwargs):
    return Organ(organ_type, o_neg, location=1, **kwargs)


def test_gates_registered_for_the_right_organs():
    assert size_gate in GATES_BY_ORGAN[OrganType.Heart]
    assert size_gate in GATES_BY_ORGAN[OrganType.Lungs]
    assert crossmatch_gate in GATES_BY_ORGAN[OrganType.Kidney]
    # kidney has no size gate; heart/lung have no crossmatch gate
    assert size_gate not in GATES_BY_ORGAN.get(OrganType.Kidney, ())
    assert crossmatch_gate not in GATES_BY_ORGAN.get(OrganType.Heart, ())
    # organs with no extra gates aren't in the map
    assert OrganType.Liver not in GATES_BY_ORGAN


def test_crossmatch_gate_blocks_sensitized_pair():
    organ = _organ(OrganType.Kidney, hla_antigens=frozenset({7, 8}))
    incompatible = _patient(OrganType.Kidney, unacceptable_antigens=frozenset({8, 9}))
    compatible = _patient(OrganType.Kidney, unacceptable_antigens=frozenset({1, 2}))

    assert crossmatch_gate(organ, incompatible) is False
    assert crossmatch_gate(organ, compatible) is True


def test_size_gate_blocks_mismatched_pair():
    small_organ = _organ(OrganType.Heart, donor_size=55.0)
    matched = _patient(OrganType.Heart, body_size=60.0)
    too_large = _patient(OrganType.Heart, body_size=110.0)

    assert size_gate(small_organ, matched) is True
    assert size_gate(small_organ, too_large) is False
