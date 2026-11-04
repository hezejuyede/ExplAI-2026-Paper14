#!/usr/bin/env python3
"""Paper 14: auditable, fold-aware review tables from REAL saved experiment logs.

Never substitutes fabricated/synthetic values for missing paper-14 logs.

Required --fold-csv fields:
  dataset,model,fold,block,ccpi_b0,ccpi_b1
Optional fields: support_rate,perturbed_tv_p95
Each dataset/model/fold must have exactly six distinct physical blocks.

Required --oof-csv fields:
  dataset,model,fold,sample_id,proba_b0_json,proba_b1_json
One row per held-out case. Probabilities must be class-aligned JSON arrays.

Copyright (c) 2026 for the authors. Source distributed for review purposes.
"""
import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

BLOCK_ORDER=['Area','Perimeter','MajorAxisLength','MinorAxisLength','ConvexArea','Extent']
ALIASES={'A':'Area','P':'Perimeter','L':'MajorAxisLength','l':'MinorAxisLength',
         'C':'ConvexArea','Ex':'Extent','MajorAxis':'MajorAxisLength',
         'MinorAxis':'MinorAxisLength','Convex Area':'ConvexArea'}

def hypergeom_top3_null():
    out=[]
    denom=math.comb(6,3)
    for k in range(4):
        out.append({'shared_blocks':k,'fraction':k/3,'probability':math.comb(3,k)*math.comb(3,3-k)/denom})
    assert sum(v['probability'] for v in out)==1
    assert abs(sum(v['fraction']*v['probability'] for v in out)-.5)<1e-12
    return pd.DataFrame(out)

def normalized_block(x):return ALIASES.get(str(x).strip(),str(x).strip())

def rank_pair(a,b):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
    assert len(a)==len(b)==6 and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    if np.unique(a).size<2 or np.unique(b).size<2:
        # A constant vector has no six-block ranking: never invent an ordering.
        return float('nan'),float('nan')
    rho=float(spearmanr(a,b).statistic)
    sa=np.sort(a)[::-1];sb=np.sort(b)[::-1]
    if sa[2]==sa[3] or sb[2]==sb[3]:
        # A tie exactly across the top-3 boundary makes the top set ambiguous.
        return rho,float('nan')
    top3=set(np.argsort(-a,kind='stable')[:3]).intersection(np.argsort(-b,kind='stable')[:3])
    return rho,len(top3)/3

