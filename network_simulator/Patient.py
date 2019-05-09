from __future__ import annotations

from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import OrganType


class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """
    patient_count = 0

    def __init__(self, patient_name: str, illness: str, organ_needed: OrganType,
                 blood_type: BloodType, priority: int, location: int,
                 wait_list: 'WaitList' = None):
        Patient.patient_count = Patient.patient_count + 1

        self.patient_id: int = Patient.patient_count
        self.patient_name: str = patient_name
        self.illness: str = illness
        self.organ_needed: OrganType = organ_needed
        self.blood_type: BloodType = blood_type
        self.priority: int = priority
        self.location: int = location
        if wait_list:
            wait_list.add_patient(self)

    def __str__(self):
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
            f'\tNearest hospital: {self.location}\n'

    def __eq__(self, other):
        """
        Rich comparison returns true iff all attributes are equal

        :param Patient other: object to compare
        :return: boolean indicating equivalence
        """
        if isinstance(other, Patient):
            return self.patient_id is other.patient_id \
                   and self.patient_name is other.patient_name \
                   and self.illness is other.illness \
                   and self.organ_needed is other.organ_needed \
                   and self.blood_type == other.blood_type \
                   and self.priority is other.priority \
                   and self.location is other.location
        return NotImplemented

    def __ne__(self, other):
        """
        Rich comparison returns true if any attributes differ

        :param Patient other: object to compare
        :return: boolean indicating non-equivalence
        """
        if isinstance(other, Patient):
            return not (self.patient_id is other.patient_id
                        and self.patient_name is other.patient_name
                        and self.illness is other.illness
                        and self.organ_needed is other.organ_needed
                        and self.blood_type == other.blood_type
                        and self.priority is other.priority
                        and self.location is other.location)
        return NotImplemented

    def __lt__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is less than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than other
        """
        if isinstance(other, Patient):
            return self.priority < other.priority
        return NotImplemented

    def __le__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is less than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than or equal to other
        """
        if isinstance(other, Patient):
            return self.priority <= other.priority
        return NotImplemented

    def __gt__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is greater than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than other
        """
        if isinstance(other, Patient):
            return self.priority > other.priority
        return NotImplemented

    def __ge__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is greater than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than or equal to other
        """
        if isinstance(other, Patient):
            return self.priority >= other.priority
        return NotImplemented
