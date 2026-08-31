# Three Gorges Reservoir microseismic catalog

Reproducibility package for **“Microseismic catalog construction in the Three Gorges Reservoir area using regionally adapted transfer learning and multi-model integration.”**

## Main scientific product

This repository follows the catalog actually used in the manuscript. The principal release product is the **6,344-event integrated manuscript catalog**:

- `data/final/final_catalog_6344.loc.txt` — 6,344-event integrated catalog used in the manuscript analyses and Figures 5–6;
- `data/final/categories/` — the 15 archived model-combination partitions whose chronological merge reproduces the 6,344-event catalog exactly;
- `data/reference/official_catalog_2018.txt` — 632-event official/reference catalog used for comparison.

The four model-specific processing streams include REAL, VELEST and hypoDD products. In the historical archive, the 6,344-event integrated manuscript catalog is assembled from the archived `hypoDD.loc` category products. Therefore this repository describes it as the **integrated manuscript catalog**, not as a combined `hypoDD.reloc` catalog. See `docs/PROVENANCE.md` and `docs/DATA_QUALITY.md`.

## Reproducibility scope

This repository supports:

- verification and deterministic reconstruction of the 6,344-event manuscript catalog from its 15 archived category partitions;
- audit of the four model-specific REAL, VELEST, `hypoDD.loc`, and `hypoDD.reloc` intermediate products;
- inference/reprocessing from user-supplied waveforms using the archived TorchScript checkpoints;
- portable wrappers for phase picking → REAL → VELEST → ph2dt/hypoDD;
- reproduction of manuscript Figures 2–8, with the 6,344-event manuscript catalog used for Figures 5–6.

Raw continuous waveform archives are intentionally excluded because of their size. REAL, VELEST, ph2dt, and hypoDD executables are external dependencies. The available materials do **not** support a strict training-from-scratch reproduction of the manuscript-specific fine-tuning stage; see `models/README.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[analysis,test,inference]"

python scripts/00_verify_models.py \
  --model-dir models/regional --prefix diting \
  --check-companion-pt --load

python scripts/08_catalog_quality.py \
  --repo-root . --output docs/catalog_quality_metrics.json \
  --fail-on-structural-error

python scripts/10_verify_manuscript_catalog.py \
  --repo-root . --output-dir build/manuscript-catalog \
  --report docs/manuscript_catalog_verification.json

python -m pytest
```

Rebuild the 6,344-event manuscript catalog from the archived 15 category partitions:

```bash
python scripts/10_verify_manuscript_catalog.py \
  --repo-root . \
  --output-dir build/manuscript-catalog \
  --report docs/manuscript_catalog_verification.json
```

Reproduce manuscript figures:

```bash
python scripts/reproduce_figures.py --repo-root . --catalog-mode manuscript
```

Graphviz is required for Figure 2 and GMT 6.5 for Figure 6.

## Catalog size comparison

The reference catalog distributed with this repository contains 632 events, whereas the integrated manuscript catalog contains 6,344 events. The latter therefore contains approximately 10 times as many events as the reference catalog (6,344 / 632 = 10.04).

The 6,344-event catalog is the catalog used for the manuscript-level temporal and spatial analyses presented in this repository. Additional information on catalog construction, verification, and quality control is provided in [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md).

## Data availability

This repository provides the principal data products and supporting materials required to inspect and reproduce the analyses reported in the manuscript, including:

- the 6,344-event integrated manuscript catalog;
- the 632-event reference catalog;
- selected intermediate products from REAL, VELEST, and hypoDD processing;
- scripts and configuration files used for catalog verification and figure reproduction;
- archived model checkpoints required for the documented inference workflow.

The complete continuous-waveform archive is not distributed through this repository because of its size and data-management constraints. Users wishing to reproduce the full workflow from continuous waveform data should obtain the corresponding waveform data separately.

Further details on the scope of the distributed data and external dependencies are provided in [`docs/DATA_AVAILABILITY.md`](docs/DATA_AVAILABILITY.md).

## License and citation

Repository-authored source code is released under the [`GPL-3.0-only`](LICENSE) license unless otherwise stated.

Data products, trained model files, third-party materials, and external software may be subject to separate licensing or redistribution conditions. Relevant information is provided in [`data/LICENSE.md`](data/LICENSE.md), [`models/LICENSE.md`](models/LICENSE.md), and the accompanying documentation. The bundled CSNBench snapshot retains its original upstream GPL-3.0 licensing terms, and external executables are not redistributed in this repository.

If you use this repository, its data products, or the associated workflow in academic work, please cite the accompanying manuscript and this repository. Citation metadata are provided in [`CITATION.cff`](CITATION.cff) and will be updated with the final article and repository DOI following publication and archival release.
