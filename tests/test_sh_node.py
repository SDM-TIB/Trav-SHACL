"""
Tests for parsing ``sh:node`` constraints ins Trav-SHACL.
"""

from glob import glob

from rdflib import Graph

SH_NODE_CASES = glob('./tests/cases/sh_node/**/definitions/*.json', recursive=True)


class TestNodeConstraintParsing:
    """Low-level checks that ShapeParser correctly builds constraint objects."""

    def _parse(self, ttl: str):
        from rdflib import Graph
        from TravSHACL.core.ShapeParser import ShapeParser
        g = Graph().parse(data=ttl, format='turtle')
        return ShapeParser().parse_ttl(
            shapes_graph=g,
            use_selective_queries=False,
            max_split_size=256,
            order_by_in_queries=False
        )

    def test_property_level_sh_node_creates_NodeConstraint(self):
        """A bare sh:node inside sh:property must produce a NodeConstraint."""
        from TravSHACL.constraints.NodeConstraint import NodeConstraint
        ttl = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :S a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:link ;
                sh:node :T
            ] .

        :T a sh:NodeShape ;
            sh:targetClass ex:Other .
        """
        shapes = self._parse(ttl)
        shape_s = next(s for s in shapes if 'S>' in s.get_id() or s.get_id().endswith(':S>') or ':S>' in s.get_id())
        node_cs = shape_s.get_node_constraints()
        assert len(node_cs) == 1, 'Expected exactly one NodeConstraint'
        assert isinstance(node_cs[0], NodeConstraint)
        assert node_cs[0].path is not None
        assert 'link' in node_cs[0].path

    def test_shape_level_sh_node_creates_DirectNodeConstraint(self):
        """A sh:node predicate directly on a node shape must produce a DirectNodeConstraint."""
        from TravSHACL.constraints.DirectNodeConstraint import DirectNodeConstraint
        ttl = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :Child a sh:NodeShape ;
            sh:targetClass ex:Child ;
            sh:node :Parent .

        :Parent a sh:NodeShape ;
            sh:targetClass ex:Parent .
        """
        shapes = self._parse(ttl)
        child = next(s for s in shapes if 'Child' in s.get_id())
        dncs = child.get_direct_node_constraints()
        assert len(dncs) == 1, 'Expected exactly one DirectNodeConstraint'
        assert isinstance(dncs[0], DirectNodeConstraint)
        assert dncs[0].path is None
        assert 'Parent' in dncs[0].shapeRef

    def test_sh_node_not_in_referencedShapes(self):
        """NodeConstraint references must NOT appear in Shape.referencedShapes (they
        bypass the selective-query filter mechanism)."""
        ttl = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :A a sh:NodeShape ;
            sh:targetClass ex:A ;
            sh:property [
                sh:path ex:rel ;
                sh:node :B
            ] .

        :B a sh:NodeShape ;
            sh:targetClass ex:B .
        """
        shapes = self._parse(ttl)
        shape_a = next(s for s in shapes if s.get_id().endswith('/A>'))
        # referencedShapes powers the queriesFilters / selective-query mechanism;
        # NodeConstraint refs must not appear there.
        assert shape_a.referencedShapes == {}, \
            'NodeConstraint reference must not pollute referencedShapes'

    def test_sh_node_in_dependency_graph(self):
        """NodeConstraint and DirectNodeConstraint references must appear in
        get_shape_refs() so the traversal-order planner can build the correct
        dependency edges."""
        from TravSHACL.core.ShapeSchema import ShapeSchema
        from TravSHACL.core.GraphTraversal import GraphTraversal
        from TravSHACL import parse_heuristics
        import tempfile
        import os
        ttl_a = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :A a sh:NodeShape ;
            sh:targetClass ex:A ;
            sh:property [ sh:path ex:rel ; sh:node :B ] .
        """
        ttl_b = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :B a sh:NodeShape ;
            sh:targetClass ex:B .
        """
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'A.ttl'), 'w') as f:
                f.write(ttl_a)
            with open(os.path.join(d, 'B.ttl'), 'w') as f:
                f.write(ttl_b)
            schema = ShapeSchema(
                schema_dir=d,
                schema_format='SHACL',
                endpoint=Graph(),          # empty graph – we just test the graph structure
                graph_traversal=GraphTraversal.DFS,
                heuristics=parse_heuristics('TARGET IN BIG'),
                use_selective_queries=False,
                max_split_size=256,
                output_dir=None,
                order_by_in_queries=False,
                save_outputs=False
            )
        shape_a = next(s for s in schema.shapes if s.get_id().endswith('/A>'))
        refs = shape_a.get_shape_refs()
        assert any('B' in r for r in refs), \
            'NodeConstraint reference to :B must appear in get_shape_refs()'

    def test_combined_sh_node_and_mincount_creates_both_constraints(self):
        """A property shape with both sh:node and sh:minCount must produce both a
        NodeConstraint *and* a MinOnlyConstraint (plain cardinality, no shapeRef)."""
        from TravSHACL.constraints.MinOnlyConstraint import MinOnlyConstraint
        ttl = """
        @prefix sh:   <http://www.w3.org/ns/shacl#> .
        @prefix ex:   <http://example.org/> .
        @prefix :     <http://example.org/shapes/> .

        :A a sh:NodeShape ;
            sh:targetClass ex:A ;
            sh:property [
                sh:path     ex:link ;
                sh:node     :B ;
                sh:minCount 1
            ] .

        :B a sh:NodeShape ;
            sh:targetClass ex:B .
        """
        shapes = self._parse(ttl)
        shape_a = next(s for s in shapes if s.get_id().endswith('/A>'))

        node_cs = shape_a.get_node_constraints()
        min_cs = [c for c in shape_a.get_constraints() if isinstance(c, MinOnlyConstraint)]

        assert len(node_cs) == 1, 'Expected one NodeConstraint'
        assert len(min_cs) == 1, 'Expected one MinOnlyConstraint'
        # The MinOnlyConstraint must carry NO shape reference (the cardinality
        # is a plain count, not a qualified-value-shape count).
        assert min_cs[0].shapeRef is None, \
            'MinOnlyConstraint from sh:node + sh:minCount must have shapeRef=None'
