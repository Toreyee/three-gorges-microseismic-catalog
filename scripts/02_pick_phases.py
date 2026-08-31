#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
import datetime
import numpy as np

try:
    import torch
    from obspy import read
except ModuleNotFoundError:
    torch = None
    read = None

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **_kwargs):
        return iterable


# -----------------------------
# 工具：解析月份参数（支持 "10-12" / "10,11,12" / "1,2,5-7,12"）
# -----------------------------
def parse_months(s: str):
    s = (s or "").strip()
    if not s:
        return []
    out = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a.strip())
            b = int(b.strip())
            if a > b:
                a, b = b, a
            for m in range(a, b + 1):
                out.add(m)
        else:
            out.add(int(part))
    months = sorted([m for m in out if 1 <= m <= 12])
    return months


def sec_to_hms(sec: float) -> str:
    sec = float(sec) % 86400.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60.0
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# -----------------------------
# 三分量对齐（核心修复：避免 np.stack shape 报错）
# -----------------------------
def _force_to_sr(tr, target_sr: float):
    tr = tr.copy()
    sr = float(tr.stats.sampling_rate)

    if abs(sr - target_sr) < 1e-6:
        return tr

    # downsample
    if sr > target_sr + 1e-6:
        try:
            tr.filter("lowpass", freq=0.45 * target_sr, corners=4, zerophase=True)
        except Exception:
            pass

        ratio = sr / target_sr
        near_int = abs(ratio - round(ratio)) < 1e-3 and round(ratio) >= 1
        try:
            if near_int:
                q = int(round(ratio))
                tr.decimate(factor=q, no_filter=True, strict_length=False)
            else:
                tr.resample(target_sr)
        except Exception:
            tr.resample(target_sr)

        return tr

    # upsample
    try:
        tr.interpolate(sampling_rate=target_sr, method="linear", starttime=tr.stats.starttime)
    except Exception:
        tr.resample(target_sr)

    return tr


def align_3c(trE, trN, trZ, target_sr: float):
    """
    返回:
      x: (npts, 3) float32，列顺序 [E, N, Z]
      common_start: 对齐后公共起始时刻（UTCDateTime）
    失败返回 (None, None)
    """
    trE = _force_to_sr(trE, target_sr)
    trN = _force_to_sr(trN, target_sr)
    trZ = _force_to_sr(trZ, target_sr)

    start = max(trE.stats.starttime, trN.stats.starttime, trZ.stats.starttime)
    end = min(trE.stats.endtime, trN.stats.endtime, trZ.stats.endtime)
    if start >= end:
        return None, None

    for tr in (trE, trN, trZ):
        tr.trim(starttime=start, endtime=end, pad=False, nearest_sample=True)

    n = min(trE.stats.npts, trN.stats.npts, trZ.stats.npts)
    if n <= 0:
        return None, None

    dE = np.asarray(trE.data[:n], dtype=np.float32)
    dN = np.asarray(trN.data[:n], dtype=np.float32)
    dZ = np.asarray(trZ.data[:n], dtype=np.float32)

    x = np.stack([dE, dN, dZ], axis=1).astype(np.float32)
    return x, start


# -----------------------------
# 选择同一“通道前缀”的 E/N/Z（三分量别混用 BH* 与 SH*）
# -----------------------------
def pick_triplet(files):
    """
    files: list[str] - 当前台站一天目录下的文件名（不含路径）
    返回: (prefix, fE, fN, fZ) 的文件名（不含路径），找不到返回 None
    """
    # 建立 prefix -> comp -> filename
    by_prefix = {}
    for fn in files:
        parts = fn.split(".")
        if len(parts) < 3:
            continue
        ch = parts[-1].upper()            # e.g. BHZ
        if len(ch) < 3:
            continue
        prefix = ch[:2]                   # e.g. BH
        comp = ch[-1]                     # E/N/Z
        if comp not in ("E", "N", "Z"):
            continue
        by_prefix.setdefault(prefix, {})[comp] = fn

    # 你可以按需要调整优先级
    priority = ["HH", "BH", "EH", "SH", "LH"]
    for p in priority:
        d = by_prefix.get(p, {})
        if all(k in d for k in ("E", "N", "Z")):
            return p, d["E"], d["N"], d["Z"]

    # 如果不在优先级里，也选任意一个完整三分量
    for p, d in by_prefix.items():
        if all(k in d for k in ("E", "N", "Z")):
            return p, d["E"], d["N"], d["Z"]

    return None


