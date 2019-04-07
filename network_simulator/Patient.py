class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """
    # heart, kidneys, liver, lungs, pancreas, intestine, and thymus.
    HEART = 1
    KIDNEY = 2
    LIVER = 3
    LUNG = 4
    PANCREAS = 5
    INTESTINE = 6
    THYMUS = 7
    patient_count = 0

    def __init__(self, patient_name, illness, organ_needed, priority, location):
        Patient.patient_count = Patient.patient_count + 1
        self.patient_id = Patient.patient_count
        self.patient_name = patient_name
        self.illness = illness
        self.organ_needed = organ_needed
        self.priority = priority
        self.location = location

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
