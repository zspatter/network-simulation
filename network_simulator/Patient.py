from __future__ import annotations

from typing import TYPE_CHECKING, FrozenSet, Optional

from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import OrganType

if TYPE_CHECKING:
    # deferred to avoid a circular import: WaitList imports Patient at module level
    from network_simulator.WaitList import WaitList


class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).

    Clinical fields (acuity, raw_urgency, body_size, unacceptable_antigens,
    cpra) model real allocation criteria and evolve over the simulation; they
    are populated by the generators and deliberately EXCLUDED from equality
    and hashing (see __eq__/__hash__) since they are mutable per-round state -
    two otherwise-identical patients at different points in their disease
    course are still the same patient.
    """
    patient_count = 0

    def __init__(self, patient_name: str, illness: str, organ_needed: OrganType,
                 blood_type: BloodType, priority: int, location: int,
                 wait_list: Optional[WaitList] = None,
                 acuity: float = 0.0, raw_urgency: float = 0.0,
                 body_size: Optional[float] = None,
                 unacceptable_antigens: FrozenSet[int] = frozenset(),
                 cpra: float = 0.0) -> None:

        Patient.patient_count = Patient.patient_count + 1

        self.patient_id: int = Patient.patient_count
        self.patient_name: str = patient_name
        self.illness: str = illness
        self.organ_needed: OrganType = organ_needed
        self.blood_type: BloodType = blood_type
        self.priority: int = priority
        self.location: int = location
        self.rounds_waited: int = 0

        # clinical state (see class docstring); excluded from equality/hashing
        self.acuity: float = acuity
        self.raw_urgency: float = raw_urgency
        self.body_size: Optional[float] = body_size
        self.unacceptable_antigens: FrozenSet[int] = unacceptable_antigens
        self.cpra: float = cpra

        if wait_list:
            wait_list.add_patient(self)

    def __str__(self) -> str:
        """
        Returns an easily readable string representing the patient

        :return: string representing the patient
        """
        return f'Patient:\n' \
            f'\tPatient ID: {"{:05d}".format(self.patient_id)}\n' \
            f'\tPatient name: {self.patient_name}\n' \
            f'\tIllness: {self.illness}\n' \
            f'\tOrgan needed: {OrganType(self.organ_needed).name}\n' \
            f'\tBlood type: {self.blood_type}\n' \
            f'\tPriority: {self.priority}\n' \
            f'\tRounds waited: {self.rounds_waited}\n' \
            f'\tNearest hospital: {self.location}\n'

    def __eq__(self, other) -> bool:
        """
        Two patients are equal iff they are the same patient (same patient_id).
        Identity semantics - not field-by-field - so equality is consistent with
        __hash__ and stays stable as a patient's mutable per-round state (wait
        time, acuity, urgency, sensitization, size) evolves; a patient who has
        deteriorated is still the same patient. This is what lets matchers track
        claimed patients in a set reliably across rounds.

        :param Patient other: object to compare
        :return: boolean indicating whether this is the same patient
        """
        if isinstance(other, Patient):
            return self.patient_id == other.patient_id
        return NotImplemented

    def __hash__(self) -> int:
        """
        Hashes by patient_id, the unique identifier, consistent with __eq__.
        Defining __eq__ without __hash__ makes instances unhashable by default,
        which would block using Patient in the sets/dicts allocation matchers use
        to track which patients have already been claimed within a batch.

        :return: hash of the patient's unique identifier
        """
        return hash(self.patient_id)