# -----------------------------
# 单模型运行（外层循环模型；一次命令可跑多个模型）
# -----------------------------
def run_one_model(model: str, args):
    if torch is None or read is None:
        raise RuntimeError("Inference requires the optional dependencies: pip install -e '.[inference]'")

    # 路径
    ym_path = args.ym_path
    output_prefix = args.output_prefix or args.checkpoint_prefix.lower()
    out_pick = os.path.join(args.out_pick_dir, f"pick_{output_prefix}_{model}_{args.year}.txt")
    out_cnt = os.path.join(args.out_cnt_dir, f"phase_num_{args.year}_{model}.txt")
    mname = os.path.join(args.ckpt_dir, f"{args.checkpoint_prefix}.{model}.jit")

    os.makedirs(os.path.dirname(out_pick), exist_ok=True)
    os.makedirs(os.path.dirname(out_cnt), exist_ok=True)

    # 输出文件处理
    if (not args.keep_existing) and os.path.exists(out_pick):
        os.remove(out_pick)
    if (not args.keep_existing) and os.path.exists(out_cnt):
        os.remove(out_cnt)

    # 设备
    if args.device == "cuda" and not torch.cuda.is_available():
        device = torch.device("cpu")
        print("[WARN] CUDA 不可用，已切换到 CPU")
    else:
        device = torch.device(args.device)

    # 加载模型
    if not os.path.exists(mname):
        print(f"[SKIP] model ckpt not found: {mname}")
        return {"model": model, "P": 0, "S": 0, "skipped": True}

    sess = torch.jit.load(mname, map_location=device)
    sess.eval()
    sess.to(device)

    # 采样率：默认与原代码一致（100Hz），USTC 则 50Hz
    sr_used = float(args.sr) if args.sr is not None else (50.0 if args.ustc_picker else 100.0)

    # 月目录列表
    ym_dirs = [f"{args.year}{m:02d}" for m in args.months]
    ym_dirs = [d for d in ym_dirs if os.path.isdir(os.path.join(ym_path, d))]
    ym_dirs.sort()

    P_all, S_all = 0, 0

    for ym_dir in tqdm(ym_dirs, position=0, ncols=60, desc=f"[{model}] YM"):
        ymd_path = os.path.join(ym_path, ym_dir)
        mon = int(ym_dir[4:6])

        # 日目录 YYYYMMDD
        ymd_dirs = []
        for d in os.listdir(ymd_path):
            if re.match(rf"^{args.year}{mon:02d}\d{{2}}$", d) and os.path.isdir(os.path.join(ymd_path, d)):
                ymd_dirs.append(d)
        ymd_dirs.sort()

        P_mon, S_mon = 0, 0

        for ymd_dir in tqdm(ymd_dirs, position=1, ncols=60, desc=f"[{model}] YMD"):
            sac_path = os.path.join(ymd_path, ymd_dir)
            try:
                sac_files = os.listdir(sac_path)
            except Exception:
                continue

            # 分组：NET.STA
            sac_dict = {}
            for sac_file in sac_files:
                parts = sac_file.split(".")
                if len(parts) < 3:
                    continue
                key = ".".join(parts[:2])  # NET.STA
                sac_dict.setdefault(key, []).append(sac_file)

            P_day, S_day = 0, 0

            for key in tqdm(list(sac_dict.keys()), position=2, ncols=80, desc=f"[{model}] STA"):
                trip = pick_triplet(sac_dict[key])
                if trip is None:
                    # 缺三分量或混乱
                    continue
                _, fE, fN, fZ = trip
                sac_fileE = os.path.join(sac_path, fE)
                sac_fileN = os.path.join(sac_path, fN)
                sac_fileZ = os.path.join(sac_path, fZ)

                # 读波形
                try:
                    stE = read(sac_fileE)
                    stN = read(sac_fileN)
                    stZ = read(sac_fileZ)
                except Exception:
                    continue
                if len(stE) == 0 or len(stN) == 0 or len(stZ) == 0:
                    continue

                trE, trN, trZ = stE[0], stN[0], stZ[0]

                # 关键：对齐三分量（解决 shape mismatch）
                x, common_start = align_3c(trE, trN, trZ, target_sr=sr_used)
                if x is None:
                    continue

                # 以对齐后的起点计算日内秒
                stime = common_start.datetime  # UTC datetime
                dtime = stime.replace(hour=0, minute=0, second=0, microsecond=0)
                tt = (stime - dtime).total_seconds()
                ymd_str = dtime.strftime("%Y-%m-%d")

                # 推理
                with torch.no_grad():
                    xt = torch.as_tensor(x, dtype=torch.float32, device=device)
                    y = sess(xt)
                    phase = y.detach().cpu().numpy()

                # 输出
                with open(out_pick, "a", encoding="utf-8") as f:
                    f.write(f"#{sac_fileZ}\n")
                    for line in phase:
                        phase_id = int(line[0])   # 0=P，其它=S（与原脚本一致）
                        idx = float(line[1])
                        score = float(line[2])

                        sec = (tt + idx / sr_used) % 86400.0
                        otime = sec_to_hms(sec)

                        if phase_id == 0:
                            P_day += 1
                            P_mon += 1
                            P_all += 1
                            f.write(f"P,{sec:8.2f},{score:.2f},{key[:7]},{ymd_str} {otime}\n")
                        else:
                            S_day += 1
                            S_mon += 1
                            S_all += 1
                            f.write(f"S,{sec:8.2f},{score:.2f},{key[:7]},{ymd_str} {otime}\n")

            # 写当天统计
            with open(out_cnt, "a", encoding="utf-8") as f:
                f.write(f"{ymd_dir}\n")
                f.write(f"P:{P_day} S:{S_day}\n")

        # 写当月统计
        with open(out_cnt, "a", encoding="utf-8") as f:
            f.write(f"{args.year} 年 {mon:02d} 月 P 相拾取: {P_mon}，S 相拾取 {S_mon}\n")

    # 写总计
    with open(out_cnt, "a", encoding="utf-8") as f:
        f.write(f"总计p相拾取 {P_all}， 总共S相拾取 {S_all}\n")

    # 释放显存
    del sess
    if device.type == "cuda":
        torch.cuda.empty_cache()

    return {"model": model, "P": P_all, "S": S_all, "skipped": False}


