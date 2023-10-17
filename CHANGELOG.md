# v1.5.1 - 17 Oct 2023
- Fix necessity of adding a slash (/) at the end of the output path
- Update trace keeping
- Minor updates of documentation

# v1.5.0 - 21 Sep 2023
- Fix parameter `endpoint` for Flask app
- Reduce the number of entities in the example
- Update the Python version for the Docker image (3.9.13 to 3.11.5)
- Update the Virtuoso version in tests and example to 7.2.10
- Update GitHub Action for the test suite to run in parallel
- Update init method of `ShapeSchema`
  - All parameters are now keyword-only and typed
  - Only `shape_dir` and `endpoint` are required
  - Add default values for the remaining parameters
- Code clean up and structural improvements
- Add documentation to GitHub pages

# v1.4.2 - 19 Jul 2023
- The raw representation of OR constraints is no longer kept after parsing the constraint
- Fix issue with OR query when there are no constraints

# v1.4.1 - 18 Jul 2023
- Refactor parsing of OR constraints

# v1.4.0 - 13 Jul 2023
- Add capability of executing simple OR constraints, i.e., minimal or maximal occurrence of a predicate
- Add capability to handle inverse paths ``sh:path [ sh:inversePath ex:your_predicate ]``
- Add test cases for the above-mentioned features
- Update dependencies
- Drop Python 3.7 support
- Add Python 3.11 support

# v1.3.2 - 09 Jul 2023
- Add option for creating only one single connected component to ``TravSHACL.core.GraphTraversal.traverse_graph()``

# v1.3.1 - 27 Jun 2023
- Remove print of execution time

# v1.3.0 - 17 Feb 2023
- Add feature for basic SPARQL constraints
- Add feature to validate RDFLib graphs
- Improve finding of shape files
- Easier import of important parts of Trav-SHACL
- Add more test cases

# v1.2.0 - 01 Feb 2023
- Add feature of target query in RDF input

# v1.1.2 - 30 Jan 2023
- Fix referencing shapes when using TTL input
- Print report to console only if it is not stored in file

# v1.1.1 - 15 Dec 2022
- Fix not changing endpoint URL when using the interface

# v1.1.0 - 14 Dec 2022
- Temporary fix for `MinMaxConstraints`
- Add simple validation interface
- Add parsing of more than one shape per file (in Turtle format only)
- Fix issue with multiple connected components in the SHACL schema
- Fix for referencing shapes when using Turtle format

# v1.0.2 - 03 Aug 2022
- Fix inferred state of targets of shape without constraints
- Include the type statement for the referencing shape in max inter-shape constraint queries

# v1.0.1 - 02 Aug 2022
- Fix max constraint query for cases where the target query contains several triple patterns

# v1.0.0 - 13 Jul 2022
- First release of Trav-SHACL