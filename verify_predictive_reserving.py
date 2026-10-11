"""Audit every registered artifact, score and design; replay fixed case IDs."""
from pathlib import Path
import json
import tempfile
import numpy as np
import pandas as pd
from benchmark_predictive_reserving import public_work
from src.predictive_reserving import (ROOT,PROBS,SCENARIOS,METHODS,protocol_guard,sha,
    calibration_case,calibration_summary,complete_simulation,score_row)


def equal(a,b,path=''):
    if isinstance(a,dict):
        assert set(a)==set(b),path
        for k in a: equal(a[k],b[k],path+'/'+str(k))
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)): equal(x,y,path+'/'+str(i))
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        np.testing.assert_allclose(a,b,rtol=2e-10,atol=2e-8,err_msg=path)
    else:
        assert a==b,(path,a,b)


def frame_equal(a,b):
    assert list(a.columns)==list(b.columns)
    assert a.shape==b.shape
    for col in a:
        if pd.api.types.is_numeric_dtype(a[col]):
            np.testing.assert_allclose(a[col],b[col],rtol=2e-10,atol=2e-8,equal_nan=True,err_msg=col)
        else:
            assert a[col].fillna('').astype(str).tolist()==b[col].fillna('').astype(str).tolist(),col


def main():
    p=protocol_guard();out=ROOT/'outputs/predictive_reserving'
    manifest=json.loads((out/'artifact_manifest.json').read_text())
    for item in manifest['files']:
        path=ROOT/item['path']
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],item['path']
    with tempfile.TemporaryDirectory() as d:
        fresh=Path(d);public_work(p,fresh)
        for path in fresh.iterdir():
            saved=out/path.name
            if path.suffix=='.json': equal(json.loads(path.read_text()),json.loads(saved.read_text()),path.name)
            elif path.suffix=='.csv': frame_equal(pd.read_csv(path,float_precision='round_trip'),pd.read_csv(saved,float_precision='round_trip'))
            elif path.suffix=='.npz':
                with np.load(path) as a,np.load(saved) as b:
                    assert set(a.files)==set(b.files)
                    for k in a.files: np.testing.assert_allclose(a[k],b[k],rtol=2e-10,atol=2e-8,err_msg=k)
    public=pd.read_csv(out/'public_diagonal_predictions.csv',float_precision='round_trip')
    old=pd.read_csv(ROOT/'outputs/stochastic_reserving/diagonal_backtest.csv',float_precision='round_trip')
    now=public[(public.dataset=='raa') & (public.scope=='cell') & (public.method=='mack_normal')]
    assert len(now)==len(old)==22
    for r in old.itertuples():
        new=now[(now.valuation==r.valuation_year)&(now.origin==r.origin)].iloc[0]
        np.testing.assert_allclose([new.actual,new.chain_ladder,new.no_development],
            [r.actual_next,r.chain_ladder_next,r.no_development_next],rtol=2e-10,atol=2e-8)
    df=pd.read_csv(out/'calibration_cases.csv',float_precision='round_trip').fillna({'error':''})
    expected={(s,r,m) for s in SCENARIOS for r in range(p['calibration_cases_per_scenario']) for m in METHODS}
    actual=set(zip(df.scenario,df.replicate,df.method))
    assert len(df)==len(expected) and actual==expected
    for row in df[df.status=='ok'].to_dict('records'):
        q=[row[k] for k in ['q025','q10','median','q90','q95','q975','q995']]
        scored=score_row(row['actual'],q,row['scale'])
        equal(scored,{k:row[k] for k in scored},'stored score')
    equal(calibration_summary(df),json.loads((out/'calibration_summary.json').read_text()),'calibration summary')
    with np.load(out/'calibration_designs.npz') as designs:
        assert designs['observed'].shape==(4*p['calibration_cases_per_scenario'],8,8)
        for s,case in enumerate(SCENARIOS):
            for r in range(p['calibration_cases_per_scenario']):
                c,y=complete_simulation(case,[20261011,s,r,0]);index=s*p['calibration_cases_per_scenario']+r
                np.testing.assert_allclose(c,designs['observed'][index],rtol=2e-10,atol=2e-8,equal_nan=True)
                np.testing.assert_allclose(y,designs['actual_reserve'][index],rtol=2e-10,atol=2e-8)
                selected=df[(df.scenario==case)&(df.replicate==r)]
                np.testing.assert_allclose(selected.actual,y,rtol=2e-10,atol=2e-8)
    replayed=0; differing_hashes=0
    for s,case in enumerate(SCENARIOS):
        for r in p['replay_replicates']:
            fresh=calibration_case(s,r,p['calibration_draws'])
            saved=df[(df.scenario==case)&(df.replicate==r)].set_index('method')
            for row in fresh:
                b=saved.loc[row['method']].to_dict();b['method']=row['method']
                for k,v in row.items():
                    if k=='training_array_sha256': differing_hashes += int(v!=b[k]);continue
                    equal(v,b[k],case+'/'+str(r)+'/'+row['method']+'/'+k)
            replayed+=1
    print('PREDICTIVE_REFERENCE_JSON='+json.dumps(dict(status='passed',manifest_files=len(manifest['files']),
        public_measures=6,public_modes_replayed=True,original_22_raa_cells_reconciled=True,
        all_stored_scores_recomputed=True,all_1024_simulation_designs_replayed=True,
        original_study_cases=1024,predictive_case_replays=replayed,replay_replicates=p['replay_replicates'],
        differing_training_byte_hashes=differing_hashes,numerical_rtol=2e-10,numerical_atol=2e-8,
        scope='Full original simulation ran 1024 cases; CI refits 16 fixed cases, not all 1024. No bit-identical hardware portability claim.')))


if __name__=='__main__': main()
