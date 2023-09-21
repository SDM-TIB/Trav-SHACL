# Trav-SHACL Example

The example data was generated using the LUBM data generator to create data for one university.
In order to provide a good example, i.e., containing only a few entities, only a subset of the generated data is included.
The data can be found in the directory `data/raw`.
Additionally, we provide some example SHACL shapes for validating the data.
The shapes are located in the directory `shapes/LUBM`.

Start the SPARQL endpoint and Trav-SHACL Docker container with
```bash
docker-compose up -d --build
```

> [!NOTE]  
> The SPARQL endpoint needs some time to load the data.
> Usually, it should be fast.
> You can check if the data is loaded by trying to access `http://localhost:9090/sparql`.

## Trav-SHACL as a Library

If you want to use Trav-SHACL as a library, check out the description of how to run the example at https://sdm-tib.github.io/Trav-SHACL/library.html#example.

## Trav-SHACL as a Service

If you are interested in running Trav-SHACL as a service, check out the description of how to use it with this example at https://sdm-tib.github.io/Trav-SHACL/service.html#example.
