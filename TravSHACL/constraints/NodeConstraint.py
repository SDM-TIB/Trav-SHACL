# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from TravSHACL.constraints.Constraint import Constraint


class NodeConstraint(Constraint):
    """Represents a ``sh:node`` constraint inside a ``sh:property`` block.

    Semantics: *all* value nodes reached via ``path`` must conform to the
    shape named by ``shape_ref``.  Unlike ``sh:qualifiedValueShape`` there
    is no cardinality attached – the constraint is violated as soon as
    **any** value node is invalid in the referenced shape.

    The constraint is validated after the referenced shape has been fully
    evaluated, by querying the endpoint for focus nodes whose ``path``
    values intersect the referenced shape's invalid set.

    Parameters
    ----------
    id_ :
        Internal constraint identifier.
    path :
        The property path (predicate) from the enclosing ``sh:property``
        block, in the same format used by other constraints (either a
        full IRI wrapped in ``<>`` or an abbreviated form).
    shape_ref :
        IRI of the referenced SHACL node shape (with ``<>`` when a full
        IRI is used).
    is_pos :
        ``True`` for a positive constraint (default).
    """

    def __init__(self, id_: str, path: str, shape_ref: str, is_pos: bool = True):
        super().__init__(id_=id_, is_pos=is_pos, shape_ref=shape_ref, path=path)
        # Sentinel values so the existing min/max query-generation code
        # never picks this constraint up by accident.
        self.min = -1
        self.max = -1
        self.variables = []
