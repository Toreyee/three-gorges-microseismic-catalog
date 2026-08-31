# Data products

- `final/` contains the **6,344-event integrated manuscript catalog** and its 15 archived model-combination partitions.
- `reference/` contains the 632-event official/reference catalog used for comparison.
- `intermediate/` contains compact per-model outputs from REAL, VELEST, and hypoDD so the processing chain can be audited without distributing the continuous waveform archive.

The final manuscript catalog is an 18-column `hypoDD.loc`-format product assembled from the archived category partitions after the model-specific hypoDD processing stage. The per-model `.reloc` files are retained as intermediate relocation outputs, but no separate cross-model `.reloc` integration is designated as the manuscript release product.

The raw waveform archive is intentionally excluded from GitHub because of its size. See `docs/DATA_AVAILABILITY.md`, `docs/PROVENANCE.md`, and `docs/DATA_DICTIONARY.md`.
