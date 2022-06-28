# Test Cases with Two Shapes

The test cases with two shapes consider the instances of the classes `ClassB` and `ClassC`.

The following cases are tested:
1. `ClassB` depends on `ClassC` with a minimal cardinality of `1`
2. `ClassB` depends on `ClassC` with a minimal cardinality of `3`
3. `ClassB` depends on `ClassC` with a maximal cardinality of `0`
4. `ClassB` depends on `ClassC` with a maximal cardinality of `2`
5. `ClassB` depends on `ClassC` with a minimal cardinality of `1` plus an additional min constraint
6. `ClassB` depends on `ClassC` with a minimal cardinality of `1` plus an additional max constraint
7. `ClassB` depends on `ClassC` with a maximal cardinality of `1` plus an additional min constraint
8. `ClassB` depends on `ClassC` with a maximal cardinality of `1` plus an additional max constraint

`ClassC` has a simple min constraint. Three out of four instances of class `ClassC` are valid w.r.t. the aforementioned constraint.

Additionally, `case9` checks whether the selective option also works when the list of valid neighbors is used for filtering.
This is done by changing the min constraint in `ClassC` to a max constraint with cardinality `0`.
Therefore, only one of the four instances is valid.
Trav-SHACL uses the shorter list for filtering in the target query based on an already evaluated neighbor.
In the main test cases, the list of invalid entities is used.