from network_simulator.CompatibilityMarkers import OrganType


class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """
    # heart, kidneys, liver, lungs, pancreas, intestine, and thymus.
    HEART, KIDNEY, LIVER, LUNG, PANCREAS, INTESTINE = 0, 1, 2, 3, 4, 5
    O_NEG, O_POS, A_NEG, A_POS, B_NEG, B_POS, AB_NEG, AB_POS = 0, 1, 2, 3, 4, 5, 6, 7
    patient_count = 0

    def __init__(self, patient_name, illness, organ_needed, blood_type, priority, location,
                 wait_list=None):
        Patient.patient_count = Patient.patient_count + 1
        self.patient_id = Patient.patient_count
        self.patient_name = patient_name
        self.illness = illness
        self.organ_needed = organ_needed
        self.blood_type = blood_type
        self.priority = priority
        self.location = location
        if wait_list:
            wait_list.add_patient(self)

    def __eq__(self, other):
        """
        Rich comparison returns true iff all attributes are equal

        :param Patient other: object to compare
        :return: boolean indicating equivalence
        """
        if self.patient_id is other.patient_id \
                and self.patient_name is other.patient_name \
                and self.illness is other.illness \
                and self.organ_needed is other.organ_needed \
                and self.blood_type is other.blood_type \
                and self.priority is other.priority \
                and self.location is other.location:
            return True
        return False

    def __ne__(self, other):
        """
        Rich comparison returns true if any attributes differ

        :param Patient other: object to compare
        :return: boolean indicating non-equivalence
        """
        if self.patient_id is other.patient_id \
                and self.patient_name is other.patient_name \
                and self.illness is other.illness \
                and self.organ_needed is other.organ_needed \
                and self.blood_type is other.blood_type \
                and self.priority is other.priority \
                and self.location is other.location:
            return False
        return True

    def __lt__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is less than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than other
        """
        return self.priority < other.priority

    def __le__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is less than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is less than or equal to other
        """
        return self.priority <= other.priority

    def __gt__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is greater than other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than other
        """
        return self.priority > other.priority

    def __ge__(self, other):
        """
        Rich comparison returns true if this object's priority attribute
        is greater than or equal to other's priority attribute

        :param Patient other: object to compare
        :return: boolean indicating if this object is greater than or equal to other
        """
        return self.priority >= other.priority

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
