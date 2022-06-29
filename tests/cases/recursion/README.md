# Test Cases with Recursion

The test cases with recursion consider the classes `ClassA`, `ClassB`, and `ClassC`.

The following cases are tested:
1. Self-recursion over `ClassA`

   a) Inter-shape constraint with a minimal cardinality of `1`

   b) Inter-shape constraint with a maximal cardinality of `1`

   c) Inter-shape constraint with a maximal cardinality of `0` in combination with a constraint with a minimal cardinality of `1`

2. Recursion between two shapes: `ClassB` --> `ClassC` --> `ClassB`

   a) `ClassB` depends on `ClassC` with a minimal cardinality of `1` and `ClassC` depends on `ClassB` with a minimal cardinality of `1`

   b) `ClassB` depends on `ClassC` with a maximal cardinality of `2` and `ClassC` depends on `ClassB` with a minimal cardinality of `1`

   c) `ClassB` depends on `ClassC` with a maximal cardinality of `1` and `ClassC` depends on `ClassB` with a maximal cardinality of `2`

3. Recursion in a path: `ClassA` --> `ClassB` --> `ClassC` --> `ClassA`
4. Self-recursion in a path: `ClassC` --> (`ClassA` --> `ClassA`) --> `ClassB`