def build_argparser():
    default_ckpt = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "models",
        "regional",
    )
    p = argparse.ArgumentParser(
        description="Run DiTing TorchScript pickers on daily 3C SAC output from seed2real.py (multi-model supported)."
    )
    p.add_argument("--year", type=str, default="2018", help="Year, e.g. 2018")
    p.add_argument("--months", type=str, default="1-12", help="Months, e.g. '1-12' or '10,11,12'")
    p.add_argument("--models", type=str, default="eqt,rnn,unet,lppnl",
                   help="Comma-separated models, e.g. 'unet,rnn,eqt,lppnl'")
    p.add_argument("--ym-path", type=str, required=True,
                   help="Prepared waveform root containing YYYYMM folders")
    p.add_argument("--ckpt-dir", type=str, default=default_ckpt,
                   help="TorchScript checkpoint directory")
    p.add_argument("--checkpoint-prefix", type=str, default="diting",
                   help="Checkpoint filename prefix; files are <prefix>.<model>.jit (default: diting)")
    p.add_argument("--output-prefix", type=str, default=None,
                   help="Prefix used in pick output filenames; defaults to lowercase checkpoint prefix")
    p.add_argument("--out-pick-dir", type=str, required=True,
                   help="Output picks dir")
    p.add_argument("--out-cnt-dir", type=str, required=True,
                   help="Output counts dir")
    p.add_argument("--device", type=str, default="cpu", choices=["cuda", "cpu"], help="Device")
    p.add_argument("--ustc-picker", action="store_true", help="If set, use 50Hz (else 100Hz)")
    p.add_argument("--sr", type=float, default=None, help="Override sampling rate used for time mapping (Hz)")
    p.add_argument("--keep-existing", action="store_true", help="Do not remove existing output files")
    return p


def main():
    args = build_argparser().parse_args()
    args.months = parse_months(args.months)
    if not args.months:
        raise SystemExit("[ERR] months parsed empty; example: --months 10-12")

    args.models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not args.models:
        raise SystemExit("[ERR] models parsed empty; example: --models rnn,unet,eqt,lppnl")

    # 逐模型运行（同一次命令完成多模型拾取与统计）
    results = []
    for model in args.models:
        print(f"\n========== RUN MODEL: {model} ==========")
        results.append(run_one_model(model, args))

    # 终端汇总打印
    print("\n========== SUMMARY ==========")
    print(f"YM_PATH: {args.ym_path}")
    print(f"MONTHS : {args.months}")
    print(f"DEVICE : {args.device}")
    print(f"SR_USED: {args.sr if args.sr is not None else (50.0 if args.ustc_picker else 100.0)}")
    print("----------------------------------------")
    print(f"{'MODEL':<10} {'P_TOTAL':>10} {'S_TOTAL':>10} {'STATUS':>10}")
    for r in results:
        status = "SKIP" if r.get("skipped") else "OK"
        print(f"{r['model']:<10} {r['P']:>10} {r['S']:>10} {status:>10}")


if __name__ == "__main__":
    main()
