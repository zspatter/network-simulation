from __future__ import annotations

from typing import TYPE_CHECKING, FrozenSet, List, Optional, Tuple

from organflow.BloodType import BloodType
from organflow.compatibility_markers import DonorType, OrganType

if TYPE_CHECKING:
    # deferred to avoid a circular import: OrganList imports Organ at module level
    from organflow.OrganList import OrganList

path_structure = Optional[List[Optional[int]]]
shortest_path_structure = Tuple[path_structure, float]

# Neutral donor-quality index for a hand-constructed organ (KDPI convention, 0 = ideal ..
# 100 = marginal): the population-mean index, which yields a neutral (1.0) discard multiplier and
# full graft survival (see organflow.clinical.acceptance). Kept as a local literal so the base
# Organ entity does not import the clinical stats package; a test pins it to
# frequencies.POPULATION_MEAN_QUALITY_INDEX so the two cannot drift.
NEUTRAL_QUALITY_INDEX = 48.6


class Organ:
    """
    A class representing a given organ which is available for transplant.

    Each organ has a name, a unique ID, lifetime (a maximum out of body duration),
    type matching, and a location.

    Clinical fields (hla_antigens, donor_size, donor_type, quality_index) describe
    the donor and gate feasibility / outcomes: HLA crossmatch (kidney), size matching
    (heart/lung), the DBD/DCD pathway, and a continuous donor-quality index (KDPI
    convention) that drives discard and graft survival. They are populated by the
    generator and default to empty/None/DBD/neutral so hand-constructed organs simply
    pass those gates and carry no quality penalty (see organflow.clinical).
    """

    organ_count = 0

    def __init__(self, organ_type: OrganType, blood_type: BloodType,
                 location: int, organ_list: Optional[OrganList] = None,
                 hla_antigens: FrozenSet[int] = frozenset(),
                 donor_size: Optional[float] = None,
                 donor_type: DonorType = DonorType.DBD,
                 quality_index: float = NEUTRAL_QUALITY_INDEX) -> None:
        Organ.organ_count = Organ.organ_count + 1

        self.organ_id: int = Organ.organ_count
        self.organ_type: OrganType = organ_type
        self.blood_type: BloodType = blood_type
        self.viability: float = Organ.get_viability(self.organ_type)
        self.origin_location: int = location
        self.current_location: int = location
        self.path: path_structure = [location]

        # donor clinical attributes (see class docstring)
        self.hla_antigens: FrozenSet[int] = hla_antigens
        self.donor_size: Optional[float] = donor_size
        self.donor_type: DonorType = donor_type
        self.quality_index: float = quality_index

        if organ_list:
            organ_list.add_organ(self)

    def move_organ(self, new_location: int, cost: float,
                   shortest_path: shortest_path_structure) -> None:
        """
        This function allows an organ's attributes to be altered to represent it's
        transportation across the network. This is intended to be used with
        Dijkstra.shortest_path (this will be the source of the cost parameter)

        :param int new_location: node id representing the destination location
        :param cost: weight/cost associated with then most efficient path
        :param list shortest_path: transit path taken when moving organ
        """
        if self.viability < cost:
            print('ERROR: organ no longer viable!')
            return
        path, weight = shortest_path
        self.path = path
        self.current_location = new_location
        self.viability -= cost

    @staticmethod
    def get_viability(organ_type: OrganType) -> float:
        """
        Gets viability rating for each organ individually, in hours - the
        same unit Network edge weights and get_operation_buffer() use (see
        Network's docstring), so viability and transit/operation time are
        directly comparable.

        These are maximum cold ischemia times (the transport budget only -
        see get_operation_buffer() for the additional time a match needs to
        reserve for the transplant procedure itself), sourced from published
        ranges: heart/lungs ~4-6h, liver ~8-12h, pancreas ~12-18h,
        kidney ~24-36h.

        :param int organ_type: constant corresponding to an organ type
        :return: hours the organ remains viable outside the body
        """
        viability = {
            OrganType.Heart.value:      6.0,
            OrganType.Kidney.value:     30.0,
            OrganType.Liver.value:      12.0,
            OrganType.Lungs.value:      6.0,
            OrganType.Pancreas.value:   12.0,
            OrganType.Intestines.value: 8.0}

        return viability[organ_type.value]

    @staticmethod
    def get_operation_buffer(organ_type: OrganType) -> float:
        """
        Gets the operation buffer for each organ: the hours of the recipient
        operation that are spent *within the cold-ischemia window*, i.e. from the
        organ's arrival until reperfusion restarts its blood supply. A feasible
        match requires organ.viability - transit_hours >= operation_buffer.

        This is the implant-to-reperfusion portion only, NOT total operating-room
        time. The whole transplant procedure runs several hours longer, but
        reperfusion happens partway through (once the vascular anastomoses are
        complete), and everything after reperfusion no longer draws down the cold-
        ischemia budget that viability (max cold ischemia time) represents. Sizing
        this as the full OR duration would double-count and, against a realistic
        transit model, make short-window thoracic organs (heart/lung) essentially
        untransplantable. Approximate anastomosis-to-reperfusion times: kidney ~1h,
        heart/lung/pancreas ~1.5h, liver/intestine ~2h.

        :param OrganType organ_type: constant corresponding to an organ type
        :return: hours of the recipient operation that consume the cold-ischemia budget
        """
        operation_buffer = {
            OrganType.Heart.value:      1.5,
            OrganType.Kidney.value:     1.0,
            OrganType.Liver.value:      2.0,
            OrganType.Lungs.value:      1.5,
            OrganType.Pancreas.value:   1.5,
            OrganType.Intestines.value: 2.0}

        return operation_buffer[organ_type.value]

    def __str__(self) -> str:
        """
        Builds an easily readable string representing an organ

        :return: str
        """
        return f'Organ:\n' \
            f'\tOrgan ID: {"{:05d}".format(self.organ_id)}\n' \
            f'\tOrgan type: {OrganType(self.organ_type).name}\n' \
            f'\tBlood type: {self.blood_type}\n' \
            f'\tViability: {self.viability}\n' \
            f'\tOrigin location: {self.origin_location}\n' \
            f'\tCurrent location: {self.current_location}\n' \
            f'\tTransit path: {self.path}\n'
