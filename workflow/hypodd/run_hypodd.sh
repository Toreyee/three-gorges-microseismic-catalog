#!/usr/bin/env bash
set -euo pipefail
usage() {
  cat <<'EOF'
Usage: run_hypodd.sh --source real|velest --station-file FILE --phase-input FILE [options]
Required:
  --source KIND          real or velest
  --station-file FILE    station_all.dat-like station file
  --phase-input FILE     REAL phaseSA or VELEST final.CNV, depending on --source
Options:
  --ph2dt-bin PATH       ph2dt executable/name (default: ph2dt)
  --hypodd-bin PATH      hypoDD executable/name (default: hypoDD)
  --python PATH          Python interpreter (default: python3)
  --work-dir DIR         isolated output directory (default: ./build/hypodd)
  --rms-threshold SEC    VELEST-to-hypoDD filter (default: 0.5)
  --gap-threshold DEG    VELEST-to-hypoDD filter (default: 300)
  --max-depth-km KM      VELEST-to-hypoDD filter (default: 20)
  -h, --help             show this help
EOF
}
source_kind=""; station_file=""; phase_input=""; ph2dt_bin="ph2dt"; hypodd_bin="hypoDD"; python_bin="python3"; work_dir="$PWD/build/hypodd"; rms_threshold="0.5"; gap_threshold="300"; max_depth_km="20"
while (($#)); do
 case "$1" in
  --source) source_kind="${2:?}"; shift 2;; --station-file) station_file="${2:?}"; shift 2;; --phase-input) phase_input="${2:?}"; shift 2;;
  --ph2dt-bin) ph2dt_bin="${2:?}"; shift 2;; --hypodd-bin) hypodd_bin="${2:?}"; shift 2;; --python) python_bin="${2:?}"; shift 2;; --work-dir) work_dir="${2:?}"; shift 2;;
  --rms-threshold) rms_threshold="${2:?}"; shift 2;; --gap-threshold) gap_threshold="${2:?}"; shift 2;; --max-depth-km) max_depth_km="${2:?}"; shift 2;;
  -h|--help) usage; exit 0;; *) echo "[ERR] unknown argument: $1" >&2; usage >&2; exit 2;; esac
done
[[ "$source_kind" == "real" || "$source_kind" == "velest" ]] || { echo "[ERR] --source must be real or velest" >&2; exit 2; }
[[ -n "$station_file" ]] || { echo "[ERR] --station-file is required" >&2; exit 2; }; [[ -n "$phase_input" ]] || { echo "[ERR] --phase-input is required" >&2; exit 2; }
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for input in "$station_file" "$phase_input"; do [[ -f "$input" ]] || { echo "[ERR] missing input: $input" >&2; exit 1; }; done
for program in "$ph2dt_bin" "$hypodd_bin"; do if [[ "$program" == */* ]]; then [[ -x "$program" ]] || { echo "[ERR] not executable: $program" >&2; exit 1; }; else command -v "$program" >/dev/null || { echo "[ERR] not found: $program" >&2; exit 1; }; fi; done
command -v "$python_bin" >/dev/null || [[ -x "$python_bin" ]] || { echo "[ERR] Python not found: $python_bin" >&2; exit 1; }
mkdir -p "$work_dir"; work_dir="$(cd "$work_dir" && pwd)"
station_file="$(cd "$(dirname "$station_file")" && pwd)/$(basename "$station_file")"; phase_input="$(cd "$(dirname "$phase_input")" && pwd)/$(basename "$phase_input")"
cp "$script_dir/ph2dt.inp" "$script_dir/hypoDD.inp" "$work_dir/"; awk '{print($4,$2,$1)}' "$station_file" > "$work_dir/station.dat"
case "$source_kind" in real) cp "$phase_input" "$work_dir/hypoDD.pha";; velest) "$python_bin" "$script_dir/velest2hypoDD.py" "$phase_input" "$work_dir/hypoDD.pha" "$rms_threshold" "$gap_threshold" "$max_depth_km";; esac
cd "$work_dir"; "$ph2dt_bin" ph2dt.inp; [[ -s dt.ct ]] || { echo "[ERR] ph2dt did not create dt.ct" >&2; exit 2; }; "$hypodd_bin" hypoDD.inp
[[ -s hypoDD.loc ]] || { echo "[ERR] hypoDD.loc missing" >&2; exit 3; }; [[ -s hypoDD.reloc ]] || { echo "[ERR] hypoDD.reloc missing" >&2; exit 3; }
echo "[OK] hypoDD outputs: $work_dir"; wc -l hypoDD.loc hypoDD.reloc
