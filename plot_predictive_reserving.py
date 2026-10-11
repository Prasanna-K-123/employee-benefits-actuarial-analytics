"""Render the completed tables; no estimation or method selection here."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/predictive_reserving'
data=pd.read_csv(OUT/'public_diagonal_summary.csv')
cal=json.loads((OUT/'calibration_summary.json').read_text())
fig,(a,b)=plt.subplots(2,1,figsize=(11,9),layout='constrained')
colors=['#17334d','#297b8c','#b15d32','#7966a1']
labels=['RAA','GenIns','ABC','UK motor','USAA paid','USAA incurred']
ids=['raa','genins','abc','ukmotor','usaa_paid','usaa_incurred']
for j,(method,label) in enumerate([('mack_normal','Normal moment'),('mack_lognormal','Lognormal moment')]):
 y=[];text=[]
 for name in ids:
  row=data[(data.dataset==name)&(data.scope=='cell')&(data.method==method)].iloc[0]
  y.append(100*row.covered95/row.observations);text.append(f'{int(row.covered95)}/{int(row.observations)}')
 x=np.arange(len(ids))+(j-.5)*.12
 a.scatter(x,y,color=colors[j],label=label,s=50,marker='o' if j==0 else 's')
 for xx,yy,t in zip(x,y,text):a.annotate(t,(xx,yy),xytext=(0,9 if j==0 else -16),textcoords='offset points',ha='center',fontsize=9,color=colors[j])
a.axhline(95,color='#737c85',ls='--',lw=1,label='Nominal 95%')
a.set_xticks(np.arange(len(ids)),labels);a.set_ylim(15,110);a.set_ylabel('Observed coverage (%)')
a.set_title('Public benchmarks: retrospective later-diagonal diagnostics',loc='left',weight='bold',fontsize=12)
a.text(.01,.03,'123 cells across six measures; dependent folds. Two USAA measures share one source.\nCounts are descriptive; observed final-reserve coverage is unavailable.',transform=a.transAxes,fontsize=9,color='#4b5966')
a.legend(loc='upper right',ncols=3,fontsize=9)
scenarios=['independent_lognormal','independent_gamma','future_calendar_shock','shared_calendar_lognormal']
short=['Independent\nlognormal','Independent\ngamma','Future 10%\ncalendar shock','Shared calendar\nlognormal (rho=0.35)']
for j,(method,label) in enumerate([('mack_normal','Mack normal'),('mack_lognormal','Mack lognormal'),('shared_lognormal','Shared-factor lognormal'),('shared_gamma','Shared-factor gamma')]):
 rows=[next(r for r in cal if r['scenario']==s and r['method']==method) for s in scenarios]
 y=np.array([100*r['coverage95'] for r in rows]);lo=np.array([100*r['wilson95'][0] for r in rows]);hi=np.array([100*r['wilson95'][1] for r in rows])
 x=np.arange(4)+(j-1.5)*.10
 b.errorbar(x,y,yerr=[y-lo,hi-y],fmt='o',capsize=3,color=colors[j],label=label,ms=5,lw=1)
b.axhline(95,color='#737c85',ls='--',lw=1)
b.set_xticks(np.arange(4),short);b.set_ylim(70,101);b.set_ylabel('95% interval coverage (%)')
b.set_title('Known-future simulation: calibration and assumption stress',loc='left',weight='bold',fontsize=12)
b.legend(loc='lower left',ncols=2,fontsize=9)
for ax in [a,b]:
 ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('Reserving uncertainty: precise replication does not ensure calibration',fontsize=14,weight='bold')
fig.text(.01,-.025,'256 independent cases per design; Wilson 95% Monte Carlo brackets. One gamma training case failed all four methods\nand remains uncovered in the denominator. Fixed designs and heuristic moments; no regulatory-capital or client claim.',fontsize=9,color='#4b5966')
fig.savefig(OUT/'predictive_coverage.png',dpi=170,bbox_inches='tight')
plt.close(fig)
print(OUT/'predictive_coverage.png')