def report_fold(ccpi):
    req={'dataset','model','fold','block','ccpi_b0','ccpi_b1'}
    if not req.issubset(ccpi.columns):raise ValueError(f'Missing columns: {sorted(req-set(ccpi.columns))}')
    df=ccpi.copy(); df['block']=df.block.map(normalized_block)
    for field in ['ccpi_b0','ccpi_b1']:
        df[field]=pd.to_numeric(df[field],errors='raise')
    foldrows=[]; blockrows=[]; withinrows=[]; driftrows=[]
    for (dataset,model), g in df.groupby(['dataset','model'],sort=True):
        repvectors={0:{},1:{}}
        for fold,h in g.groupby('fold',sort=True):
            if set(h.block)!=set(BLOCK_ORDER) or len(h)!=6:
                raise ValueError(f'{dataset} {model} fold {fold}: expected six unique blocks, got {list(h.block)}')
            h=h.set_index('block').reindex(BLOCK_ORDER)
            a=h.ccpi_b0.to_numpy(dtype=float);b=h.ccpi_b1.to_numpy(dtype=float)
            rho,top=rank_pair(a,b)
            row={'dataset':dataset,'model':model,'fold':fold,'rho_b0_vs_b1':rho,'top3_overlap':top,
                 'max_abs_drift':float(np.max(np.abs(a-b)))}
            for opt in ['support_rate','perturbed_tv_p95']:
                if opt in h.columns:row[f'{opt}_mean_across_blocks']=float(h[opt].astype(float).mean())
            foldrows.append(row)
            repvectors[0][fold]=a;repvectors[1][fold]=b
            for j,block in enumerate(BLOCK_ORDER):
                blockrows.append({'dataset':dataset,'model':model,'fold':fold,'block':block,
                                  'ccpi_b0':float(a[j]),'ccpi_b1':float(b[j]),
                                  'signed_drift':float(b[j]-a[j]),'abs_drift':float(abs(b[j]-a[j]))})
        for rep in [0,1]:
            for f1,f2 in itertools.combinations(repvectors[rep],2):
                rho,_=rank_pair(repvectors[rep][f1],repvectors[rep][f2])
                withinrows.append({'dataset':dataset,'model':model,'representation':f'B{rep}',
                                   'fold_1':f1,'fold_2':f2,'rho_within_rep':rho})
    fold=pd.DataFrame(foldrows); block=pd.DataFrame(blockrows);within=pd.DataFrame(withinrows)
    def mean_sd(s):return pd.Series({'mean':s.mean(),'sd':s.std(ddof=1),'minimum':s.min(),'maximum':s.max(),'n_folds':s.size})
    summaries=[]
    for (dataset,model),g in fold.groupby(['dataset','model']):
        w=within[(within.dataset==dataset)&(within.model==model)]
        x={'dataset':dataset,'model':model,'n_folds':len(g),
           'rho_mean':g.rho_b0_vs_b1.mean(),'rho_sd':g.rho_b0_vs_b1.std(ddof=1),
           'rho_min':g.rho_b0_vs_b1.min(),'rho_max':g.rho_b0_vs_b1.max(),
           'top3_mean':g.top3_overlap.mean(),'top3_sd':g.top3_overlap.std(ddof=1),
           'top3_min':g.top3_overlap.min(),'top3_max':g.top3_overlap.max(),
           'top3_null_expected':0.5,'top3_null_P_le_1_of_3':0.5,
           'n_rho_defined':int(g.rho_b0_vs_b1.notna().sum()),'n_top3_defined':int(g.top3_overlap.notna().sum()),
           'max_abs_drift_over_folds':g.max_abs_drift.max()}
        for rep in ['B0','B1']:
            wr=w[w.representation==rep].rho_within_rep
            x[f'{rep}_within_foldpair_rho_mean']=wr.mean()
            x[f'{rep}_within_foldpair_rho_sd']=wr.std(ddof=1)
            x[f'{rep}_foldpair_count']=len(wr)
        summaries.append(x)
    summary=pd.DataFrame(summaries)
    blocks=(block.groupby(['dataset','model','block'])
            .agg(n_folds=('ccpi_b0','size'),b0_mean=('ccpi_b0','mean'),b0_sd=('ccpi_b0','std'),
                 b1_mean=('ccpi_b1','mean'),b1_sd=('ccpi_b1','std'),
                 signed_diff_mean=('signed_drift','mean'), signed_diff_sd=('signed_drift','std'),
                 abs_diff_max=('abs_drift','max')).reset_index())
    return {'Table5_foldwise.csv':fold,'Table5_descriptive_with_null.csv':summary,
            'Appendix_sixblock_CCPI_mean_sd.csv':blocks,'Within_rep_foldpair_ranks.csv':within,
            'Appendix_perfold_sixblock_CCPI.csv':block}

