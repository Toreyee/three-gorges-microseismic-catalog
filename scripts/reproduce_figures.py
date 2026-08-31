#!/usr/bin/env python3
"""Reproduce manuscript Figures 2--8 in isolated build directories."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
TARGET_STEMS={2:'Figure2_workflow',3:'Figure3_transfer_learning_performance',4:'Figure4_catalog_reduction_residual_improvement',5:'Figure5_time_distribution_water_level',6:'Figure6_spatial_comparison',7:'Figure7_EQT_magnitude_frequency_distribution',8:'Figure8_model_comparison'}
SOURCE_STEMS={2:'Figure2_workflow',3:'Fig3_transfer_learning_performance_JAG_v2',4:'Fig4_catalog_reduction_residual_improvement',5:'Fig5_time_distribution_water_level_final2',6:'Fig6_manual_vs_final_OSM_publish',7:TARGET_STEMS[7],8:TARGET_STEMS[8]}
def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest().upper()
def run(command:list[str],cwd:Path,env:dict[str,str]|None=None)->None:
 print('+',' '.join(command),f'[cwd={cwd}]');subprocess.run(command,cwd=cwd,env=env,check=True)
def copy_inputs(source:Path,destination:Path)->None:
 if not source.is_dir():return
 for item in source.iterdir():
  target=destination/item.name
  shutil.copytree(item,target,dirs_exist_ok=True) if item.is_dir() else shutil.copy2(item,target)
def to_wsl_path(path:Path,distro:str)->str:
 return subprocess.run(['wsl.exe','-d',distro,'--','wslpath','-a',str(path)],check=True,text=True,capture_output=True).stdout.strip()
def run_figure6(script:Path,work:Path,distro:str)->None:
 if os.name!='nt':
  bash=shutil.which('bash')
  if not bash:raise RuntimeError('bash is required for Figure 6')
  if not shutil.which('gmt'):raise RuntimeError('GMT is required for Figure 6')
  run([bash,str(script)],work);return
 if not shutil.which('wsl.exe'):raise RuntimeError('WSL is required to run GMT Figure 6 on Windows')
 ww=to_wsl_path(work,distro);sw=to_wsl_path(script,distro)
 run(['wsl.exe','-d',distro,'--','bash','-lc','cd "$1" && command -v gmt >/dev/null && bash "$2"','bash',ww,sw],work)
def write_loc_lonlat(catalog:Path,destination:Path)->None:
 with catalog.open('r',encoding='utf-8') as src,destination.open('w',encoding='utf-8',newline='\n') as dst:
  for lineno,line in enumerate(src,1):
   if not line.strip() or line.lstrip().startswith('#'):continue
   fields=line.split()
   if len(fields)!=18:raise ValueError(f'{catalog}:{lineno}: expected 18 fields')
   dst.write(f'{fields[2]} {fields[1]}\n')
def compare_png(generated:Path,reference:Path)->dict:
 try:from PIL import Image,ImageChops
 except ModuleNotFoundError:return {'method':'sha256','exact':sha256(generated)==sha256(reference)}
 with Image.open(generated) as a,Image.open(reference) as b:
  a=a.convert('RGBA');b=b.convert('RGBA')
  if a.size!=b.size:return {'method':'pixels','exact':False,'generated_size':a.size,'reference_size':b.size}
  bbox=ImageChops.difference(a,b).getbbox();return {'method':'pixels','exact':bbox is None,'size':a.size,'difference_bbox':bbox}
def compare_file(generated:Path,reference:Path)->dict:
 result={'reference':reference.name,'reference_exists':reference.is_file(),'generated_sha256':sha256(generated)}
 if not reference.is_file():return result
 result['reference_sha256']=sha256(reference);result['sha256_exact']=result['generated_sha256']==result['reference_sha256']
 if generated.suffix.lower()=='.png':result['image_comparison']=compare_png(generated,reference)
 return result
def locate_output(work:Path,figure:int,extension:str)->Path:
 source=work/f'{SOURCE_STEMS[figure]}.{extension}'
 if not source.is_file():
  c=sorted(work.glob(f'*{figure}*.{extension}'))
  if len(c)==1:source=c[0]
 if not source.is_file():raise FileNotFoundError(f'Figure {figure} did not create {extension}: {work}')
 return source
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--figures',default='2,3,4,5,6,7,8');p.add_argument('--python',default=sys.executable);p.add_argument('--wsl-distro',default='Ubuntu-20.04-New');p.add_argument('--catalog-mode',choices=('manuscript',),default='manuscript',help='use the archived 6,344-event manuscript catalog for Figures 5-6');p.add_argument('--compare-dir',type=Path);p.add_argument('--output-dir',type=Path);p.add_argument('--report',type=Path,default=Path('docs/figure_reproduction_report.json'));p.add_argument('--skip-missing-system',action='store_true');a=p.parse_args()
 root=a.repo_root.resolve();scripts=root/'figures/scripts';data=root/'figures/data';output=(a.output_dir if a.output_dir else root/'figures/output').resolve();compare_dir=a.compare_dir.resolve() if a.compare_dir else None;build=root/'build/figures';output.mkdir(parents=True,exist_ok=True);build.mkdir(parents=True,exist_ok=True)
 requested=[int(x.strip()) for x in a.figures.split(',') if x.strip()];unsupported=sorted(set(requested)-set(TARGET_STEMS));
 if unsupported:p.error(f'unsupported figures: {unsupported}')
 env=os.environ.copy();env['MPLBACKEND']='Agg';env['PYTHONHASHSEED']='0';mode=a.catalog_mode;report={'catalog_mode':mode,'requested':requested,'figures':{}}
 for figure in requested:
  work=(build/f'figure{figure}').resolve()
  if not work.is_relative_to(build.resolve()):raise RuntimeError(f'unsafe build directory: {work}')
  if work.exists():shutil.rmtree(work)
  work.mkdir(parents=True);entry={'status':'running','files':{}};report['figures'][str(figure)]=entry
  try:
   if figure==2:
    dot=shutil.which('dot')
    if not dot:raise RuntimeError('Graphviz dot is required for Figure 2')
    src=scripts/'figure2_workflow.dot';run([dot,'-Tpdf',str(src),'-o',str(work/f'{SOURCE_STEMS[2]}.pdf')],work);run([dot,'-Tpng','-Gdpi=600',str(src),'-o',str(work/f'{SOURCE_STEMS[2]}.png')],work)
   elif figure==3:run([a.python,str(scripts/'figure3_transfer_learning.py')],work,env)
   elif figure==4:run([a.python,str(scripts/'figure4_catalog_reduction.py')],work,env)
   elif figure==5:
    copy_inputs(data/'fig5',work)
    shutil.copy2(root/'data/reference/official_catalog_2018.txt',work/'2018.cat.txt')
    shutil.copy2(root/'data/final/final_catalog_6344.loc.txt',work/'ALL.txt')
    run([a.python,str(scripts/'figure5_time_water_level.py')],work,env)
   elif figure==6:
    copy_inputs(data/'fig6',work)
    write_loc_lonlat(root/'data/final/final_catalog_6344.loc.txt',work/'final_lonlat.txt')
    run_figure6(scripts/'figure6_spatial_map.sh',work,a.wsl_distro)
   elif figure==7:
    copy_inputs(data/'fig7_8',work);run([a.python,str(scripts/'figure7_eqt_fmd.py'),'--event-csv','manual_recalib_eval.strict.csv','--summary-csv','paper_style_mc_strict.summary.csv','--out-prefix',SOURCE_STEMS[7]],work,env)
   elif figure==8:
    copy_inputs(data/'fig7_8',work);run([a.python,str(scripts/'figure8_model_comparison.py'),'--summary-csv','fig7_model_comparison.summary.csv','--out-prefix',SOURCE_STEMS[8]],work,env)
   for ext in ('pdf','png'):
    generated=locate_output(work,figure,ext);target=output/f'{TARGET_STEMS[figure]}.{ext}';fr={'generated_sha256':sha256(generated)}
    if compare_dir is not None:fr['comparison']=compare_file(generated,compare_dir/target.name)
    shutil.copy2(generated,target);fr['output']=(target.relative_to(root).as_posix() if target.is_relative_to(root) else target.as_posix());entry['files'][ext]=fr;print(f'[ok] {target.name} {fr["generated_sha256"]}')
   entry['status']='ok'
  except (RuntimeError,FileNotFoundError) as exc:
   if not a.skip_missing_system:raise
   entry['status']='skipped';entry['reason']=str(exc);print(f'[skip] Figure {figure}: {exc}')
 report['all_requested_reproduced']=all(x['status']=='ok' for x in report['figures'].values());rp=a.report if a.report.is_absolute() else root/a.report;rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(f'wrote {rp}');return 0
if __name__=='__main__':raise SystemExit(main())
