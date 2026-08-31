#!/usr/bin/env python3
"""Rebuild and verify the archived 6,344-event manuscript catalog."""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXPECTED_CATEGORIES = ("ERUL","ERU","ERL","EUL","RUL","ER","EU","EL","RU","RL","UL","EE","RR","UU","LL")
CATEGORY_MODELS = {
    "E":"EQT", "R":"RNN", "U":"Unet", "L":"lppnl",
}
EXPECTED_SHA256 = "87f4b7105ef56e0cbfedca12b43d3a8ed9ae28fba8d33d36799e58feb971fb12"

def lines(path: Path) -> list[str]:
    return [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def timestamp(line: str) -> datetime:
    p=line.split()
    if len(p)!=18: raise ValueError(f"expected 18 fields, got {len(p)}: {line[:120]}")
    return datetime(*map(int,p[10:15])) + timedelta(seconds=float(p[15]))

def expected_models(category: str) -> set[str]:
    if category in {"EE","RR","UU","LL"}: return {CATEGORY_MODELS[category[0]]}
    return {CATEGORY_MODELS[c] for c in category}

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output-dir",type=Path,default=Path("build/manuscript-catalog"))
    ap.add_argument("--report",type=Path,default=Path("docs/manuscript_catalog_verification.json"))
    a=ap.parse_args(); root=a.repo_root.resolve()
    cdir=root/"data/final/categories"; final=root/"data/final/final_catalog_6344.loc.txt"
    out=a.output_dir if a.output_dir.is_absolute() else root/a.output_dir; out.mkdir(parents=True,exist_ok=True)

    model_rows={m:set(lines(root/f"data/intermediate/hypodd/{m}/hypoDD.loc")) for m in CATEGORY_MODELS.values()}
    category_counts={}; provenance_counts=Counter(); assembled=[]; category_provenance_ok=True
    for cat in EXPECTED_CATEGORIES:
        p=cdir/f"{cat}.txt"; rows=lines(p); category_counts[cat]=len(rows)
        allowed=expected_models(cat)
        for row in rows:
            sources={m for m,s in model_rows.items() if row in s}
            if not sources or not sources.issubset(allowed): category_provenance_ok=False
            provenance_counts["+".join(sorted(sources)) if sources else "NONE"] += 1
            assembled.append((timestamp(row),row))
    assembled.sort(key=lambda x:x[0])
    generated=[row for _,row in assembled]
    archived=lines(final)
    generated_path=out/"final_catalog_6344.loc.txt"
    generated_path.write_text("".join(x+"\n" for x in generated),encoding="utf-8",newline="\n")

    checks={
      "category_count_is_15": len(category_counts)==15,
      "category_sum_is_6344": sum(category_counts.values())==6344,
      "generated_rows_is_6344": len(generated)==6344,
      "archived_rows_is_6344": len(archived)==6344,
      "ordered_exact_match": generated==archived,
      "set_exact_match": set(generated)==set(archived),
      "archived_sha256_matches_expected": sha256(final)==EXPECTED_SHA256,
      "generated_sha256_matches_archived": sha256(generated_path)==sha256(final),
      "every_category_row_traces_to_expected_model_loc": category_provenance_ok,
    }
    report={
      "generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "final_catalog":str(final.relative_to(root)),
      "generated_catalog":(generated_path.relative_to(root).as_posix() if generated_path.is_relative_to(root) else generated_path.as_posix()),
      "category_counts":category_counts,
      "category_sum":sum(category_counts.values()),
      "archived_sha256":sha256(final),
      "generated_sha256":sha256(generated_path),
      "source_model_trace_counts":dict(sorted(provenance_counts.items())),
      "checks":checks,
      "all_checks_pass":all(checks.values()),
      "provenance_note":"This verifies deterministic reassembly of the archived 15 category products. The original program that created those category assignments from the four per-model .loc catalogs is not present in the recovered archive.",
    }
    rp=a.report if a.report.is_absolute() else root/a.report; rp.parent.mkdir(parents=True,exist_ok=True); rp.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(report,indent=2)); return 0 if report["all_checks_pass"] else 2
if __name__=="__main__": raise SystemExit(main())
