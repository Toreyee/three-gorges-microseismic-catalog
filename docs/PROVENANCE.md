# Provenance map

This release was reconciled against the supplied historical processing archive `cats.zip`.

| Repository product | Historical source / lineage | Verification |
|---|---|---|
| `data/final/final_catalog_6344.loc.txt` | `cats/hypoDD_loc/ALL/ALL.txt` | byte-identical; 6,344 rows |
| `data/final/categories/*.txt` | `cats/hypoDD_loc/ALL/{EE,...,ERUL}.txt` | all 15 files byte-identical; row sum = 6,344 |
| `data/intermediate/hypodd/<model>/hypoDD.loc` | `cats/hypoDD/<model>/hypoDD.loc` | byte-identical |
| `data/intermediate/hypodd/<model>/hypoDD.reloc` | `cats/hypoDD/<model>/hypoDD.reloc` | byte-identical |
| `data/intermediate/velest/<model>/new.cat` | `cats/VELEST/<model>/new.cat` | archived per-model VELEST result |
| `data/intermediate/real/<model>/...` | `cats/REAL/<model>/...` | archived per-model REAL result |
| `models/regional/diting.*.jit/.pt` | archived AIpick/DiTing checkpoint workspace | checksum-verified; four `.jit` files load with TorchScript |
| `third_party/csnbench/` | pinned upstream CSNBench snapshot | upstream source retained with GPL-3.0 license |

## Recovered manuscript-catalog assembly

The historical archive contains `cats/hypoDD_loc/ALL/zuhe.py`. That script:

1. reads the 15 already-created category `.txt` files;
2. parses columns 11–16 as year, month, day, hour, minute, second;
3. sorts all rows chronologically;
4. writes `ALL.txt`.

The second field is parsed correctly. Reproducing this operation yields the archived 6,344-row `ALL.txt` exactly.

The original script that generated the 15 category partitions themselves is not present in `cats.zip`. This is the remaining gap in the historical cross-model integration provenance and is explicitly retained as a limitation rather than reconstructed by assumption.

## Processing counts observed in `cats.zip`

| Model | REAL catalog | VELEST `new.cat` | hypoDD `.loc` | hypoDD `.reloc` |
|---|---:|---:|---:|---:|
| EQTransformer | 8,392 | 7,913 | 5,620 | 4,517 |
| RNN | 7,863 | 7,538 | 5,232 | 4,298 |
| U-Net | 7,078 | 6,748 | 4,908 | 3,907 |
| LPPNL | 6,733 | 6,460 | 4,777 | 3,912 |

The archived four-model VELEST category integration contains 9,955 events. The manuscript hypoDD-stage integrated product contains 6,344 events.

Intentionally excluded from the GitHub release: raw continuous waveform archives, caches/logs/IDE state, unrelated experiments, and external scientific binaries.
