# Data availability

This repository provides the principal processed data products, trained model artifacts, workflow materials, and analysis code required to inspect and reproduce the results reported in the associated manuscript.

## Included materials

The repository includes:

- the 6,344-event integrated manuscript catalog and its 15 archived model-combination partitions;
- the 632-event reference catalog used for comparison in the manuscript;
- selected model-specific REAL, VELEST, and hypoDD processing products;
- trained inference checkpoints used in the documented workflow;
- workflow configurations, scripts, tests, and catalog-verification utilities;
- figure inputs and figure-generation scripts for the principal manuscript analyses.

## Materials not distributed

The complete continuous-waveform archive is not included because its size is on the order of hundreds of gigabytes and is not suitable for distribution through GitHub.

External REAL, VELEST, ph2dt, and hypoDD executables are also not redistributed. Users should obtain these programs from their respective upstream sources.

## Reproducibility scope

The repository is intended to support:

- inspection of the manuscript data products;
- verification of the 6,344-event integrated manuscript catalog;
- examination of selected intermediate processing outputs;
- reproduction of the principal catalog analyses and manuscript figures.

Additional provenance and quality-control information is provided in `docs/PROVENANCE.md` and `docs/DATA_QUALITY.md`.
