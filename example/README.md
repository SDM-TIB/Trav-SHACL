# Trav-SHACL Example

The example data was generated using the LUBM data generator to create data for one university.
Additionally, we provide some SHACL shapes (in JSON format) for validating the data.

Extract the pre-loaded data
```bash
tar -zxf data/pre-loaded.tar.gz -C data/
```

Start the SPARQL endpoint and Trav-SHACL docker container with
```bash
docker-compose up -d --build
```

In order to validate the shape schema over the knowledge graph, run
```bash
./validate.sh
```

If you want to try different parameters, please check the README of the main directory of the repository for a detailed description of all possibilities.