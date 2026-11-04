#!/usr/bin/env python3
"""Compare authentic newly run UCI outputs with numbers printed in ExplAI-2026 Paper 14.

This is a CONFLICT DETECTOR, not a selection/tuning procedure. Rebuilding from
public UCI with assumed hyperparameters does not reproduce historical provenance.
The recorded historical numbers below are transcribed from the anonymous manuscript.
"""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from sklearn.metrics import f1_score

ORIGINAL=[
 ('DryBean','HGB',.9190,.9286,.9535,-.474, .333,.0149,.234),
 ('DryBean','LR',.9198,.9264,.9756,-.554,.333,.0142,.149),
 ('DryBean','RF',.9212,.9284,.9609,-.074,.333,.0180,.223),
 ('Rice','HGB',.9130,.9187,.9567,-.589,.267,.0079,.203),
 ('Rice','LR',.9270,.9268,.9856,+.097,.667,.0065,.081),
 ('Rice','RF',.9211,.9243,.9806,-.406,.333,.0055,.139),
]
# B0, B1 mean values rounded to 5 decimals in printed Table 7.
BLOCK_ORIGINAL={
 ('DryBean','HGB','Area'):(.00500,.04505),('DryBean','HGB','ConvexArea'):(.00280,.03427),
 ('DryBean','LR','Area'):(.00052,.03750),('DryBean','LR','ConvexArea'):(.00071,.03328),
 ('DryBean','RF','Area'):(.00890,.05919),('DryBean','RF','ConvexArea'):(.00832,.04826),
 ('Rice','HGB','Area'):(.00703,.02779),('Rice','HGB','ConvexArea'):(.00728,.02284),
 ('Rice','LR','Area'):(.00054,.01454),('Rice','LR','ConvexArea'):(.00294,.01754),
 ('Rice','RF','Area'):(.00538,.02119),('Rice','RF','ConvexArea'):(.00563,.01459),
}

def run(path,out):
    scores=pd.read_csv(path/'fold_scores.csv'); ccpi=pd.read_csv(path/'fold_ccpi.csv'); oof=pd.read_csv(path/'oof_probabilities.csv')
    rows=[];blockrows=[]
    from reanalyse_from_logs import report_fold,report_oof
    tbl5=report_fold(ccpi)['Table5_descriptive_with_null.csv']
    tbl4=report_oof(oof)['Table4_original_point_TV.csv']
    for dataset,model,f0_ref,f1_ref,agree_ref,rho_ref,top_ref,drift_ref,tv_ref in ORIGINAL:
        sel=scores[(scores.dataset==dataset)&(scores.model==model)]
        g=oof[(oof.dataset==dataset)&(oof.model==model)]
        if len(sel)!=5: raise ValueError(f'Expected 5 folds for {dataset} {model} not {len(sel)}')
        if 'true_class' not in g: raise ValueError('New reconstruction must include true_class')
        p0=np.array([json.loads(a) for a in g.proba_b0_json]);p1=np.array([json.loads(a) for a in g.proba_b1_json]);
        y=g.true_class.to_numpy(dtype=int)
        f0=f1_score(y,p0.argmax(axis=1),average='macro');f1=f1_score(y,p1.argmax(axis=1),average='macro'); agree=(p0.argmax(axis=1)==p1.argmax(axis=1)).mean()
        z=tbl5[(tbl5.dataset==dataset)&(tbl5.model==model)].iloc[0]
        t=tbl4[(tbl4.dataset==dataset)&(tbl4.model==model)].iloc[0]
        rows.append(dict(dataset=dataset,model=model,new_F1_B0=f0,paper_F1_B0=f0_ref,diff_F1_B0=f0-f0_ref,
                         new_F1_B1=f1,paper_F1_B1=f1_ref,diff_F1_B1=f1-f1_ref,
                         new_agreement=agree,paper_agreement=agree_ref,diff_agreement=agree-agree_ref,
                         new_CCPI_rho=z.rho_mean,paper_CCPI_rho=rho_ref,diff_rho=z.rho_mean-rho_ref,
                         new_Top3=z.top3_mean,paper_Top3=top_ref,diff_top3=z.top3_mean-top_ref,
                         new_Mean_abs_drift=float(ccpi[(ccpi.dataset==dataset)&(ccpi.model==model)].assign(d=lambda x:abs(x.ccpi_b1-x.ccpi_b0)).d.mean()),paper_Mean_abs_drift=drift_ref,
                         new_original_point_mean_TV=t.mean_TV,paper_original_point_mean_TV='NOT_REPORTED',
                         paper_perturbed_TV_p95=tv_ref,
                         note='New UCI reconstruction used disclosed assumptions; this is not historical protocol equivalence'))
    for (ds,mdl,block),(a,b) in BLOCK_ORIGINAL.items():
        g=ccpi[(ccpi.dataset==ds)&(ccpi.model==mdl)&(ccpi.block==block)]
        if len(g)!=5:raise ValueError(f'Expected 5 fold rows: {ds} {mdl} {block}')
        v0,v1=g.ccpi_b0.mean(),g.ccpi_b1.mean()
        blockrows.append(dict(dataset=ds,model=mdl,block=block,new_B0=v0,paper_B0=a,diff_B0=v0-a,new_B1=v1,paper_B1=b,diff_B1=v1-b))
    out.mkdir(exist_ok=True,parents=True)
    pd.DataFrame(rows).to_csv(out/'RECONSTRUCTED_vs_PUBLISHED_Table4_Table5.csv',index=False)
    pd.DataFrame(blockrows).to_csv(out/'RECONSTRUCTED_vs_PUBLISHED_Table7.csv',index=False)
    # A pass should not be determined from an arbitrary closeness threshold.
    (out/'INTERPRETATION.txt').write_text('Differences are diagnostic. No tolerance establishes historical equivalence without comparing the original source code, libraries, splits, random seeds, bootstrap, and perturbation draws. Do not tune assumptions to force matching numbers.\n')
    print('Comparison complete; discrepancies saved, no assumptions retroactively selected.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True,type=Path);p.add_argument('--outdir',required=True,type=Path);a=p.parse_args();run(a.run_dir,a.outdir)
