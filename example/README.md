# Trav-SHACL Example

The example data was generated using the LUBM data generator to create data for one university.
In order to provide a good example, i.e., containing only a few entities, only a subset of the generated data is included.
Additionally, we provide some example SHACL shapes for validating the data.

Start the SPARQL endpoint and Trav-SHACL Docker container with
```bash
docker-compose up -d --build
```

> [!NOTE]  
> The SPARQL endpoint needs some time to load the data.
> Usually, it should be fast.
> You can check if the data is loaded by trying to access `http://localhost:9090/sparql`.

In order to validate the shape schema over the knowledge graph, run
```bash
./validate.sh
```

If you want to try different parameters, please check the README of the main directory of the repository for a detailed description of all possibilities.
