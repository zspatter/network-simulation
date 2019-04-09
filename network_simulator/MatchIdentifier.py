import network_simulator.Patient as P
import network_simulator.Organ as O


class MatchIdentifier:

    @classmethod
    def is_match(cls, patient, organ):
        """
        Determines if the organ and patient are a compatible match

        :param Patient patient: patient in need of organ
        :param Organ organ: donated organ
        :return:
        """

        if patient.blood_type is organ.blood_type:
            return True
        if patient.blood_type % 2 is 1 and patient.blood_type - organ.blood_type is 1:
            return True
        if patient.blood_type is P.Patient.AB_POS:
            return True
        if patient.blood_type is P.Patient.A_NEG and organ.blood_type % 2 is 0:
            return True
        if organ.blood_type is O.Organ.O_NEG:
            return True
        if organ.blood_type is O.Organ.O_POS and patient.blood_type % 2 is 1:
            return True
        return False
