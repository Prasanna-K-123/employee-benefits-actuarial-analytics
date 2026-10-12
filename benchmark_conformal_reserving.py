"""New registered cases only; refuse to overwrite a completed study."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,platform,time
import numpy as np
import scipy
from src.predictive_reserving import complete_simulation,SCENARIOS,wilson
from src.conformal_reserving import forecast,fit_calibration,interval,score,METHODS,LEVELS

ROOT=Path(__file__).resolve().parent
REF=ROOT/'reference/conformal_reserving'
OUT=ROOT/'outputs/conformal_reserving'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def guard():
    p=json.loads((REF/'PROTOCOL.json').read_text());r=json.loads((REF/'registration_receipt.json').read_text())
    assert sha(REF/'PROTOCOL.json')==r['protocol_sha256'],'Protocol changed'
    for path,digest in r['frozen_sha256'].items():assert sha(ROOT/path)==digest,path
    return p

def make_cases(p,role,count):
    records=[];arrays=[]
    for s,scenario in enumerate(SCENARIOS):
        for i in range(count):
            seed=[p['seed_root'],p['seed_namespace'],1 if role=='calibration' else 2,s,i,0]
            observed,actual=complete_simulation(scenario,seed)
            f=forecast(observed)
            records.append(dict(role=role,scenario=scenario,replicate=i,seed=seed,actual=actual,
                point=f.point,scale=f.scale,raw_std_error=f.raw_std_error,exposure=f.exposure,status=f.status,
                observed_sha256=hashlib.sha256(observed.tobytes()).hexdigest()))
            arrays.append(observed)
        print(role.upper()+'_SCENARIO_COMPLETE '+scenario,flush=True)
    return records,np.asarray(arrays)

def as_forecast(r):
    from src.conformal_reserving import Forecast
    return Forecast(r['point'],r['scale'],r['exposure'],r['status'],r['raw_std_error'])

def run(out):
    p=guard();out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Refuse completed or partial output overwrite')
    out.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    cal,cal_arrays=make_cases(p,'calibration',p['calibration_per_scenario'])
    models={}
    for scenario in SCENARIOS:
        rows=[r for r in cal if r['scenario']==scenario]
        models[scenario]=fit_calibration([as_forecast(r) for r in rows],[r['actual'] for r in rows])
    write_json(out/'calibration_models.json',models)
    models_hash=sha(out/'calibration_models.json')
    print('CALIBRATION_MODELS_FROZEN '+models_hash,flush=True)
    evaluation,eval_arrays=make_cases(p,'evaluation',p['evaluation_per_scenario'])
    assert sha(out/'calibration_models.json')==models_hash
    (out/'case_records.json.gz').write_bytes(gzip.compress(json.dumps(cal+evaluation,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    np.savez_compressed(out/'observed_triangles.npz',calibration=cal_arrays,evaluation=eval_arrays)
    shape=(len(SCENARIOS),2,len(METHODS),len(LEVELS),p['evaluation_per_scenario'])
    lower=np.empty(shape);upper=np.empty(shape);status_code=np.empty(shape,dtype=np.uint8)
    summaries=[];strata=[]
    for s,scenario in enumerate(SCENARIOS):
        rows=[r for r in evaluation if r['scenario']==scenario]
        calrows=[r for r in cal if r['scenario']==scenario]
        quartiles=np.quantile([r['exposure'] for r in calrows],[.25,.5,.75])
        for mode,calibration_scenario in enumerate([scenario,'independent_lognormal']):
            model=models[calibration_scenario]
            mode_name='matched_distribution' if mode==0 else 'independent_lognormal_calibration'
            for m,method in enumerate(METHODS):
                for l,level in enumerate(LEVELS):
                    scores=[]
                    for i,r in enumerate(rows):
                        lo,hi,status=interval(as_forecast(r),model,method,level)
                        lower[s,mode,m,l,i]=lo;upper[s,mode,m,l,i]=hi
                        status_code[s,mode,m,l,i]=0 if status=='ok' else 1 if status=='failed' else 2
                        scores.append(score(r['actual'],lo,hi,status,r['exposure'],level))
                    covered=sum(x['covered'] for x in scores);finite=[x for x in scores if x['finite']]
                    key=dict(scenario=scenario,calibration_scenario=calibration_scenario,mode=mode_name,method=method,level=level)
                    summaries.append(dict(**key,cases=len(rows),covered=covered,coverage=covered/len(rows),
                        wilson95=wilson(covered,len(rows)),failed=sum(x['failed'] for x in scores),
                        unbounded=sum(not x['finite'] and not x['failed'] for x in scores),
                        finite_intervals=len(finite),mean_finite_width_scaled=float(np.mean([x['width'] for x in finite])) if finite else None,
                        mean_finite_interval_score_scaled=float(np.mean([x['interval_score'] for x in finite])) if finite else None,
                        mean_all_width_is_infinite=len(finite)!=len(rows),mean_all_score_is_infinite=len(finite)!=len(rows)))
                    for q in range(4):
                        ids=[i for i,r in enumerate(rows) if int(np.searchsorted(quartiles,r['exposure'],side='right'))==q]
                        strata.append(dict(**key,exposure_quartile=q+1,cases=len(ids),covered=sum(scores[i]['covered'] for i in ids),
                            coverage=sum(scores[i]['covered'] for i in ids)/len(ids) if ids else None,
                            quartile_cutoffs_from_calibration=quartiles.tolist(),claim='Diagnostic only; no conditional/group-coverage guarantee'))
        print('ALL_INTERVALS_COMPLETE '+scenario,flush=True)
    np.savez_compressed(out/'intervals.npz',lower=lower,upper=upper,status_code=status_code)
    write_json(out/'exposure_strata.json',strata)
    summary=dict(study=p['study'],protocol_sha256=sha(REF/'PROTOCOL.json'),
        registration_commit=json.loads((REF/'registration_receipt.json').read_text())['commit'],
        distinct_new_triangles=len(cal)+len(evaluation),calibration_triangles=len(cal),evaluation_triangles=len(evaluation),
        interval_method_rows=int(np.prod(shape)),methods=list(METHODS),levels=list(LEVELS),
        model_frozen_before_evaluation=True,calibration_models_sha256=models_hash,
        calibration_failures=sum(r['status']=='fallback_failed_mack' for r in cal),
        evaluation_failures=sum(r['status']=='fallback_failed_mack' for r in evaluation),
        scale_floor_cases=sum(r['status']=='scale_floor' for r in cal+evaluation),
        rank_lower_bounds={str(l):models[SCENARIOS[0]]['ranks'][str(l)]/(p['calibration_per_scenario']+1) for l in LEVELS},
        results=summaries,environment={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        wall_seconds=time.perf_counter()-start,
        scope='Fresh draws from four previously inspected fixed synthetic laws. Whole triangles are independent within a matching law. Marginal conformal guarantee requires exchangeable calibration/test pairs, not a fixed-batch or real insurer coverage certificate. Shift and exposure-stratum failures retained; no public triangle rescore, client valuation, capital calibration, external review, adoption or mastery claim.')
    write_json(out/'SUMMARY.json',summary)
    write_json(out/'artifact_manifest.json',{'files':[{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(out.iterdir()) if x.is_file()]})
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));args=ap.parse_args();run(args.output)
