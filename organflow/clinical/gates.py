"""
Organ-specific feasibility gates, registered per organ type.

feasibility.py applies the universal gates (organ type, blood type, viability
vs. transit + operation time) and then, for each organ, every gate registered
here for that organ type. This keeps feasibility.py the single source of truth
while letting size (heart/lung) and HLA crossmatch (kidney) constraints live
with the clinical logic they belong to. Gates are pure, deterministic
functions of already-generated fields - all randomness happened at generation
time, so feasibility stays reproducible.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Tuple

from organflow.clinical.hla import crossmatch_positive
from organflow.clinical.size import size_compatible
from organflow.compatibility_markers import OrganType

if TYPE_CHECKING:
    from organflow.Organ import Organ
    from organflow.Patient import Patient

# A gate returns True if the (organ, patient) pair passes its constraint.
Gate = Callable[['Organ', 'Patient'], bool]


def size_gate(organ: 'Organ', patient: 'Patient') -> bool:
    """Passes iff donor and recipient body sizes are compatible for this organ."""
    return size_compatible(organ.donor_size, patient.body_size, organ.organ_type)


def crossmatch_gate(organ: 'Organ', patient: 'Patient') -> bool:
    """Passes iff the HLA crossmatch is negative (donor carries no unacceptable antigen)."""
    return not crossmatch_positive(organ.hla_antigens, patient.unacceptable_antigens)


# Which extra gates apply to which organ type. Organs absent from this map have
# only the universal feasibility checks in feasibility.py.
GATES_BY_ORGAN: Dict[OrganType, Tuple[Gate, ...]] = {
    OrganType.Heart: (size_gate,),
    OrganType.Lungs: (size_gate,),
    OrganType.Kidney: (crossmatch_gate,),
}
