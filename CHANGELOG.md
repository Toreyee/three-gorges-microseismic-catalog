# Changelog

## 0.3.0 — manuscript-catalog alignment

- reconciled the release against the recovered historical `cats.zip` processing archive;
- designated the 6,344-event catalog actually used in the manuscript as the main repository product;
- moved the 15 archived `hypoDD.loc` model-combination partitions into `data/final/categories/`;
- added deterministic verification that chronological merging of those 15 files reproduces the 6,344-event manuscript catalog exactly;
- verified from the recovered historical `zuhe.py` that year/month/day/hour/minute/second are parsed correctly during final category merging;
- documented the remaining missing provenance step: the original program that generated the 15 category partitions is not present in the archive;
- aligned Figures 5–6 and repository documentation with the 6,344-event manuscript product;
- retained per-model `.reloc` outputs as intermediate hypoDD products without designating a separate cross-model `.reloc` integration as the manuscript release product;
- documented that 6,344 / 632 = 10.04, so any manuscript “8.5-fold” statement requires revision if 6,344 is retained.

## 0.2.0 — release-candidate restructuring

- parameterized historical processing wrappers;
- added catalog parsing, audit, tests, CI, figure runner, checksums and model verification;
- excluded raw continuous waveforms from Git due to size.
