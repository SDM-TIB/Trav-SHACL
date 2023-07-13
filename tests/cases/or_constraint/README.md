# Test Cases with OR Constraints

The test cases with OR constraints consider the instances of class `ClassA`.

The following cases are tested:
1. One OR constraint including two constraints

   a) two minimal cardinality constraints

   b) two maximal cardinality constraints

   c) one minimal cardinality and one maximal cardinality constraint

2. One OR constraint including three constraints

3. One OR constraint AND another constraint

   a) two minimal cardinality constraints in OR and a maximal cardinality constraint

   b) one minimal cardinality and one maximal cardinality in OR and a minimal cardinality constraint; empty intersection

4. One OR constraint AND two additional constraints

5. Two OR constraints, i.e., OR1 and OR2

6. Two OR constraints AND another constraint

The additional test case 7 uses the classes `ClassB` and `ClassC` to check whether OR constraints are also working when the shape involving the OR constraint also has a dependency on another shape (not inside the OR though).
This test case is necessary since Trav-SHACL is able to limit the target entities checked based on the result of the previously evaluated shapes.