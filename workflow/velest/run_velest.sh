#!/usr/bin/env bash
set -euo pipefail
usage() {
  cat <<'EOF'
Usage: run_velest.sh --station-all FILE --model-nd FILE --phase-sa FILE [options]
Required:
  --station-all FILE     station_all.dat input
  --model-nd FILE        1-D velocity model used by convertformat.pl
  --phase-sa FILE        REAL phaseSA_allday.txt input
Options:
  --velest-bin PATH      VELEST executable/name (default: velest)
  --work-dir DIR         isolated output directory (default: ./build/velest)
  --isingle INT          VELEST mode passed to converter (default: 1)
  --station-gap DEG      output filter (default: 300)
  --res-max SEC          output residual filter (default: 0.5)
  --center-lat DEG       conversion center latitude (default: 31.00)
  --center-lon DEG       pre-conversion center longitude (historical default: -110.30)
  --distance-max KM      conversion distance limit (default: 200)
  -h, --help             show this help
EOF
}
station_all=""; model_nd=""; phase_sa=""; velest_bin="velest"; work_dir="$PWD/build/velest"
isingle="1"; stationgap="300"; resmax="0.5"; clat="31.00"; clon="-110.30"; dismax="200"
while (($#)); do
  case "$1" in
    --station-all) station_all="${2:?}"; shift 2 ;;
    --model-nd) model_nd="${2:?}"; shift 2 ;;
    --phase-sa) phase_sa="${2:?}"; shift 2 ;;
    --velest-bin) velest_bin="${2:?}"; shift 2 ;;
    --work-dir) work_dir="${2:?}"; shift 2 ;;
    --isingle) isingle="${2:?}"; shift 2 ;;
    --station-gap) stationgap="${2:?}"; shift 2 ;;
    --res-max) resmax="${2:?}"; shift 2 ;;
    --center-lat) clat="${2:?}"; shift 2 ;;
    --center-lon) clon="${2:?}"; shift 2 ;;
    --distance-max) dismax="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERR] unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
for name in station_all model_nd phase_sa; do [[ -n "${!name}" ]] || { echo "[ERR] --${name//_/-} is required" >&2; exit 2; }; done
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for input in "$station_all" "$model_nd" "$phase_sa"; do [[ -f "$input" ]] || { echo "[ERR] missing input: $input" >&2; exit 1; }; done
if [[ "$velest_bin" == */* ]]; then [[ -x "$velest_bin" ]] || { echo "[ERR] not executable: $velest_bin" >&2; exit 1; }; else command -v "$velest_bin" >/dev/null || { echo "[ERR] VELEST not found: $velest_bin" >&2; exit 1; }; fi
mkdir -p "$work_dir"; work_dir="$(cd "$work_dir" && pwd)"
station_all="$(cd "$(dirname "$station_all")" && pwd)/$(basename "$station_all")"
model_nd="$(cd "$(dirname "$model_nd")" && pwd)/$(basename "$model_nd")"
phase_sa="$(cd "$(dirname "$phase_sa")" && pwd)/$(basename "$phase_sa")"
cp "$script_dir/regionsnamen.dat" "$script_dir/regionskoord.dat" "$work_dir/"; cd "$work_dir"
perl "$script_dir/convertformat.pl" "$clat" "$clon" "$dismax" "$isingle" "$station_all" "$model_nd" "$phase_sa"
sed -i 's/\r$//' velest.cmn velest.mod velest.sta velest.pha 2>/dev/null || true
for product in velest.cmn velest.pha initial.cat; do [[ -s "$product" ]] || { echo "[ERR] not generated: $work_dir/$product" >&2; exit 1; }; done
"$velest_bin" < velest.cmn > velest.stdout 2>&1
[[ -s final.CNV ]] || { echo "[ERR] final.CNV missing; inspect $work_dir/velest.stdout" >&2; exit 2; }
[[ -s out.CHECK ]] || { echo "[ERR] out.CHECK missing; inspect $work_dir/velest.stdout" >&2; exit 2; }
perl "$script_dir/convertoutput.pl" "$stationgap" "$resmax" new.cat dele.cat
[[ -s new.cat ]] || { echo "[ERR] new.cat missing after convertoutput.pl" >&2; exit 3; }
echo "[OK] VELEST outputs: $work_dir"; wc -l initial.cat new.cat
