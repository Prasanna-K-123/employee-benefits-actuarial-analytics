"""Execute the fixed registered study; refuse overwrite of completed output."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import argparse
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import scipy
from src.predictive_reserving import (ROOT,STUDY,PROBS,SCENARIOS,protocol_guard,
    parts,load_public,shared_projection,sample_summary,moment_quantiles,
    public_diagonals,calendar_diagnostics,calibration_case,calibration_summary,complete_simulation,
    json_write,sha)


def task(args):
    return calibration_case(*args)


def public_work(p, out):
    reserve,diagonals,residuals,tails = {},[],[],[]
    samples = {}
    for index, spec in enumerate(p['public_measures']):
        name=spec['id']; c,years=load_public(ROOT/spec['path'],spec['measure'])
        fit=parts(c); point=float(fit['ibnr'].sum()); se=fit['total_std_error']
        modes={}
        for family in ['lognormal','gamma']:
            d=shared_projection(c,p['public_draws'],[20261011,index,10 if family=='lognormal' else 11],family)
            po=shared_projection(c,p['public_draws'],[20261011,index,20 if family=='lognormal' else 21],family,True)
            for mode,values in [('combined',d['reserve']),('parameter_only',d['parameter_reserve']),('process_only',po['reserve'])]:
                modes[family+'_'+mode]=sample_summary(values)
                samples[name+'__'+family+'_'+mode]=values
            modes[family+'_law_total_variance']={k:v for k,v in d.items() if not isinstance(v,np.ndarray)}
            modes[family+'_process_only_numerical']={'final_zero_origin_draws':po['final_zero_origin_draws']}
        for family in ['normal','lognormal']:
            if family=='lognormal' and point<=0:
                modes['mack_'+family]={'status':'unavailable','reason':'nonpositive aggregate reserve mean'}
            else:
                q=moment_quantiles(point,se*se,family)
                modes['mack_'+family]={'mean':point,'std':se,'quantiles':{str(a):float(b) for a,b in zip(PROBS,q)}}
        negative_inc=sum(int(np.sum(np.diff(c[i,:len(c)-i])<0)) for i in range(len(c)))
        reserve[name]=dict(source_path=spec['path'],measure=spec['measure'],source_sha256=sha(ROOT/spec['path']),
            years=years,observed_cells=int(np.isfinite(c).sum()),negative_observed_increments=negative_inc,
            ibnr=point,mack_std_error=se,mack_process_variance=float(fit['process_variance'].sum()),
            mack_parameter_variance=float(fit['parameter_variance'].sum()+fit['aggregate_parameter_covariance']),
            mack_shared_parameter_covariance=fit['aggregate_parameter_covariance'],modes=modes)
        d=public_diagonals(c,years);d.insert(0,'dataset',name);diagonals.append(d)
        r=calendar_diagnostics(c,years);r.insert(0,'dataset',name);residuals.append(r)
        for t in p['tail_factors']:
            tails.append(dict(dataset=name,tail_factor=t,ibnr=float(t*fit['ultimate'].sum()-fit['latest'].sum()),
                additional_reserve=float((t-1)*fit['ultimate'].sum()),scaled_mack_std_error=t*se,
                additional_tail_uncertainty_estimated=False))
        print('PUBLIC_COMPLETE '+name,flush=True)
    diagonal=pd.concat(diagonals,ignore_index=True)
    resids=pd.concat(residuals,ignore_index=True)
    diagonal.to_csv(out/'public_diagonal_predictions.csv',index=False,float_format='%.17g')
    resids.to_csv(out/'calendar_residuals.csv',index=False,float_format='%.17g')
    pd.DataFrame(tails).to_csv(out/'tail_sensitivity.csv',index=False,float_format='%.17g')
    json_write(out/'public_reserve_summary.json',reserve)
    np.savez_compressed(out/'public_samples.npz',**samples)
    summaries=[]
    for (dataset,scope,method),g in diagonal.groupby(['dataset','scope','method'],sort=True):
        summaries.append(dict(dataset=dataset,scope=scope,method=method,observations=len(g),
            chain_ladder_mae=float(abs(g.chain_ladder-g.actual).mean()),
            no_development_mae=float(abs(g.no_development-g.actual).mean()),
            covered80=int(g.cover80.sum()),covered95=int(g.cover95.sum()),
            upper95_exceeded=int(g.upper95_exceeded.sum()),
            mean_width80_scaled=float(g.width80_scaled.mean()),mean_width95_scaled=float(g.width95_scaled.mean()),
            mean_score80_scaled=float(g.score80_scaled.mean()),mean_score95_scaled=float(g.score95_scaled.mean())))
    pd.DataFrame(summaries).to_csv(out/'public_diagonal_summary.csv',index=False,float_format='%.17g')
    calendar=(resids.groupby(['dataset','calendar'],sort=True).residual.agg(['size','mean','std']).reset_index())
    calendar.to_csv(out/'calendar_summary.csv',index=False,float_format='%.17g')
    return reserve,summaries


def run(out, workers=4):
    p=protocol_guard()
    out=Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Refuse to replace completed study output')
    out.mkdir(parents=True,exist_ok=True)
    receipt=json.loads((STUDY/'source_receipt.json').read_text())
    for item in receipt['files']:
        if sha(ROOT/item['path'])!=item['sha256']:
            raise ValueError('Registered collected source changed')
    reserve,public_summary=public_work(p,out)
    tasks=[(s,r,p['calibration_draws']) for s in range(len(SCENARIOS)) for r in range(p['calibration_cases_per_scenario'])]
    rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for index, batch in enumerate(pool.map(task,tasks,chunksize=4)):
            rows.extend(batch)
            if (index+1)%64==0:
                print('CALIBRATION_COMPLETE '+str(index+1)+'/'+str(len(tasks)),flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/'calibration_cases.csv',index=False,float_format='%.17g')
    designs=[complete_simulation(SCENARIOS[s],[20261011,s,r,0]) for s,r,_ in tasks]
    np.savez_compressed(out/'calibration_designs.npz',observed=np.array([x[0] for x in designs]),
                        actual_reserve=np.array([x[1] for x in designs]))
    cal=calibration_summary(df)
    json_write(out/'calibration_summary.json',cal)
    env=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,
             platform=platform.platform(),workers=workers)
    json_write(out/'environment.json',env)
    summary=dict(protocol_sha256=sha(STUDY/'PROTOCOL.json'),public_measures=len(reserve),
        public_sources=5,public_draws_per_mode=p['public_draws'],
        public_eligible_cell_predictions=sum(x['observations'] for x in public_summary if x['scope']=='cell' and x['method']=='mack_normal'),
        public_eligible_diagonals=sum(x['observations'] for x in public_summary if x['scope']=='eligible_diagonal' and x['method']=='mack_normal'),
        independent_simulated_cases=len(tasks),cases_per_scenario=p['calibration_cases_per_scenario'],
        predictive_draws_per_simulation_method=p['calibration_draws'],calibration_method_rows=len(df),
        failed_calibration_methods=int((df.status!='ok').sum()),
        interpretation='Public later-diagonals are retrospective, dependent diagnostics. Synthetic coverage is conditional on four fixed simulation designs. Shared-factor moment simulation is not a validated bootstrap, posterior or regulatory capital model.',
        unestimated=['dispersion-parameter uncertainty','cross-age factor dependence','empirical-tail uncertainty',
                     'unobserved exposure/claim mix changes','calendar dependence unless explicitly stressed',
                     'new insurer/time validation','client pension/health liability calibration'])
    json_write(out/'summary.json',summary)
    files=[ROOT/'src/predictive_reserving.py',ROOT/'benchmark_predictive_reserving.py',ROOT/'collect_predictive_sources.py',
           ROOT/'verify_predictive_reserving.py',ROOT/'tests/test_predictive_reserving.py',ROOT/'requirements-predictive.txt',
           ROOT/'.github/workflows/predictive-reserving.yml',STUDY/'PROTOCOL.json',STUDY/'registration_receipt.json',STUDY/'source_receipt.json']
    files += [ROOT/x['path'] for x in receipt['files']]
    files += sorted(x for x in out.iterdir() if x.is_file())
    json_write(out/'artifact_manifest.json',dict(files=[dict(path=str(x.relative_to(ROOT)),bytes=x.stat().st_size,sha256=sha(x)) for x in files]))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(ROOT/'outputs/predictive_reserving'))
    ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    if not 1<=args.workers<=4: raise ValueError('Workers must be 1..4')
    run(args.output,args.workers)
