# Technical status

## Verified

- 6,344-event manuscript catalog is byte-identical to `cats/hypoDD_loc/ALL/ALL.txt`.
- Fifteen archived model-combination category files sum to 6,344 rows.
- Chronological reassembly of those category files reproduces the manuscript catalog exactly.
- All final-category rows can be traced to the corresponding model-specific `hypoDD.loc` inputs.
- Per-model REAL, VELEST, `hypoDD.loc`, and `hypoDD.reloc` products are retained for audit.
- Bundled TorchScript checkpoints pass checksum verification and CPU loading.
- Raw continuous waveforms are intentionally external.

## Important interpretation

`hypoDD.loc` and `hypoDD.reloc` are distinct hypoDD outputs. The retained 6,344-event manuscript product is in `.loc` format. It should therefore be described as the integrated manuscript catalog or hypoDD-stage integrated catalog, not as a combined `.reloc` catalog.

## Remaining limitations

1. The original script that created the 15 category partitions from the four per-model `.loc` files is absent from the recovered archive.
2. Exact historical version identifiers for some external executables were not recoverable from the archived workspace; available configuration files and upstream software sources are documented for reproducibility.
3. The manuscript's fold-increase statement must be reconciled with 6,344 versus the 632-event reference catalog.
4. Public redistribution rights for model artifacts and third-party/reference data remain to be confirmed.
5. Strict training-from-scratch reproduction of manuscript-specific fine-tuning is not supported by the available materials.
