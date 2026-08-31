#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from obspy import Stream, Trace, UTCDateTime, read


# ----------------------------
# Utilities
# ----------------------------
def ensure_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)


def scan_seed_files(in_dir: Path) -> List[str]:
    """Recursively scan *.seed files under a directory."""
    out = []
    for root, _, files in os.walk(str(in_dir)):
        for fn in files:
            if fn.lower().endswith(".seed"):
                out.append(os.path.join(root, fn))
    out.sort()
    return out


def parse_seed_basename(basename: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse basename like:
      20170101.SX.BFS.seed   -> (ymd='20170101', net='SX', sta='BFS')

    Anything not matching this pattern returns None and will be skipped.
    """
    parts = basename.split(".")
    if len(parts) < 4:
        return None
    ymd, net, sta = parts[0], parts[1], parts[2]
    if not (len(ymd) == 8 and ymd.isdigit()):
        return None
    return ymd, net, sta


# ----------------------------
# Logging
# ----------------------------
class MonthLogger:
    def __init__(self, out_month_dir: Path, ym: str):
        self.out_month_dir = out_month_dir
        self.ym = ym
        self.bad_path = out_month_dir / f"{ym}.bad.log"
        self.fh = open(self.bad_path, "a", encoding="utf-8")

    def bad(self, msg: str) -> None:
        print(msg)
        try:
            self.fh.write(msg + "\n")
            self.fh.flush()
        except Exception:
            pass

    def close(self) -> None:
        try:
            self.fh.close()
        except Exception:
            pass


# ----------------------------
# Reading SEED/MSEED
# ----------------------------
def _try_rdseed(seed_file: str, tmp_dir: Path) -> Stream:
    """
    Fallback reader via external rdseed.
    This requires `rdseed` installed and in PATH.
    """
    ensure_dir(tmp_dir)
    # rdseed outputs many files; simplest is ask it to output miniseed and read back
    # -o 4 => miniSEED
    cmd = ["rdseed", "-f", seed_file, "-d", "-o", "4", "-q", "-p"]
    subprocess.run(cmd, cwd=str(tmp_dir), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Find generated miniSEED(s)
    mseed_files = []
    for root, _, files in os.walk(str(tmp_dir)):
        for fn in files:
            # rdseed may produce .mseed or no ext; we just try read everything as MSEED
            if fn.lower().endswith((".mseed", ".seed", ".miniseed")) or fn.startswith("DATA"):
                mseed_files.append(os.path.join(root, fn))
    if not mseed_files:
        # try reading any file as MSEED
        for root, _, files in os.walk(str(tmp_dir)):
            for fn in files:
                mseed_files.append(os.path.join(root, fn))

    st = Stream()
    for f in mseed_files:
        try:
            st += read(f, format="MSEED")
        except Exception:
            continue
    if len(st) == 0:
        raise RuntimeError("rdseed fallback produced no readable MSEED traces")
    return st


def read_seed_stream(seed_file: str, fallback_rdseed: bool = False) -> Stream:
    """
    Try reading as MiniSEED first; if failed, try generic read();
    if still failed and fallback_rdseed enabled, attempt rdseed.
    """
    try:
        return read(seed_file, format="MSEED")
    except Exception:
        pass

    try:
        return read(seed_file)
    except Exception as e:
        if not fallback_rdseed:
            raise e

    # rdseed fallback
    tmp_dir = Path("/tmp") / f"seed2real_rdseed_{os.getpid()}"
    try:
        st = _try_rdseed(seed_file, tmp_dir=tmp_dir)
        return st
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


# ----------------------------
# Writing
# ----------------------------
def write_trace_file(tr: Trace, out_path: Path, out_format: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tr.write(str(out_path), format=out_format)


# ----------------------------
# Core processing
# ----------------------------
def homogenize_and_merge_channel(
    stc: Stream,
    logger: MonthLogger,
    seed_file: str,
    target_sr: float = 100.0,
    allow_upsample_low_sr: bool = False,
) -> Optional[Trace]:
    """
    Make all traces in `stc` share the same sampling rate (= target_sr) and merge into one Trace.

    Policy:
      - sr == target_sr: keep
      - sr  > target_sr: downsample to target_sr (prefer integer decimation with anti-alias filter)
      - sr  < target_sr: drop by default (or interpolate if allow_upsample_low_sr=True)
    """
    if not stc or len(stc) == 0:
        return None

    def _sr(x: Trace) -> float:
        try:
            return float(x.stats.sampling_rate)
        except Exception:
            return float("nan")

    def _down_or_resample(tr: Trace) -> Optional[Trace]:
        sr = _sr(tr)
        if not (sr > 0):
            logger.bad(f"[BAD_SR] {seed_file} :: invalid sampling_rate={sr}")
            return None

        if abs(sr - target_sr) < 1e-6:
            return tr

        if sr < target_sr - 1e-6:
            if not allow_upsample_low_sr:
                logger.bad(
                    f"[DROP_LOW_SR] {seed_file} :: {tr.id} sr={sr:g} < target_sr={target_sr:g}"
                )
                return None
            try:
                tr.interpolate(sampling_rate=target_sr, method="linear")
                return tr
            except Exception as e:
                logger.bad(
                    f"[UPSAMPLE_FAIL] {seed_file} :: {tr.id} sr={sr:g} -> {target_sr:g} :: {type(e).__name__}: {e}"
                )
                return None

        # sr > target_sr -> downsample
        ratio = sr / target_sr
        try:
            k = int(round(ratio))
            if k >= 2 and abs(sr / k - target_sr) < 1e-6:
                # IMPORTANT: no_filter=False => anti-alias filter enabled
                tr.decimate(factor=k, no_filter=False, strict_length=False)
                return tr

            # Non-integer ratio fallback
            tr.resample(sampling_rate=target_sr, no_filter=False, strict_length=False)
            return tr
        except Exception as e:
            logger.bad(
                f"[DOWNSAMPLE_FAIL] {seed_file} :: {tr.id} sr={sr:g} -> {target_sr:g} :: {type(e).__name__}: {e}"
            )
            return None

    keep: List[Trace] = []
    for tr in list(stc):
        tr2 = _down_or_resample(tr)
        if tr2 is not None:
            keep.append(tr2)

    if not keep:
        return None

    stc2 = Stream(keep)

    try:
        stc2.sort(keys=["starttime"])
    except Exception:
        pass

    try:
        stc2.merge(method=1, fill_value=0)
        if len(stc2) == 0:
            return None
        if len(stc2) == 1:
            return stc2[0]
        stc2.traces.sort(key=lambda t: t.stats.npts, reverse=True)
        return stc2[0]
    except Exception as e:
        logger.bad(
            f"[MERGE_FAIL] {seed_file} :: {type(e).__name__}: {e} (fallback to longest trace)"
        )
        try:
            stc2.traces.sort(key=lambda t: t.stats.npts, reverse=True)
            return stc2[0] if len(stc2) else None
        except Exception:
            return None


def _done_marker_path(out_dir: Path, ymd: str, net: str, sta: str) -> Path:
    return out_dir / f".seed2real.done.{ymd}.{net}.{sta}"


def _expected_out_paths(out_dir: Path, prefix: str) -> List[Path]:
    # 断点续跑的“已完成”快速判定：至少三分量存在
    return [
        out_dir / f"{prefix}.SHE",
        out_dir / f"{prefix}.SHN",
        out_dir / f"{prefix}.SHZ",
    ]


def convert_seed_file(
    *,
    seed_file: str,
    ymd: str,
    net: str,
    sta: str,
    out_month_dir: Path,
    out_format: str,
    layout: str,
    chan_pattern: str,
    keep_net: bool,
    logger: MonthLogger,
    target_sr: float = 100.0,
    allow_upsample_low_sr: bool = False,
    skip_existing: bool = True,
    use_done_marker: bool = True,
    fallback_rdseed: bool = False,
) -> int:
    """
    Return:
      - -1 : skipped (already done)
      -  0 : no output produced
      - >0 : number of traces written
    """
    out_dir = out_month_dir / ymd if layout == "daydir" else out_month_dir
    ensure_dir(out_dir)

    prefix = f"{net}.{sta}" if keep_net else sta
    done_path = _done_marker_path(out_dir, ymd, net, sta)

    # 断点续跑：marker 存在则秒跳过
    if skip_existing and use_done_marker and done_path.exists():
        return -1

    # 断点续跑：如果三分量已经存在，也视为完成并写入 marker（加速下一次运行）
    if skip_existing and use_done_marker:
        exp = _expected_out_paths(out_dir, prefix)
        if all(p.exists() for p in exp):
            try:
                done_path.touch(exist_ok=True)
            except Exception:
                pass
            return -1

    # Read waveform
    try:
        st = read_seed_stream(seed_file, fallback_rdseed=fallback_rdseed)
    except Exception as e:
        logger.bad(f"[BAD] {seed_file} :: {type(e).__name__}: {e}")
        return 0

    # Channel selection pattern
    st = st.select(channel=chan_pattern)
    if len(st) == 0:
        logger.bad(f"[NOCHAN] {seed_file} :: no channels match pattern '{chan_pattern}'")
        return 0

    written = 0
    channels = sorted({tr.stats.channel for tr in st})

    for ch in channels:
        stc = st.select(channel=ch)
        tr = homogenize_and_merge_channel(
            stc=stc,
            logger=logger,
            seed_file=seed_file,
            target_sr=target_sr,
            allow_upsample_low_sr=allow_upsample_low_sr,
        )
        if tr is None:
            continue

        out_path = out_dir / f"{prefix}.{ch}"

        # 输出已存在则跳过（不覆盖）
        if skip_existing and out_path.exists():
            continue

        try:
            write_trace_file(tr, out_path, out_format)
            written += 1
        except Exception as e:
            logger.bad(f"[WRITE_FAIL] {seed_file} :: {out_path} :: {type(e).__name__}: {e}")
            continue

    # 写入 marker（只要这次“有效完成”：写了文件或输出已存在）
    if skip_existing and use_done_marker:
        try:
            if written > 0:
                done_path.touch(exist_ok=True)
            else:
                any_exist = any(p.exists() for p in out_dir.glob(f"{prefix}.*"))
                if any_exist:
                    done_path.touch(exist_ok=True)
        except Exception:
            pass

    return written


def convert_year(
    *,
    year: int,
    in_root: Path,
    out_root: Path,
    out_format: str = "SAC",
    layout: str = "daydir",
    keep_net: bool = True,
    chan_pattern: str = "SH[ENZ]",
    fallback_rdseed: bool = False,
    target_sr: float = 100.0,
    allow_upsample_low_sr: bool = False,
    skip_existing: bool = True,
    use_done_marker: bool = True,
) -> None:
    year_str = f"{year:04d}"

    in_year_dir = in_root / year_str
    if not in_year_dir.exists():
        print(f"[ERROR] Input year directory not found: {in_year_dir}")
        return

    out_year_dir = out_root / f"{year_str}test"
    ensure_dir(out_year_dir)

    total_written = 0
    total_bad = 0
    total_skipped = 0

    for month in range(1, 13):
        ym = f"{year_str}{month:02d}"
        in_month_dir = in_year_dir / ym
        out_month_dir = out_year_dir / ym

        if not in_month_dir.exists():
            print(f"[SKIP] {in_month_dir} not found")
            continue

        ensure_dir(out_month_dir)
        logger = MonthLogger(out_month_dir, ym)

        seed_files = scan_seed_files(in_month_dir)
        sx_files: List[str] = []
        sx_skipped = 0

        for f in seed_files:
            base = os.path.basename(f)
            info = parse_seed_basename(base)
            if info is None:
                sx_skipped += 1
                continue
            _, net, _ = info
            if net != "SX":
                sx_skipped += 1
                continue
            sx_files.append(f)

        print(f"[INFO] {ym}: {len(sx_files)} SX seed files (skipped {sx_skipped} non-SX/invalid)")

        for seed_file in sx_files:
            base = os.path.basename(seed_file)
            info = parse_seed_basename(base)
            if info is None:
                total_bad += 1
                logger.bad(f"[BADNAME] {seed_file}")
                continue

            ymd, net, sta = info

            try:
                n = convert_seed_file(
                    seed_file=seed_file,
                    ymd=ymd,
                    net=net,
                    sta=sta,
                    out_month_dir=out_month_dir,
                    out_format=out_format,
                    layout=layout,
                    chan_pattern=chan_pattern,
                    keep_net=keep_net,
                    logger=logger,
                    target_sr=target_sr,
                    allow_upsample_low_sr=allow_upsample_low_sr,
                    skip_existing=skip_existing,
                    use_done_marker=use_done_marker,
                    fallback_rdseed=fallback_rdseed,
                )
            except Exception as e:
                total_bad += 1
                logger.bad(f"[BAD] {seed_file} :: {type(e).__name__}: {e}")
                continue

            if n < 0:
                total_skipped += 1
                continue
            if n == 0:
                total_bad += 1
                continue

            total_written += n

        logger.close()

    print(
        f"[DONE] year={year_str} written={total_written} bad={total_bad} skipped={total_skipped} "
        f"(target_sr={target_sr:g}Hz, pattern='{chan_pattern}', layout={layout})"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert (Mini)SEED files to SAC (or other ObsPy formats), with year/month/day directory support."
    )
    p.add_argument("--year", type=int, required=True, help="Year to convert, e.g., 2017")
    p.add_argument("--in-root", type=Path, required=True, help="Input root directory containing source waveform files")
    p.add_argument("--out-root", type=Path, required=True, help="Output root directory for prepared waveforms")

    p.add_argument("--format", default="SAC", help="Output format (ObsPy supported), default: SAC")
    p.add_argument(
        "--layout",
        default="daydir",
        choices=["flat", "daydir"],
        help="Output layout: flat -> YYYYtest/YYYYMM/<files>; daydir -> YYYYtest/YYYYMM/YYYYMMDD/<files>",
    )
    p.add_argument(
        "--chan-pattern",
        default="SH[ENZ]",
        help="ObsPy channel selection pattern, e.g. 'SH[ENZ]' or '[SB]H[ENZ]'",
    )

    p.add_argument("--keep-net", action="store_true", help="Keep network code in output filename prefix (default)")
    p.add_argument("--drop-net", dest="keep_net", action="store_false", help="Drop network code in output filename prefix")
    p.set_defaults(keep_net=True)

    p.add_argument(
        "--target-sr",
        type=float,
        default=100.0,
        help="Force all output traces to this sampling rate (Hz). Default: 100",
    )
    p.add_argument(
        "--upsample-low-sr",
        action="store_true",
        help="If enabled, interpolate traces whose sampling rate is lower than target-sr. "
             "By default such traces are dropped (recommended).",
    )

    p.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Do not skip existing output files (overwrite). Default behavior is to skip.",
    )
    p.set_defaults(skip_existing=True)

    p.add_argument(
        "--no-done-marker",
        dest="use_done_marker",
        action="store_false",
        help="Disable '.seed2real.done.*' marker files. Default uses markers to resume quickly.",
    )
    p.set_defaults(use_done_marker=True)

    p.add_argument(
        "--fallback-rdseed",
        action="store_true",
        help="If ObsPy cannot read a file, try calling external 'rdseed' (must be installed) as a fallback.",
    )
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    convert_year(
        year=args.year,
        in_root=args.in_root,
        out_root=args.out_root,
        out_format=args.format,
        layout=args.layout,
        keep_net=args.keep_net,
        chan_pattern=args.chan_pattern,
        fallback_rdseed=args.fallback_rdseed,
        target_sr=args.target_sr,
        allow_upsample_low_sr=args.upsample_low_sr,
        skip_existing=args.skip_existing,
        use_done_marker=args.use_done_marker,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
