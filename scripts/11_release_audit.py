#!/usr/bin/env python3
"""Audit a repository tree for common GitHub release blockers."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
CACHE_DIRS={'__pycache__','.pytest_cache','.ipynb_checkpoints','.mypy_cache','.ruff_cache','.tox','.nox'}; CACHE_SUFFIXES={'.pyc','.pyo'}
TEXT_SUFFIXES={'.py','.pl','.sh','.md','.txt','.yml','.yaml','.toml','.cff','.dot','.gmt','.csv','.json'}
SECRET_PATTERNS={'private_key':re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),'github_token':re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),'generic_secret_assignment':re.compile(r'(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*[\'\"][^\'\"]{6,}[\'\"]')}
MACHINE_PATH_PATTERNS={'linux_home':re.compile(r'/(?:home|Users)/(?:tao|li|wangwt)(?:/|\\)'),'mnt_drive':re.compile(r'/mnt/[a-zA-Z]/'),'windows_drive':re.compile(r'\b[A-Z]:\\')}
def read_text(path:Path)->str|None:
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'Makefile','.gitignore','.gitattributes','LICENSE','NOTICE'}: return None
    try:return path.read_text(encoding='utf-8',errors='replace')
    except OSError:return None
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,default=Path('docs/release_audit.json'));p.add_argument('--github-limit-mb',type=float,default=100.0);a=p.parse_args();root=a.repo_root.resolve()
    caches=[];large=[];secrets=[];machine=[];files=[]
    for path in root.rglob('*'):
        rel=path.relative_to(root)
        if '.git' in rel.parts:continue
        if path.is_dir():
            if path.name in CACHE_DIRS or path.name.endswith('.egg-info'):caches.append(rel.as_posix())
            continue
        if not path.is_file():continue
        files.append(path)
        if path.suffix.lower() in CACHE_SUFFIXES:caches.append(rel.as_posix())
        if path.stat().st_size>=a.github_limit_mb*1024*1024:large.append({'path':rel.as_posix(),'bytes':path.stat().st_size})
        text=read_text(path)
        if text is None:continue
        for label,pat in SECRET_PATTERNS.items():
            for m in pat.finditer(text):secrets.append({'path':rel.as_posix(),'line':text.count('\n',0,m.start())+1,'pattern':label})
        for label,pat in MACHINE_PATH_PATTERNS.items():
            for m in pat.finditer(text):
                allowed=rel.parts[0] in {'docs','third_party'} or rel.name=='README.md';machine.append({'path':rel.as_posix(),'line':text.count('\n',0,m.start())+1,'pattern':label,'allowed_context':allowed})
    blocking=[x for x in machine if not x['allowed_context']]
    report={'file_count':len(files),'cache_artifacts':sorted(caches),'github_oversize_files':large,'secret_pattern_hits':secrets,'machine_path_hits':machine,'blocking_machine_path_hits':blocking,'all_blocking_checks_pass':not caches and not large and not secrets and not blocking,'notes':['Comments in the pinned third_party snapshot may contain upstream machine paths and are recorded but not treated as project blockers.','This is a pattern-based audit, not a substitute for repository-owner review or a dedicated secret scanner before publication.']}
    out=a.output if a.output.is_absolute() else root/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,indent=2));return 0 if report['all_blocking_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
