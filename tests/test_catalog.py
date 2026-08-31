from pathlib import Path
import hashlib
import subprocess
import sys
import pandas as pd
from tgr_catalog.catalog import category_models, integrate_model_catalogs, read_hypodd_catalog

def test_category_models():
    assert category_models('ERUL') == ('EQTransformer','RNN','Unet','LPPNL')
    assert category_models('EE') == ('EQTransformer',)
    assert category_models('RL_output') == ('RNN','LPPNL')

def test_loc_time_uses_true_second_column(tmp_path: Path):
    p=tmp_path/'sample.loc';p.write_text('1 31.0 110.0 5.0 0 0 0 0 0 0 2018 1 2 3 4 59.75 -Inf 1\n')
    f=read_hypodd_catalog(p,kind='loc');assert f.loc[0,'timestamp_utc']==pd.Timestamp('2018-01-02 03:04:59.750')

def test_second_overflow_is_normalized(tmp_path: Path):
    p=tmp_path/'overflow.loc';p.write_text('1 31.0 110.0 5.0 0 0 0 0 0 0 2018 1 2 3 4 60.25 -Inf 1\n')
    f=read_hypodd_catalog(p,kind='loc');assert f.loc[0,'timestamp_utc']==pd.Timestamp('2018-01-02 03:05:00.250')

def test_reloc_schema_has_quality_fields(tmp_path: Path):
    p=tmp_path/'sample.reloc';p.write_text('1 31.0 110.0 5.0 0 0 0 10 20 30 2018 1 2 3 4 5.5 -Inf 0 0 4 5 -9.0 0.042 1\n')
    f=read_hypodd_catalog(p,kind='reloc');assert f.loc[0,'rms_ct_s']==0.042 and f.loc[0,'cluster_id']==1

def test_generic_reloc_integration_uses_minimum_rms(tmp_path: Path):
    rows={'EQT':'1 31 110 5 0 0 0 0 0 0 2018 1 1 0 0 1.0 -Inf 0 0 1 1 -9 0.040 1\n','RNN':'2 31 110 5 0 0 0 0 0 0 2018 1 1 0 0 1.5 -Inf 0 0 1 1 -9 0.020 1\n','Unet':'3 31 110 5 0 0 0 0 0 0 2018 1 1 0 0 2.0 -Inf 0 0 1 1 -9 0.030 1\n','lppnl':'4 31 110 5 0 0 0 0 0 0 2018 1 1 0 0 2.5 -Inf 0 0 1 1 -9 0.050 1\n'}
    paths={}
    for m,row in rows.items():
        p=tmp_path/f'{m}.reloc';p.write_text(row);paths[m]=p
    groups=integrate_model_catalogs(paths,threshold_seconds=2.0);assert len(groups['ERUL'])==1 and groups['ERUL'][0].split()[0]=='2'

def test_final_manuscript_catalog_has_6344_rows_and_expected_hash():
    root=Path(__file__).resolve().parents[1]
    p=root/'data/final/final_catalog_6344.loc.txt'
    f=read_hypodd_catalog(p,kind='loc')
    assert len(f)==6344
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='87f4b7105ef56e0cbfedca12b43d3a8ed9ae28fba8d33d36799e58feb971fb12'

def test_archived_category_partitions_sum_to_6344():
    root=Path(__file__).resolve().parents[1]
    files=sorted((root/'data/final/categories').glob('*.txt'))
    assert len(files)==15
    assert sum(len([x for x in p.read_text().splitlines() if x.strip()]) for p in files)==6344

def test_manuscript_catalog_verification_script(tmp_path: Path):
    root=Path(__file__).resolve().parents[1]
    report=tmp_path/'report.json'; out=tmp_path/'out'
    subprocess.run([sys.executable,str(root/'scripts/10_verify_manuscript_catalog.py'),'--repo-root',str(root),'--output-dir',str(out),'--report',str(report)],check=True)
    assert (out/'final_catalog_6344.loc.txt').read_bytes()==(root/'data/final/final_catalog_6344.loc.txt').read_bytes()
