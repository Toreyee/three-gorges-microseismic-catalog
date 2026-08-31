# Recovered manuscript-catalog assembly helper

`zuhe.py` is copied from `cats/hypoDD_loc/ALL/zuhe.py` in the recovered historical processing archive. It reads the already-generated category `.txt` files, parses the true year/month/day/hour/minute/second fields, sorts events chronologically, and writes `ALL.txt`.

It does **not** generate the 15 category assignments from the four model-specific catalogs. The original category-generation program was not present in the recovered archive. For portable verification in this repository, use `scripts/10_verify_manuscript_catalog.py`.
