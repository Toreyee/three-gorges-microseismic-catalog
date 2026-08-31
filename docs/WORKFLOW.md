# Reproducible workflow

## Environment

Use Python 3.10+ (recommended 3.11). Graphviz is required for Figure 2; GMT 6.5 for Figure 6. REAL, VELEST, ph2dt, and hypoDD are external executables.

```bash
python -m pip install -e ".[analysis,test,inference]"
```

## Waveforms and phase picking

Raw continuous waveforms are not included because of their size. Supply explicit input paths to the waveform-preparation and phase-picking scripts.

Included inference checkpoints:

```text
models/regional/diting.eqt.jit
models/regional/diting.rnn.jit
models/regional/diting.unet.jit
models/regional/diting.lppnl.jit
```

Verify them before inference:

```bash
python scripts/00_verify_models.py --model-dir models/regional --prefix diting --check-companion-pt --load
```

## Model-specific processing stages

The historical `cats.zip` archive contains the following event counts:

| Model | REAL | VELEST | hypoDD.loc | hypoDD.reloc |
|---|---:|---:|---:|---:|
| EQTransformer | 8,392 | 7,913 | 5,620 | 4,517 |
| RNN | 7,863 | 7,538 | 5,232 | 4,298 |
| U-Net | 7,078 | 6,748 | 4,908 | 3,907 |
| LPPNL | 6,733 | 6,460 | 4,777 | 3,912 |

The repository retains compact copies of these products under `data/intermediate/`.

## Manuscript integration

The manuscript release product is the archived 6,344-event `hypoDD.loc`-format integration. Its 15 category partitions are stored in `data/final/categories/`.

Rebuild and verify the manuscript catalog:

```bash
python scripts/10_verify_manuscript_catalog.py \
  --repo-root . \
  --output-dir build/manuscript-catalog \
  --report docs/manuscript_catalog_verification.json
```

This operation reproduces `data/final/final_catalog_6344.loc.txt` exactly by chronologically merging the 15 archived category files. It does not claim to recreate the missing historical category-generation step from the four per-model `.loc` files.

## Figures

```bash
python scripts/reproduce_figures.py --repo-root . --catalog-mode manuscript
```

Figures 5–6 use `data/final/final_catalog_6344.loc.txt`.
