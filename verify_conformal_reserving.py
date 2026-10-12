"""Independent scalar Mack/rank/score audit; optional complete new-DGP replay.

This imports neither conformal_reserving nor the study runner. All 6,144 input
forecasts and 98,304 interval rows are checked, not a selected case subset.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,math,statistics
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/conformal_reserving'
REF=ROOT/'reference/conformal_reserving'
METHODS=['mack_normal','calibrated_normal','conformal_absolute','conformal_scaled']
LEVELS=[80,90,95]
SCENARIOS=['independent_lognormal','independent_gamma','future_calendar_shock','shared_calendar_lognormal']
Z={80:1.2815515655446004,90:1.6448536269514722,95:1.959963984540054}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b):
    assert math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-8),(a,b)

def scalar_mack(c):
    n=len(c);exposure=math.fsum(float(c[i,n-i-1]) for i in range(n))
    for i in range(n):
        for j in range(n):
            assert math.isfinite(float(c[i,j]))==(i+j<n)
    if any(c[i,j]<=0 for i in range(n) for j in range(n-i)):
        return 0.,exposure,exposure,'fallback_failed_mack',None
    factors=[];variances=[];sums=[]
    for k in range(n-1):
        x=[float(c[i,k]) for i in range(n-k-1)]
        z=[float(c[i,k+1]) for i in range(n-k-1)]
        denominator=math.fsum(x);f=math.fsum(z)/denominator
        factors.append(f);sums.append(denominator)
        variances.append(math.fsum(a*(b/a-f)**2 for a,b in zip(x,z))/(len(x)-1) if len(x)>1 else 0.)
    variances[-1]=min(variances[-2]**2/variances[-3],variances[-2],variances[-3]) if variances[-3]>0 else 0.
    projected=[[float(c[i,j]) for j in range(n)] for i in range(n)]
    for i in range(1,n):
        for k in range(n-i-1,n-1):projected[i][k+1]=projected[i][k]*factors[k]
    ultimate=[r[-1] for r in projected]
    point=math.fsum(ultimate)-exposure
    variance=0.
    for i in range(1,n):
        for k in range(n-i-1,n-1):
            variance+=ultimate[i]**2*variances[k]/factors[k]**2*(1/projected[i][k]+1/sums[k])
    for i in range(1,n):
        for j in range(i+1,n):
            for k in range(max(n-i-1,n-j-1),n-1):
                variance+=2*ultimate[i]*ultimate[j]*variances[k]/factors[k]**2/sums[k]
    se=math.sqrt(variance);floor=exposure*1e-12
    return point,max(se,floor),exposure,'scale_floor' if se<floor else 'ok',se

def verify(replay_design=False):
    p=json.loads((REF/'PROTOCOL.json').read_text());r=json.loads((REF/'registration_receipt.json').read_text())
    assert sha(REF/'PROTOCOL.json')==r['protocol_sha256']
    for path,digest in r['frozen_sha256'].items():assert sha(ROOT/path)==digest,path
    for f in json.loads((OUT/'artifact_manifest.json').read_text())['files']:
        assert sha(ROOT/f['path'])==f['sha256'] and (ROOT/f['path']).stat().st_size==f['bytes']
    records=json.loads(gzip.decompress((OUT/'case_records.json.gz').read_bytes()))
    arrays=np.load(OUT/'observed_triangles.npz')
    groups={role:[x for x in records if x['role']==role] for role in ['calibration','evaluation']}
    ids=set();forecast_checks=0;replay_checks=0
    for role,rows in groups.items():
        count=p['calibration_per_scenario'] if role=='calibration' else p['evaluation_per_scenario']
        assert len(rows)==4*count and arrays[role].shape==(len(rows),8,8)
        for index,row in enumerate(rows):
            key=tuple(row['seed']);assert key not in ids;ids.add(key)
            s=SCENARIOS.index(row['scenario'])
            assert row['seed']==[p['seed_root'],p['seed_namespace'],1 if role=='calibration' else 2,s,row['replicate'],0]
            c=arrays[role][index];assert hashlib.sha256(c.tobytes()).hexdigest()==row['observed_sha256']
            point,scale,exposure,status,se=scalar_mack(c)
            for a,b in [(point,row['point']),(scale,row['scale']),(exposure,row['exposure'])]:close(a,b)
            assert status==row['status']
            if se is None:assert row['raw_std_error'] is None
            else:close(se,row['raw_std_error'])
            if replay_design:
                # The source generator alone is reused. It is never given a
                # fitted interval, and none of the old 1,024 study seeds run.
                from src.predictive_reserving import complete_simulation
                fresh,actual=complete_simulation(row['scenario'],row['seed'])
                assert np.allclose(c,fresh,rtol=1e-9,atol=1e-8,equal_nan=True)
                close(row['actual'],actual);replay_checks+=1
            forecast_checks+=1
    models=json.loads((OUT/'calibration_models.json').read_text())
    for scenario in SCENARIOS:
        cal=[x for x in groups['calibration'] if x['scenario']==scenario]
        z=[(x['actual']-x['point'])/x['scale'] for x in cal]
        model=models[scenario];assert model['n']==len(cal)
        close(model['scaled_bias'],statistics.mean(z));close(model['scaled_std'],statistics.stdev(z))
        assert model['fallback_calibration_cases']==sum(x['status']=='fallback_failed_mack' for x in cal)
        for level in LEVELS:
            k=((len(cal)+1)*level+99)//100;assert model['ranks'][str(level)]==k
            close(model['absolute'][str(level)],sorted(abs(x['actual']-x['point']) for x in cal)[k-1])
            close(model['scaled'][str(level)],sorted(abs(v) for v in z)[k-1])
    intervals=np.load(OUT/'intervals.npz');summary=json.loads((OUT/'SUMMARY.json').read_text())
    assert summary['distinct_new_triangles']==6144 and summary['calibration_triangles']==2048 and summary['evaluation_triangles']==4096
    assert summary['model_frozen_before_evaluation'] is True
    assert sha(OUT/'calibration_models.json')==summary['calibration_models_sha256']
    assert summary['registration_commit']==r['commit']
    assert summary['calibration_failures']==sum(x['status']=='fallback_failed_mack' for x in groups['calibration'])
    assert summary['evaluation_failures']==sum(x['status']=='fallback_failed_mack' for x in groups['evaluation'])
    assert summary['scale_floor_cases']==sum(x['status']=='scale_floor' for x in records)
    interval_checks=0
    for s,scenario in enumerate(SCENARIOS):
        rows=[x for x in groups['evaluation'] if x['scenario']==scenario]
        cal=[x for x in groups['calibration'] if x['scenario']==scenario]
        quartiles=np.quantile([x['exposure'] for x in cal],[.25,.5,.75])
        for mode,calibration_scenario in enumerate([scenario,'independent_lognormal']):
            model=models[calibration_scenario]
            for m,method in enumerate(METHODS):
                for l,level in enumerate(LEVELS):
                    count=failed=unbounded=0;finite_width=[];finite_loss=[];covered_flags=[]
                    for i,row in enumerate(rows):
                        if row['status']=='fallback_failed_mack':
                            lo=hi=math.nan if method=='mack_normal' else math.inf
                            if method!='mack_normal':lo=-math.inf
                            status=1 if method=='mack_normal' else 2
                        else:
                            center=row['point']
                            if method=='mack_normal':radius=Z[level]*row['raw_std_error']
                            elif method=='calibrated_normal':
                                center+=model['scaled_bias']*row['scale'];radius=Z[level]*model['scaled_std']*row['scale']
                            else:radius=model['absolute'][str(level)] if method=='conformal_absolute' else model['scaled'][str(level)]*row['scale']
                            lo,hi=center-radius,center+radius;status=0
                        a=intervals['lower'][s,mode,m,l,i];b=intervals['upper'][s,mode,m,l,i]
                        assert int(intervals['status_code'][s,mode,m,l,i])==status
                        if status==1:assert math.isnan(a) and math.isnan(b);failed+=1;covered=False
                        elif status==2:assert a==-math.inf and b==math.inf;unbounded+=1;covered=True
                        else:
                            close(a,lo);close(b,hi);covered=a<=row['actual']<=b
                            finite_width.append((b-a)/row['exposure'])
                            alpha=(100-level)/100
                            finite_loss.append((b-a+(2/alpha)*(max(a-row['actual'],0)+max(row['actual']-b,0)))/row['exposure'])
                        count+=covered;covered_flags.append(covered);interval_checks+=1
                    mode_name='matched_distribution' if mode==0 else 'independent_lognormal_calibration'
                    result=next(x for x in summary['results'] if x['scenario']==scenario and x['mode']==mode_name and x['method']==method and x['level']==level)
                    assert result['cases']==len(rows) and result['covered']==count and result['failed']==failed and result['unbounded']==unbounded
                    close(result['coverage'],count/len(rows));assert result['finite_intervals']==len(finite_width)
                    close(result['mean_finite_width_scaled'],statistics.mean(finite_width));close(result['mean_finite_interval_score_scaled'],statistics.mean(finite_loss))
                    z=Z[95];phat=count/len(rows);den=1+z*z/len(rows)
                    midpoint=(phat+z*z/(2*len(rows)))/den;half=z*math.sqrt(phat*(1-phat)/len(rows)+z*z/(4*len(rows)**2))/den
                    close(result['wilson95'][0],midpoint-half);close(result['wilson95'][1],midpoint+half)
                    strata=json.loads((OUT/'exposure_strata.json').read_text())
                    for q in range(4):
                        ids_q=[i for i,row in enumerate(rows) if np.searchsorted(quartiles,row['exposure'],side='right')==q]
                        item=next(x for x in strata if x['scenario']==scenario and x['mode']==mode_name and x['method']==method and x['level']==level and x['exposure_quartile']==q+1)
                        assert item['cases']==len(ids_q) and item['covered']==sum(covered_flags[i] for i in ids_q)
    assert interval_checks==summary['interval_method_rows']==98304
    return {'independent_scalar_forecasts':forecast_checks,'independent_interval_rows':interval_checks,
        'independent_rank_mean_std_and_summary_checks':True,'full_new_design_replays':replay_checks,
        'old_1024_study_seeds_rerun':0,'scope':'Automated internal oracle; not external practitioner review.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--replay-design',action='store_true');args=ap.parse_args()
    print(json.dumps(verify(args.replay_design),indent=2))
