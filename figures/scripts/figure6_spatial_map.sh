#!/usr/bin/env bash
set -e

# =========================
# Input files
# =========================
MANUAL="manual_lonlat.txt"
FINAL="final_lonlat.txt"
TGD="tgd.xy.txt"
FAULT_SHP="faults_fig6.gmt"
#BOUNDARY_GMT="block_boundaries.gmt"

# OSM shapefiles
OSM_DIR="hubei-260324-free.shp"
WATER_POLY="main_water_poly_fig6.shp"
WATER_LINE="${OSM_DIR}/gis_osm_waterways_free_1.shp"

# Map region and projection
REGION="109.55/111.35/30.45/31.45"
PROJ="M8.2c"

# Output
OUT="Fig6_manual_vs_final_OSM_publish"

gmt begin "$OUT" pdf,png
    # =========================
    # Global style (publication-oriented)
    # =========================
    gmt set FONT_ANNOT_PRIMARY 7.5p,Helvetica,black
    gmt set FONT_LABEL 8.5p,Helvetica,black
    gmt set FONT_TITLE 9p,Helvetica-Bold,black
    gmt set MAP_FRAME_TYPE plain
    gmt set MAP_FRAME_PEN 0.7p
    gmt set MAP_TICK_PEN_PRIMARY 0.5p
    gmt set FORMAT_GEO_MAP ddd.xxF
    gmt set MAP_LABEL_OFFSET 3p
    gmt set MAP_TITLE_OFFSET 5p

    # keep topo CPT disabled because relief is removed
    # gmt makecpt -Cgray -T-2000/3000/50 -Z -H > topo.cpt

    # slightly wider gap is cleaner for publication
    gmt subplot begin 1x2 -Fs8.0c/7.0c -M0.70c/0.30c

        # =========================
        # (a) Official catalog
        # =========================
        gmt subplot set 0,0
        gmt basemap -R$REGION -J$PROJ \
            -Bxa0.5f0.25+l"Longitude (°E)" \
            -Bya0.25f0.125+l"Latitude (°N)" \
            -BWSen

        # -------------------------
        # Water polygons: muted gray scientific style
        # -------------------------
        if [ -f "$WATER_POLY" ]; then
            gmt plot "$WATER_POLY" -R$REGION -J$PROJ -Ggray90 -W0.10p,gray72
        fi

        # Optional waterways (kept off for cleaner figure)
        # if [ -f "$WATER_LINE" ]; then
        #     gmt plot "$WATER_LINE" -R$REGION -J$PROJ -W0.10p,gray70
        # fi

        # -------------------------
        # Faults: lighter and thinner
        # -------------------------
        if [ -f "$FAULT_SHP" ]; then
            gmt plot "$FAULT_SHP" -R$REGION -J$PROJ -W0.26p,gray55
        fi

        # Optional block boundaries
        # if [ -f "$BOUNDARY_GMT" ]; then
        #     gmt plot "$BOUNDARY_GMT" -R$REGION -J$PROJ -W0.7p,gray40
        # fi

        # -------------------------
        # Earthquakes: hollow black-gray style
        # -------------------------
        #gmt plot "$MANUAL" -R$REGION -J$PROJ -Sc0.022c -Gwhite -W0.18p,black@75
        gmt plot "$MANUAL" -R$REGION -J$PROJ -Sc0.018c -Gblack@78 -W0p

        # -------------------------
        # TGD marker
        # -------------------------
        gmt plot "$TGD" -R$REGION -J$PROJ -Sa0.16c -Gwhite -W0.50p,black
        echo "111.003827 30.832958 TGD" | \
            gmt text -R$REGION -J$PROJ -F+f6.3p,Helvetica,black+jLM -Dj0.035c/0.015c

        # -------------------------
        # Panel title
        # -------------------------
        echo "109.60 31.39 (a) Official catalog" | \
            gmt text -R$REGION -J$PROJ -F+f8.2p,Helvetica-Bold,black+jTL

        # =========================
        # (b) Final high-precision catalog
        # =========================
        gmt subplot set 0,1
        gmt basemap -R$REGION -J$PROJ \
            -Bxa0.5f0.25+l"Longitude (°E)" \
            -Bya0.25f0.125 \
            -BWSen

        # -------------------------
        # Water polygons: muted gray scientific style
        # -------------------------
        if [ -f "$WATER_POLY" ]; then
            gmt plot "$WATER_POLY" -R$REGION -J$PROJ -Ggray90 -W0.10p,gray72
        fi

        # Optional waterways (kept off for cleaner figure)
        # if [ -f "$WATER_LINE" ]; then
        #     gmt plot "$WATER_LINE" -R$REGION -J$PROJ -W0.10p,gray70
        # fi

        # -------------------------
        # Faults: lighter and thinner
        # -------------------------
        if [ -f "$FAULT_SHP" ]; then
            gmt plot "$FAULT_SHP" -R$REGION -J$PROJ -W0.26p,gray60
        fi

        # Optional block boundaries
        # if [ -f "$BOUNDARY_GMT" ]; then
        #     gmt plot "$BOUNDARY_GMT" -R$REGION -J$PROJ -W0.7p,gray40
        # fi

        # -------------------------
        # Earthquakes: slightly smaller hollow symbols for dense catalog
        # -------------------------
        #gmt plot "$FINAL" -R$REGION -J$PROJ -Sc0.020c -Gwhite -W0.16p,black@70
        gmt plot "$FINAL" -R$REGION -J$PROJ -Sc0.015c -Gblack@65 -W0p

        # -------------------------
        # TGD marker
        # -------------------------
        gmt plot "$TGD" -R$REGION -J$PROJ -Sa0.16c -Gwhite -W0.50p,black
        echo "111.003827 30.832958 TGD" | \
            gmt text -R$REGION -J$PROJ -F+f6.3p,Helvetica,black+jLM -Dj0.035c/0.015c

        # -------------------------
        # Panel title
        # -------------------------
        echo "109.60 31.39 (b) Final high-precision catalog" | \
            gmt text -R$REGION -J$PROJ -F+f8.2p,Helvetica-Bold,black+jTL

    gmt subplot end
gmt end