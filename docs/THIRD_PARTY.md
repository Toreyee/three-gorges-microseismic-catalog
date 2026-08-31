# Third-party components

## CSNBench / DiTing model code

Upstream: <https://github.com/cangyeone/csnbench>

Pinned snapshot: `d7d58f0926bbf8df4c9081e484634d6e1ecf689d`

License: GPL-3.0. The upstream license is retained in `third_party/csnbench/LICENSE`. The snapshot provides model definitions and upstream DiTing training utilities. It is not evidence that the manuscript-specific fine-tuning procedure is reproducible; that exact program was not present in the supplied workspaces.

## REAL and VELEST

Upstream: <https://github.com/Dal-mzhang/REAL>

License: MIT for the upstream repository. Executables are not copied into this repository. Users install them separately and provide their paths to workflow adapters.

## hypoDD and ph2dt

Upstream: <https://github.com/fwaldhauser/HypoDD>

The upstream repository does not present a standard open-source license file and its README asks users not to redistribute modified code. For that reason, this package contains only project-specific adapters/control inputs and does not vendor the hypoDD/ph2dt source or executables.

## Data and trained artifacts

Project-generated catalogs, processed products, figure inputs, and trained inference artifacts distributed with this repository are included with the agreement of the project contributors for scientific research and reproducibility.

Third-party software remains subject to its respective upstream license and terms. The repository does not redistribute external REAL, VELEST, hypoDD, or ph2dt executables.

The complete continuous-waveform archive is not distributed through this repository because of its size and data-management requirements.
