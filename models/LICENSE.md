# Model artifact availability

The files in `models/regional/` are project-specific trained inference artifacts retained and distributed to support reproducibility of the manuscript workflow.

The repository includes four TorchScript (`.jit`) checkpoints and four corresponding PyTorch (`.pt`) files for EQTransformer, RNN, U-Net, and LPPNL. These trained artifacts were produced and retained as part of the project workflow and are distributed with the agreement of the project contributors.

The upstream source code and model architectures remain subject to their respective original licenses. Redistribution of the trained artifacts in this repository does not modify or supersede those upstream licensing terms.

Relevant upstream software, provenance, and licensing information are documented in `docs/THIRD_PARTY.md`.

SHA-256 identifiers for the distributed checkpoints are provided in `models/README.md` and `SHA256SUMS`.
