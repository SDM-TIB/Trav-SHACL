# Trav-SHACL Documentation

The documentation is built using [Sphinx](https://www.sphinx-doc.org/en/master/).

## Prerequisites
* make
* Python packages listed in [../requirements-doc.txt](https://raw.githubusercontent.com/SDM-TIB/diefpy/master/requirements-doc.txt).

## Generating the Documentation
You can create a new version of the documentation by running:
```bash
make docs
```

This will generate the docs without any cached files. The new documentation will be available in `_build/html`.

## Publishing the Documentation
In order to publish a new version (and building one before), run the following command:
```bash
make docs deploy
```

This will generate the docs and create a new commit on the `gh-pages` branch. GitHub will then deploy the new version automatically.