# Catalog data-quality note

## Retained manuscript product

The release product is the 6,344-event catalog used in the manuscript:

| Product | Rows | Interpretation |
|---|---:|---|
| `data/final/final_catalog_6344.loc.txt` | 6,344 | integrated manuscript catalog; exact archived product used for manuscript Figures 5–6 |
| `data/reference/official_catalog_2018.txt` | 632 | official/reference catalog |

The final catalog has SHA-256:

```text
87f4b7105ef56e0cbfedca12b43d3a8ed9ae28fba8d33d36799e58feb971fb12
```

## Model-specific hypoDD products

The supplied archive contains both `hypoDD.loc` and `hypoDD.reloc` for every model:

| Model | `hypoDD.loc` | `hypoDD.reloc` |
|---|---:|---:|
| EQTransformer | 5,620 | 4,517 |
| RNN | 5,232 | 4,298 |
| U-Net | 4,908 | 3,907 |
| LPPNL | 4,777 | 3,912 |

According to the hypoDD documentation, `.loc` is the initial-hypocenter output and `.reloc` is the relocated-hypocenter output. The manuscript's 6,344-event integrated product is preserved in `.loc` format, so it should be described as the **integrated manuscript catalog** rather than as a cross-model `.reloc` catalog.

## What the recovered archive proves

The newly supplied historical `cats.zip` resolves an earlier provenance ambiguity:

1. `cats/hypoDD_loc/ALL/ALL.txt` contains exactly 6,344 rows and is byte-identical to the manuscript catalog distributed here.
2. The 15 files under `cats/hypoDD_loc/ALL/` sum to 6,344 rows.
3. The surviving historical `zuhe.py` correctly reads year, month, day, hour, minute, and the true second field, then chronologically merges the 15 category files.
4. Re-running that merge logic reproduces `ALL.txt` exactly, in the same order.
5. Every archived category row is an exact row from one of the corresponding model-specific `hypoDD.loc` files.

The recovered `zuhe.py` parses the true second field correctly; the preserved 6,344-event assembly is therefore documented from the recovered files without attributing it to a time-field parsing error.

## Remaining provenance limitation

The archive does **not** contain the historical program that originally created the 15 category partitions from the four model-specific `hypoDD.loc` files. Consequently, this repository can deterministically rebuild the 6,344-event catalog from the archived category products, but it does not claim a from-scratch reconstruction of those category assignments from the four `.loc` files alone.

## Count-ratio consistency

The official/reference file contains 632 events:

```text
6344 / 632 = 10.0380
```

Thus a manuscript statement of “approximately 8.5-fold” is not numerically consistent with the retained 6,344-event product. If 6,344 remains the publication count, the comparison should be revised (for example, “approximately 10 times as many events as the official catalog”) or the fold statement should be omitted.

## Other cautions

- The 18-column manuscript catalog contains non-finite magnitude placeholders and is not itself the magnitude-analysis table.
- The `.loc` formal-error columns are zero-filled in the archived product and should not be interpreted as measured zero uncertainty.
- The exact historical hypoDD and external executable version identifiers were not recoverable from the archived workspace; the repository therefore documents the available configuration files, inputs, and upstream software sources instead.
