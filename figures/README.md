# Figures 2–8

Requirements: Graphviz for Figure 2; Python/NumPy/pandas/Matplotlib/Pillow for Figures 3–5 and 7–8; GMT 6.5 + POSIX shell for Figure 6.

Figures 5–6 use the 6,344-event manuscript catalog:

```bash
python scripts/reproduce_figures.py --repo-root . --catalog-mode manuscript --report docs/figure_reproduction_report.json
```

The archived manuscript Figure 5–6 outputs are preserved under `figures/reference/manuscript/`. The same products are placed under `figures/output/` as the paper-aligned release figures.
