# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from TravSHACL.constraints.Constraint import Constraint


class DirectNodeConstraint(Constraint):
    """Represents a ``sh:node`` constraint placed **directly** on a node shape
    (i.e. *not* inside a ``sh:property`` block).

    Semantics: every focus node of the owning shape must also conform to
    ``shape_ref``.  This is equivalent to shape inheritance – if a focus
    node is invalid in ``shape_ref`` it is automatically invalid in the
    owning shape too.

    The check is O(1) per target: after ``shape_ref`` has been evaluated
    we simply intersect its invalid set with the pending targets of the
    owning shape.

    Parameters
    ----------
    id_ :
        Internal constraint identifier.
    shape_ref :
        IRI of the referenced SHACL node shape (with ``<>`` when a full
        IRI is used).
    is_pos :
        ``True`` for a positive constraint (default).
    """

    def __init__(self, id_: str, shape_ref: str, is_pos: bool = True):
        super().__init__(id_=id_, is_pos=is_pos, shape_ref=shape_ref, path=None)
        # Sentinel values so the existing min/max query-generation code
        # never picks this constraint up.
        self.min = -1
        self.max = -1
        self.variables = []
