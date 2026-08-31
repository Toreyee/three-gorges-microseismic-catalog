# Final manuscript catalog

`final_catalog_6344.loc.txt` is the 6,344-event catalog used in the manuscript.

The `categories/` directory contains 15 mutually exclusive archived model-combination products:

- single-model-only categories: `EE`, `RR`, `UU`, `LL`;
- two-model categories: `ER`, `EU`, `EL`, `RU`, `RL`, `UL`;
- three-model categories: `ERU`, `ERL`, `EUL`, `RUL`;
- four-model category: `ERUL`.

The letters denote EQTransformer (`E`), RNN (`R`), U-Net (`U`), and LPPNL (`L`). Chronologically merging these 15 files reproduces `final_catalog_6344.loc.txt` exactly.

The archived materials do not contain the original script that generated the 15 category partitions from the four model-specific catalogs. The surviving historical `zuhe.py` script only merges and sorts those already-generated partitions. This limitation is documented in `docs/PROVENANCE.md`.