def report_oof(oof):
    req={'dataset','model','fold','sample_id','proba_b0_json','proba_b1_json'}
    if not req.issubset(oof.columns):raise ValueError(f'Missing columns: {sorted(req-set(oof.columns))}')
    data=[]
    for row in oof.itertuples(index=False):
        a=np.array(json.loads(row.proba_b0_json),dtype=float)
        b=np.array(json.loads(row.proba_b1_json),dtype=float)
        if a.shape!=b.shape or a.ndim!=1 or a.size<2:raise ValueError(f'Class-alignment/dimensionality problem: {row.dataset}, {row.model}, id={row.sample_id}')
        if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not np.isclose(a.sum(),1,atol=1e-6) or not np.isclose(b.sum(),1,atol=1e-6):
            raise ValueError(f'Invalid probability vector at id={row.sample_id}')
        data.append({'dataset':row.dataset,'model':row.model,'fold':row.fold,'sample_id':row.sample_id,
                     'original_point_TV':0.5*np.abs(a-b).sum(),'decision_agreement':bool(a.argmax()==b.argmax())})
    tv=pd.DataFrame(data)
    res=(tv.groupby(['dataset','model']).agg(n=('original_point_TV','size'),
           mean_TV=('original_point_TV','mean'),median_TV=('original_point_TV','median'),
           p95_TV=('original_point_TV',lambda s:np.percentile(s,95)),
           agreement=('decision_agreement','mean')).reset_index())
    if tv.duplicated(['dataset','model','sample_id']).any():
        raise ValueError('OOF duplicates: sample_id repeated across folds for same model and dataset')
    return {'Table4_original_point_TV.csv':res,'Appendix_original_point_TV_by_sample.csv':tv}

def selftest():
    null=hypergeom_top3_null();assert np.allclose(null.probability,[.05,.45,.45,.05]);
    assert rank_pair([1,2,3,4,5,6],[1,2,3,4,5,6])==(1.,1.)
    assert rank_pair([1,2,3,4,5,6],[6,5,4,3,2,1])==(-1.,0.)
    toy=[]
    for fold in range(2):
        for i,block in enumerate(BLOCK_ORDER):
            toy.append({'dataset':'TEST_ONLY','model':'TEST_ONLY','fold':fold,'block':block,
                        'ccpi_b0':i+1,'ccpi_b1':i+1})
    o=report_fold(pd.DataFrame(toy))
    assert o['Table5_foldwise.csv'].rho_b0_vs_b1.eq(1).all()
    s=report_oof(pd.DataFrame([{'dataset':'TEST_ONLY','model':'TEST_ONLY','fold':0,
             'sample_id':0,'proba_b0_json':'[0.7,0.3]','proba_b1_json':'[0.6,0.4]'}]))
    assert abs(s['Table4_original_point_TV.csv'].mean_TV.iloc[0]-0.1)<1e-12
    print('PASS: exact combinatorial null, six-block rank, fold aggregation, paired TV; toy test data NOT research output')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--fold-csv',type=Path)
    ap.add_argument('--oof-csv',type=Path)
    ap.add_argument('--outdir',type=Path,default=Path('review_outputs'))
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:return selftest()
    args.outdir.mkdir(parents=True,exist_ok=True)
    hypergeom_top3_null().to_csv(args.outdir/'Exact_top3_chance_null.csv',index=False)
    inputs={}
    if args.fold_csv:
        outputs=report_fold(pd.read_csv(args.fold_csv))
        for n,d in outputs.items():d.to_csv(args.outdir/n,index=False)
        inputs['fold_csv']=str(args.fold_csv)
    if args.oof_csv:
        outputs=report_oof(pd.read_csv(args.oof_csv))
        for n,d in outputs.items():d.to_csv(args.outdir/n,index=False)
        inputs['oof_csv']=str(args.oof_csv)
    if not inputs:
        pd.DataFrame(columns=['dataset','model','fold','block','ccpi_b0','ccpi_b1','support_rate','perturbed_tv_p95']).to_csv(args.outdir/'INPUT_SCHEMA_fold_ccpi.csv',index=False)
        pd.DataFrame(columns=['dataset','model','fold','sample_id','proba_b0_json','proba_b1_json']).to_csv(args.outdir/'INPUT_SCHEMA_oof_probabilities.csv',index=False)
        print('Only analytical null output and EMPTY input schemas created: no paper-14 experiment logs provided. No empirical claims reproduced.')
    else:print('Tables generated from PROVIDED rows only. Verify logs against original experimental run before submission.')
    (args.outdir/'RUN_MANIFEST.json').write_text(json.dumps({'data_provenance':inputs,'null_calibration':'analytic','empirical_status':'recomputed only if original logs supplied'},indent=2),encoding='utf-8')
if __name__=='__main__':main()
