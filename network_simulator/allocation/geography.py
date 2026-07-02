"""
Geographic tier classifiers used by allocation.matchers.tiered.TieredMatcher to model
hard geographic allocation constraints - and the option to remove them.

Real OPTN policy historically allocated within fixed, arbitrary boundaries: 11 "Regions"
and 58 Donation Service Areas (DSAs), eliminated from kidney/pancreas policy in 2021 and
from liver/lung/heart policy in 2018-2020 after HRSA found they "have not and cannot be
justified." They were replaced by concentric distance *circles* (150/250/500 nautical
miles from the donor hospital) - still current for kidney, pancreas, and heart - while
lung moved further, in March 2023, to "continuous distribution," where distance is one
continuously-weighted point factor with no hard boundary at all (liver/heart continuous
distribution is in progress). See:
  - https://www.hrsa.gov/optn/professionals/resources/kidney-pancreas/kidney-allocation-system/removal-dsa-region-kidney-allocation-policy
  - https://optn.transplant.hrsa.gov/policies-bylaws/a-closer-look/continuous-distribution/continuous-distribution-heart/

This module gives the benchmark three points on that spectrum to compare: the legacy
arbitrary-region model, the current distance-circle model, and no hard constraint at all
(geography left to the scorer, if it weighs it - see allocation.scoring.RealWorldScore).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.Patient import Patient

TierFn = Callable[[Organ, Patient, float, 'Network'], int]

# Approximate transit-hour thresholds standing in for the real 150/250/500 NM circles.
# Not derived by inverting distance.py's two-speed (ground/air) model: that model's
# ground->air switch at 400km makes km->hours non-monotonic (a farther-but-air-eligible
# point can be *faster* than a nearer ground-only one), so a literal NM->hours conversion
# would produce non-monotonic tier boundaries. These are round, documented approximations
# instead - the same style of simplifying assumption distance.py itself uses - chosen so
# tier 0/1/2 increase in the same order of magnitude as the real 150/250/500 NM circles.
LOCAL_THRESHOLD_HOURS = 2.0
REGIONAL_THRESHOLD_HOURS = 5.0


@dataclass(frozen=True)
class TierClassifier:
    """Pairs a tier function with how many tiers (0..max_tier) it can produce."""
    name: str
    max_tier: int
    classify: TierFn


def _region_tier(organ: Organ, patient: Patient, transit_hours: float,
                 network: Network) -> int:
    """
    0 (local) if the organ and patient share a Node.region, else 1 (national). A two-tier
    simplification of the real historical DSA -> Region -> National cascade: this project
    tracks Node.region but not DSA, so DSA and Region collapse into one "local" tier.
    """
    donor_region = network.network_dict[organ.origin_location].region
    patient_region = network.network_dict[patient.location].region
    return 0 if donor_region is not None and donor_region == patient_region else 1


def _circle_tier(organ: Organ, patient: Patient, transit_hours: float,
                 network: Network) -> int:
    """
    0 (local) / 1 (regional) / 2 (national) by transit_hours against
    LOCAL_THRESHOLD_HOURS / REGIONAL_THRESHOLD_HOURS - approximates the real
    150/250/500 NM acuity-circle waterfall used for kidney, pancreas, and heart today.
    """
    if transit_hours <= LOCAL_THRESHOLD_HOURS:
        return 0
    if transit_hours <= REGIONAL_THRESHOLD_HOURS:
        return 1
    return 2


def _national_tier(organ: Organ, patient: Patient, transit_hours: float,
                   network: Network) -> int:
    """Always 0: every feasible candidate is eligible immediately - no hard constraint."""
    return 0


region_tier = TierClassifier('region', max_tier=1, classify=_region_tier)
circle_tier = TierClassifier('circle', max_tier=2, classify=_circle_tier)
national_tier = TierClassifier('national', max_tier=0, classify=_national_tier)
