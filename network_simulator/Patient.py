class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """
    # heart, kidneys, liver, lungs, pancreas, intestine, and thymus.
    HEART = 0
    KIDNEY = 1
    LIVER = 2
    LUNG = 3
    PANCREAS = 4
    INTESTINE = 5
    THYMUS = 6
    O_NEG = 0
    O_POS = 1
    A_NEG = 2
    A_POS = 3
    B_NEG = 4
    B_POS = 5
    AB_NEG = 6
    AB_POS = 7
    patient_count = 0

    def __init__(self, patient_name, illness, organ_needed, blood_type, priority, location):
        Patient.patient_count = Patient.patient_count + 1
        self.patient_id = Patient.patient_count
        self.patient_name = patient_name
        self.illness = illness
        self.organ_needed = organ_needed
        self.blood_type = blood_type
        self.priority = priority
        self.location = location

    def blood_type_compatibility(self, blood_type):
        if self.blood_type is blood_type:
            return True
        if self.blood_type % 2 is 1 and self.blood_type - blood_type is 1:
            return True
        if self.blood_type is Patient.AB_POS:
            return True
        if self.blood_type is Patient.AB_NEG and blood_type % 2 is 0:
            return True
        if blood_type is Patient.O_NEG:
            return True
        if blood_type is Patient.O_POS and self.blood_type % 2 is 1:
            return True
        return False


    @staticmethod
    def organ_category_name(n):
        """
        Returns the string associated with an organ category int
        This is designed to improve readability with console output

        :param int n: a number between 1-7 (inclusive) as defined with organ constants
        :return: string representing organ (or None if no match found)
        """
        if 0 < n < 8:
            organs = {Patient.HEART: 'Heart',
                      Patient.KIDNEY: 'Kidney',
                      Patient.LIVER: 'Liver',
                      Patient.LUNG: 'Lung',
                      Patient.PANCREAS: 'Pancreas',
                      Patient.INTESTINE: 'Intestines',
                      Patient.THYMUS: 'Thymus'}

            return organs[n]

        return None
