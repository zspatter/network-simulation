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
        Rich comparison returns true iff all attributes are equal

        :param Patient other: object to compare
        :return: boolean indicating equivalence
        """
        if isinstance(other, Patient):
            return self.patient_id == other.patient_id \
                   and self.patient_name == other.patient_name \
                   and self.illness == other.illness \
                   and self.organ_needed == other.organ_needed \
                   and self.blood_type == other.blood_type \
                   and self.priority == other.priority \
                   and self.location == other.location \
                   and self.rounds_waited == other.rounds_waited
        return NotImplemented

    def __hash__(self) -> int:
        """
        Hashes by patient_id (the class's unique identifier). Defining
        __eq__ without __hash__ makes instances unhashable by default, which
        would block using Patient in sets/dicts - e.g. allocation matchers
        that need to track which patients have already been claimed within
        a batch.

        :return: hash of the patient's unique identifier
        """
        return hash(self.patient_id)

    def __ne__(self, other) -> bool:
        """
        Rich comparison returns true if any attributes differ

        :param Patient other: object to compare
        :return: boolean indicating non-equivalence
        """
        if isinstance(other, Patient):
            return not (self.patient_id == other.patient_id
                        and self.patient_name == other.patient_name
                        and self.illness == other.illness
                        and self.organ_needed == other.organ_needed
                        and self.blood_type == other.blood_type
                        and self.priority == other.priority
                        and self.location == other.location
                        and self.rounds_waited == other.rounds_waited)
        return NotImplemented

    def __lt__(self, other) -> bool:
        """
        Rich comparison returns true if this object's priority attribute
        is less than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than other
        """
        if isinstance(other, Patient):
            return self.priority < other.priority
        return NotImplemented

    def __le__(self, other) -> bool:
        """
        Rich comparison returns true if this object's priority attribute
        is less than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than or equal to other
        """
        if isinstance(other, Patient):
            return self.priority <= other.priority
        return NotImplemented

    def __gt__(self, other) -> bool:
        """
        Rich comparison returns true if this object's priority attribute
        is greater than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than other
        """
        if isinstance(other, Patient):
            return self.priority > other.priority
        return NotImplemented

    def __ge__(self, other) -> bool:
        """
        Rich comparison returns true if this object's priority attribute
        is greater than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than or equal to other
        """
        if isinstance(other, Patient):
            return self.priority >= other.priority
        return NotImplemented
