from network_simulator.allocation.geography import (
    LOCAL_THRESHOLD_HOURS,
    REGIONAL_THRESHOLD_HOURS,
    circle_tier,
    national_tier,
    region_tier,
)
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.Patient import Patient

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _network_with_regions(region1, region2):
    return Network({1: Node(1, region=region1), 2: Node(2, region=region2)})


def _organ_and_patient():
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 0, 2)
    return organ, patient


def test_region_tier_is_local_when_donor_and_patient_share_a_region():
    network = _network_with_regions(3, 3)
    organ, patient = _organ_and_patient()

    assert region_tier.classify(organ, patient, transit_hours=5.0, network=network) == 0


def test_region_tier_is_national_across_different_regions():
    network = _network_with_regions(3, 4)
    organ, patient = _organ_and_patient()

    assert region_tier.classify(organ, patient, transit_hours=5.0, network=network) == 1


def test_region_tier_max_tier_is_one():
    assert region_tier.max_tier == 1


def test_circle_tier_boundaries():
    network = _network_with_regions(1, 1)
    organ, patient = _organ_and_patient()

    assert circle_tier.classify(organ, patient, LOCAL_THRESHOLD_HOURS, network) == 0
    assert circle_tier.classify(organ, patient, LOCAL_THRESHOLD_HOURS + 0.01, network) == 1
    assert circle_tier.classify(organ, patient, REGIONAL_THRESHOLD_HOURS, network) == 1
    assert circle_tier.classify(organ, patient, REGIONAL_THRESHOLD_HOURS + 0.01, network) == 2


def test_circle_tier_max_tier_is_two():
    assert circle_tier.max_tier == 2


def test_national_tier_is_always_local_regardless_of_distance_or_region():
    network = _network_with_regions(1, 9)
    organ, patient = _organ_and_patient()

    assert national_tier.classify(organ, patient, transit_hours=999.0, network=network) == 0
    assert national_tier.max_tier == 0
