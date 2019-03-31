class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """

    patient_count = 0

    def __init__(self, patient_name, illness, organ_needed, wait_time, location):
        Patient.patient_count = Patient.patient_count + 1
        self.patient_id = Patient.patient_count
        self.patient_name = patient_name
        self.illness = illness
        self.organ_needed = organ_needed
        self.wait_time = wait_time
        self.location = location
