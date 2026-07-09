import random
from typing import List, Optional

from organflow.clinical.frequencies import (
    DONOR_RECOVERY_PROBABILITIES,
    KIDNEYS_PER_DONOR,
    random_donor_type,
    random_quality_index,
    random_us_blood_type,
)
from organflow.clinical.hla import donor_antigens
from organflow.clinical.size import body_size
from organflow.compatibility_markers import OrganType
from organflow.Network import Network
from organflow.Organ import Organ
from organflow.OrganList import OrganList


class OrganGenerator:
    """
    Generates organs harvested from a variable number of deceased donors.

    Each organ type is recovered from a given donor with an organ-specific
    probability (see organflow.clinical.frequencies), reflecting that
    kidneys are recovered from nearly every donor (and there are two) while
    heart/lung face stricter suitability criteria. All organs from one donor
    share that donor's location and blood type.
    """

    @staticmethod
    def generate_organs(graph: Network, n: int, rng: Optional[random.Random] = None,
                        eligible_nodes: Optional[List[int]] = None) -> List[Organ]:
        """
        Harvests organs from n deceased donors. Each organ type is recovered
        with its own probability (DONOR_RECOVERY_PROBABILITIES), so not every
        organ is recovered from every donor - representing organs unsuitable
        for donation. Kidneys yield KIDNEYS_PER_DONOR organs when recovered.

        :param Network graph: network where organs can be generated
        :param int n: number of donors to harvest organs from
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :param eligible_nodes: optional subset of node ids a donor may be located at (defaults
            to every node in `graph`); e.g. on a real hospital network, donors may originate at
            a transplant hospital or an Organ Procurement Organization, but not e.g. a lab
            (see execute.import_hospitals)
        """

        # list of currently active nodes
        nodes = eligible_nodes if eligible_nodes is not None else graph.nodes()
        organs: List[Organ] = list()
        source = rng or random

        # number of donors to harvest from
        for _ in range(n):
            location_id = source.choice(nodes)
            blood_type = random_us_blood_type(rng)
            # donor-level attributes shared across every organ from this donor. quality_index is
            # a donor property (marginality from age/comorbidities/warm ischemia), so both kidneys
            # and every other organ from one donor carry the same index, drawn from the pathway.
            antigens = donor_antigens(rng)
            donor_body_size = body_size(rng)
            donor_type = random_donor_type(rng)
            quality_index = random_quality_index(donor_type, rng)

            for organ_type in OrganType:
                # determines if this organ is suitable for recovery from this donor
                if source.random() < DONOR_RECOVERY_PROBABILITIES[organ_type]:
                    count = KIDNEYS_PER_DONOR if organ_type is OrganType.Kidney else 1
                    for _ in range(count):
                        organs.append(Organ(organ_type=organ_type,
                                            blood_type=blood_type,
                                            location=location_id,
                                            hla_antigens=antigens,
                                            donor_size=donor_body_size,
                                            donor_type=donor_type,
                                            quality_index=quality_index))
        return organs

    @staticmethod
    def generate_organs_to_list(graph: Network, n: int, organ_list: OrganList,
                                rng: Optional[random.Random] = None,
                                eligible_nodes: Optional[List[int]] = None) -> None:
        """
        Generates N organs and adds all generated organs to an OrganList

        :param Network graph: network where organs can be generated
        :param int n: number of bodies to harvest organs from
        :param OrganList organ_list: list of organs to add harvested organs to
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :param eligible_nodes: optional subset of node ids a donor may be located at - see
            generate_organs()
        """
        organ_list.add_organs(OrganGenerator.generate_organs(graph, n, rng, eligible_nodes))
