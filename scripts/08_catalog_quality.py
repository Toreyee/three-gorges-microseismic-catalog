#!/usr/bin/env python3
"""Profile the manuscript catalog and compact processing products."""
from __future__ import annotations
import argparse, hashlib, json, math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXPECTED_FINAL_SHA256="87f4b7105ef56e0cbfedca12b43d3a8ed9ae28fba8d33d36799e58feb971fb12"

def rows(path:Path): return [x.split() for x in path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
def sha256(path:Path):
 h=hashlib.sha256();
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def event_time(p): return datetime(*map(int,p[10:15]))+timedelta(seconds=float(p[15]))
def profile(path:Path,width:int,root:Path):
 r=rows(path); widths=Counter(map(len,r));
 if set(widths)!={width}: raise ValueError(f"{path}: expected {width} fields; observed {dict(widths)}")
 ts=[event_time(x) for x in r]; mags=[float(x[16]) for x in r]
 return {"path":path.relative_to(root).as_posix(),"rows":len(r),"columns":width,"sha256":sha256(path),"chronologically_sorted":all(a<=b for a,b in zip(ts,ts[1:])),"time_min":min(ts).isoformat(sep=" ") if ts else None,"time_max":max(ts).isoformat(sep=" ") if ts else None,"finite_magnitude_rows":sum(math.isfinite(x) for x in mags),"nonfinite_magnitude_rows":sum(not math.isfinite(x) for x in mags),"zero_formal_error_values":sum(float(v)==0 for x in r for v in x[7:10]) if width==18 else None}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument("--output",type=Path);ap.add_argument("--fail-on-structural-error",action="store_true");a=ap.parse_args();root=a.repo_root.resolve()
 final=root/"data/final/final_catalog_6344.loc.txt"; official=root/"data/reference/official_catalog_2018.txt"; fp=profile(final,18,root); official_n=len(rows(official))
 cats={p.stem:len(rows(p)) for p in sorted((root/"data/final/categories").glob("*.txt"))}
 per={m:{"loc_rows":len(rows(root/f"data/intermediate/hypodd/{m}/hypoDD.loc")),"reloc_rows":len(rows(root/f"data/intermediate/hypodd/{m}/hypoDD.reloc"))} for m in ("EQT","RNN","Unet","lppnl")}
 checks={"final_rows_6344":fp["rows"]==6344,"official_rows_632":official_n==632,"category_count_15":len(cats)==15,"category_sum_6344":sum(cats.values())==6344,"final_sha256":fp["sha256"]==EXPECTED_FINAL_SHA256}
 report={"generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"manuscript_catalog":fp,"official_catalog":{"path":official.relative_to(root).as_posix(),"rows":official_n,"sha256":sha256(official)},"category_counts":cats,"category_sum":sum(cats.values()),"per_model_hypodd_rows":per,"ratio_to_official":fp["rows"]/official_n,"structural_checks":checks,"all_structural_checks_pass":all(checks.values()),"findings":[{"severity":"high","issue":"Fold comparison must match the retained manuscript catalog.","evidence":f"6344/632={fp['rows']/official_n:.4f}","remediation":"If 6,344 is retained, report approximately 10 times as many events as the 632-event reference catalog, or omit the fold statement."},{"severity":"medium","issue":"The manuscript release product is in hypoDD.loc format.","remediation":"Describe it as the integrated manuscript catalog/hypoDD-stage integrated catalog, not as a combined hypoDD.reloc catalog."},{"severity":"medium","issue":"Historical category-generation code is incomplete.","remediation":"State that the 15 archived partitions are preserved and exactly reassemble to the 6,344-event final product; do not claim from-scratch regeneration of category assignments."}]}
 text=json.dumps(report,indent=2)+"\n";
 if a.output:
  p=a.output if a.output.is_absolute() else root/a.output;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8",newline="\n");print(f"wrote {p}")
 print(text,end="");return 2 if a.fail_on_structural_error and not report["all_structural_checks_pass"] else 0
if __name__=="__main__":raise SystemExit(main())
