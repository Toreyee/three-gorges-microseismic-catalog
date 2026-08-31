# Data dictionary

All catalogs are whitespace-delimited unless noted.

## `hypoDD.loc`

18 columns following the hypoDD initial-hypocenter output layout:

`event_id`, latitude, longitude, depth, local Cartesian offsets (`x/y/z`), coordinate-error fields, year, month, day, hour, minute, second, magnitude, cluster identifier.

The 6,344-event manuscript catalog is stored in this 18-column format. The recovered historical merge script reads the true second field correctly.

## `hypoDD.reloc`

24 columns following the hypoDD relocated-hypocenter output layout. The parser labels the trailing fields:

`ncc_p`, `ncc_s`, `nct_p`, `nct_s`, `rms_cc_s`, `rms_ct_s`, `cluster_id`.

These per-model files are retained as intermediate relocation products for audit. They are not designated as the cross-model manuscript release product.

## Model-combination codes

`E` = EQTransformer, `R` = RNN, `U` = U-Net, `L` = LPPNL. Codes such as `ERUL` identify the archived four-model category. Doubled codes (`EE`, `RR`, `UU`, `LL`) are the historical single-model-only categories.

## Official catalog

`official_catalog_2018.txt` contains the 632-event reference used by manuscript comparisons. Public release should add the explicit source agency, retrieval date, timezone, units, and redistribution/license statement.

Figure 7–8 magnitude summary CSVs are separate recalibrated analysis products and are not the non-finite magnitude field in the combined hypoDD-format catalogs.
