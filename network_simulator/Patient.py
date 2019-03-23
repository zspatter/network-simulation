class Patient:
    """
    A class representing a patient in need of an organ transplant.

    Each patient is defined with a name, a unique ID, illness, organ needed,
    waiting time (priority?), and location ('home' hospital).
    """

    def __init__(self, patient_name, id, illness, organ_needed, wait_time, location):
        self.patient_name = patient_name
        self.id = id
        self.illness = illness
        self.organ_needed = organ_needed
        self.wait_time = wait_time
        self.location = location
