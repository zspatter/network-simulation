"""
Drives one round of disease progression and wait-list mortality over a
WaitList. Kept separate from WaitList (which stays a pure collection) and from
the matchers (a death is a third outcome, orthogonal to matching), following
the project's "callers apply side effects explicitly" convention.

Intended to be called once per simulation round, after allocation: every
remaining patient's urgency advances and their acuity is recomputed, then each
faces a per-round death roll; patients who die are removed from the wait list
and returned so the caller can record them.
"""
from __future__ import annotations

import random
from typing import List, Optional

from organflow.clinical import mortality, urgency
from organflow.Patient import Patient
from organflow.WaitList import WaitList


def initialize_urgency(patient: Patient, rng: Optional[random.Random] = None) -> None:
    """
    Sets a newly generated patient's initial native urgency and acuity for
    their organ need. Called by the patient generator; separated here so the
    urgency model has a single entry point.

    :param Patient patient: the patient to initialize (mutated in place)
    :param random.Random rng: optional seeded source (defaults to the global module)
    """
    patient.raw_urgency = urgency.initial_raw_urgency(patient.organ_needed, rng)
    patient.acuity = urgency.to_acuity(patient.organ_needed, patient.raw_urgency)


def simulate_round_progression(wait_list: WaitList,
                               rng: Optional[random.Random] = None) -> List[Patient]:
    """
    Progresses every patient on the wait list by one round and rolls wait-list
    mortality. Each patient's urgency advances (urgency.progress), acuity is
    recomputed (urgency.to_acuity), and a death is drawn from that acuity
    (mortality.rolls_death). Patients who die are removed from the wait list.

    Deterministic under a seeded rng given the wait list's iteration order.

    :param WaitList wait_list: the wait list to progress (mutated in place)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: the patients who died this round (already removed from the list)
    """
    dead: List[Patient] = []
    # snapshot the list, since we remove dead patients as we go
    for patient in list(wait_list.wait_list):
        patient.raw_urgency = urgency.progress(
                patient.organ_needed, patient.raw_urgency, patient.rounds_waited, rng)
        patient.acuity = urgency.to_acuity(patient.organ_needed, patient.raw_urgency)
        if mortality.rolls_death(patient.acuity, rng):
            wait_list.remove_patient(patient)
            dead.append(patient)
    return dead
