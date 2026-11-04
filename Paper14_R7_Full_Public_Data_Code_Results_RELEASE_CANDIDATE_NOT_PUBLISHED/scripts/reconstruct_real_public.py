#!/usr/bin/env python3
"""New independently implemented, batch-predicting public-UCI replication plan.

This script was executed on the frozen local public-UCI CSV snapshots in this release; it does not reproduce any unavailable original author-private environment.
It uses explicitly disclosed CONFIGURATION ASSUMPTIONS, and must not be
misdescribed as the authors' historical experiment. Uses existing local UCI
files ONLY. No network requests, no fabricated data, no synthesized observations.

Usage:
  python reconstruct_real_public.py \
    --dry-bean path/Dry_Bean_Dataset.xlsx \
    --rice path/Rice_Cammeo_Osmancik.arff \
    --outdir audit_reconstruction
  python reanalyse_from_logs.py \
    --fold-csv audit_reconstruction/fold_ccpi.csv \
    --oof-csv audit_reconstruction/oof_probabilities.csv \
    --outdir audit_reconstruction/derived_tables
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy, sklearn
from scipy.io import arff
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, RobustScaler, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import f1_score

B0=['Area','Perimeter','MajorAxisLength','MinorAxisLength','ConvexArea','Extent']
ALIAS={'Area':['Area'],'Perimeter':['Perimeter'],
 'MajorAxisLength':['MajorAxisLength','Major_Axis','MajorAxis','Major_Axis_Length'],
 'MinorAxisLength':['MinorAxisLength','Minor_Axis','MinorAxis','Minor_Axis_Length'],
 'ConvexArea':['ConvexArea','Convex_Area'], 'Extent':['Extent'],
 'Class':['Class','class','CLASS']}

def read_data(path):
    ext=path.suffix.lower()
    if ext=='.arff':
        data,meta=arff.loadarff(path);df=pd.DataFrame(data)
        for k in df.columns:
            if df[k].dtype=='object': df[k]=df[k].apply(lambda b:b.decode('utf8') if isinstance(b,bytes) else b)
    elif ext=='.xlsx':df=pd.read_excel(path)
    elif ext=='.csv':df=pd.read_csv(path)
    else:raise ValueError('Expected .arff, .xlsx or .csv UCI table')
    ren={}
    norm={''.join(ch for ch in str(k).lower() if ch.isalnum()):k for k in df.columns}
    for canon,names in ALIAS.items():
        found=next((norm.get(''.join(ch for ch in str(n).lower() if ch.isalnum())) for n in names if norm.get(''.join(ch for ch in str(n).lower() if ch.isalnum())) is not None),None)
        if found is None:raise ValueError(f'Missing {canon}. Available columns: {list(df.columns)}')
        ren[found]=canon
    df=df.rename(columns=ren)
    if df[B0+['Class']].isna().any().any():raise ValueError('Missing cells in six-block source')
    for c in B0:df[c]=pd.to_numeric(df[c],errors='raise')
    return df

def to_b1(x):
    a,p,L,l,C,ex=np.asarray(x).T
    ed=np.sqrt(4*a/np.pi)
    return np.column_stack((ed,4*np.pi*a/p**2,ed/L,L/l,a/C,ex))

def from_b1(z):
    ed, r, co, ar, sol, ex = np.asarray(z).T
    a = np.pi*ed**2/4.
    P = np.sqrt(4*np.pi*a/r)
    L = ed/co
    minor=L/ar
    convex=a/sol
    return np.column_stack((a,P,L,minor,convex,ex))

def valid(x):
    a,p,L,l,C,ex=np.asarray(x).T
    return (a>0)&(p>0)&(L>=l)&(l>0)&(C>=a)&(ex>0)&(ex<=1)&(p**2>=4*np.pi*a)&(C<=a/ex)

def estimators(seed,c,rate,n_jobs):
    return {
      'LR':make_pipeline(StandardScaler(), LogisticRegression(C=c,penalty='l2',solver='lbfgs',max_iter=4000,random_state=seed)),
      'RF':RandomForestClassifier(n_estimators=200,min_samples_leaf=2,n_jobs=n_jobs,random_state=seed),
      'HGB':HistGradientBoostingClassifier(max_iter=250,l2_regularization=1.,learning_rate=rate,random_state=seed),
    }

def supported_perturbations(xtr, xte, block, seed, draws):
    """Return exactly draws accepted changes for each supported held-out observation.
    Note that ''support'' is assessed independently of B0/B1 class agreement.
    """
    other=[k for k in range(6) if k!=block]
    sc=RobustScaler().fit(xtr[:,other]);a=sc.transform(xtr[:,other]);b=sc.transform(xte[:,other])
    train_near=NearestNeighbors(n_neighbors=6,n_jobs=1).fit(a)
    cap=float(np.quantile(train_near.kneighbors(a,return_distance=True)[0][:,5],.95))
    index=NearestNeighbors(n_neighbors=min(40,len(a)),n_jobs=1).fit(a)
    ds,nb=index.kneighbors(b)
    rng=np.random.default_rng(seed*7+block)
    kept=[];arr=[]
    for i,row in enumerate(xte):
        allowed=nb[i,ds[i]<=cap]
        if len(allowed)==0:continue
        draws_out=[]
        for attempt in range(max(100,draws*30)):
            k=int(rng.choice(allowed));alpha=float(rng.uniform(.1,.3))
            z=row.copy();z[block]=(1-alpha)*z[block]+alpha*xtr[k,block]
            if bool(valid(z[None,:])[0]):draws_out.append(z)
            if len(draws_out)==draws:break
        if len(draws_out)==draws:kept.append(i);arr.append(np.asarray(draws_out))
    if not kept:return np.empty((0,),int),np.empty((0,draws,6)),cap
    return np.asarray(kept,dtype=int),np.stack(arr),cap

def run(name,source,out,config,raw=False):
    df=read_data(source);original_count=len(df)
    if not raw:df=df.drop_duplicates().reset_index(drop=True)
    x=df[B0].to_numpy(float)
    if not valid(x).all():raise ValueError(f'{name}: {np.count_nonzero(~valid(x))} published vectors violate the proposed necessary geometry gate; original source must be examined, not dropped silently.')
    z=to_b1(x);le=LabelEncoder();y=le.fit_transform(df['Class'])
    folds=StratifiedKFold(n_splits=5,shuffle=True,random_state=20261016)
    oof=[];ccpi=[];scores=[];sample=[]
    for fold,(train,test) in enumerate(folds.split(x,y)):
        xb=x[train];xt=x[test];zb=z[train];zt=z[test];yt=y[train];yv=y[test]
        m0=estimators(20261016+fold,config.lr_c,config.hgb_learning_rate,config.n_jobs)
        m1=estimators(20261016+fold,config.lr_c,config.hgb_learning_rate,config.n_jobs)
        fit={}
        for model in ['LR','RF','HGB']:
            f0=m0[model].fit(xb,yt);f1=m1[model].fit(zb,yt)
            pp0=f0.predict_proba(xt);pp1=f1.predict_proba(zt)
            assert np.array_equal(f0.classes_,f1.classes_)
            pr0=pp0.argmax(axis=1);pr1=pp1.argmax(axis=1); agree=pr0==pr1
            fit[model]=(f0,f1,pp0,pp1,pr0,agree)
            scores.append(dict(dataset=name,model=model,fold=fold,n_train=len(train),n_test=len(test),
                f1_b0=f1_score(yv,pr0,average='macro'),f1_b1=f1_score(yv,pr1,average='macro'),
                agreement=float(agree.mean()),mean_tv_original=float(np.mean(.5*np.abs(pp0-pp1).sum(axis=1)))))
            for i,case in enumerate(test):
                oof.append(dict(dataset=name,model=model,fold=fold,sample_id=int(case),true_class=int(yv[i]),
                    proba_b0_json=json.dumps(pp0[i].tolist()),proba_b1_json=json.dumps(pp1[i].tolist())))
        for blockno,block in enumerate(B0):
            indices,pert,distcap=supported_perturbations(xb,xt,blockno,20261016+fold,config.draws)
            physical_support_rate=len(indices)/len(test)
            # Optional reviewer analysis: diagnostic for physically shared
            # perturbations that become large in the standardized B1 space.
            # This is a descriptive model-support diagnostic, not evidence of
            # a causal mechanism.
            if len(indices):
                transformed=to_b1(pert.reshape(-1,6)).reshape(len(indices),config.draws,6)
                sd=zb.std(axis=0,ddof=1)
                sd=np.where(sd<1e-12,1.,sd)
                baseline=zt[indices,None,:]
                zsteps=np.abs((transformed-baseline)/sd)
                standardized_step_mean=float(np.mean(np.max(zsteps,axis=2)))
                standardized_step_p95=float(np.quantile(np.max(zsteps,axis=2),.95))
                train_min=zb.min(axis=0);train_max=zb.max(axis=0)
                out_of_range=float(np.mean(np.any((transformed<train_min)|(transformed>train_max),axis=2)))
                # Exact inverse coordinate map, subject to machine rounding.
                inverse_rel=float(np.max(np.abs(from_b1(transformed.reshape(-1,6))-
                                   pert.reshape(-1,6))/(1+np.abs(pert.reshape(-1,6)))))
            else:
                standardized_step_mean=standardized_step_p95=out_of_range=inverse_rel=float('nan')
            for model,(f0,f1,p0,p1,pred,agree) in fit.items():
                sel=indices[agree[indices]]
                # The support rate does NOT include model agreement filtering.
                if not len(sel):raise ValueError(f'{name}:{model}: fold={fold}, block={block}, no common-class supported points')
                selected_pert=pert[agree[indices]]
                n=len(sel);d=config.draws
                qr0=f0.predict_proba(selected_pert.reshape(-1,6)).reshape(n,d,-1)
                qr1=f1.predict_proba(to_b1(selected_pert.reshape(-1,6))).reshape(n,d,-1)
                c=pred[sel];ar=np.arange(n)
                v0=np.abs(qr0[ar,:,c]-p0[sel,c][:,None]).mean(axis=1)
                v1=np.abs(qr1[ar,:,c]-p1[sel,c][:,None]).mean(axis=1)
                vtp=.5*np.abs(qr0-qr1).sum(axis=2)
                tv0=.5*np.abs(p0[sel]-p1[sel]).sum(axis=1)
                vtp_mean=vtp.mean(axis=1)
                margin=tv0+vtp_mean
                violations=np.sum(np.abs(v0-v1)>margin+1.e-10)
                if violations:raise AssertionError('Data-dependent TV CCPI upper bound violated!')
                ccpi.append(dict(dataset=name,model=model,fold=fold,block=block,
                    ccpi_b0=float(v0.mean()),ccpi_b1=float(v1.mean()),
                    support_rate=float(physical_support_rate),eligible_fraction=float(n/len(test)),
                    perturbed_tv_p95=float(np.quantile(vtp,.95)),
                    perturbed_tv_mean=float(vtp.mean()),max_sample_tv_bound_violation=int(violations),
                    B1_step_max_coord_in_train_SD_mean=standardized_step_mean,
                    B1_step_max_coord_in_train_SD_p95=standardized_step_p95,
                    B1_outside_train_marginal_range_fraction=out_of_range,
                    B1_inverse_max_scaled_error=inverse_rel))
                if config.sample_diagnostics:
                    for k,idx in enumerate(sel):
                        sample.append(dict(dataset=name,model=model,fold=fold,block=block,sample_id=int(test[idx]),
                            ccpi_b0=float(v0[k]),ccpi_b1=float(v1[k]),abs_drift=float(abs(v1[k]-v0[k])),
                            mean_tv_perturbed=float(vtp_mean[k]),original_tv=float(tv0[k]),tv_upper_bound=float(margin[k])))
        print(f'{name} fold {fold+1}/5 complete; train={len(train)}, test={len(test)}',flush=True)
    pd.DataFrame(oof).to_csv(out/f'{name}_oof_probabilities.csv',index=False)
    pd.DataFrame(ccpi).to_csv(out/f'{name}_fold_ccpi.csv',index=False)
    pd.DataFrame(scores).to_csv(out/f'{name}_fold_scores.csv',index=False)
    if sample:pd.DataFrame(sample).to_csv(out/f'{name}_sample_diagnostics.csv',index=False)
    return {'dataset':name,'original_rows':original_count,'used_rows':len(x),'dedup_removed':original_count-len(x),
            'classes':le.classes_.tolist(),'raw_flag':bool(raw)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-bean',required=True,type=Path)
    parser.add_argument('--rice',required=True,type=Path)
    parser.add_argument('--outdir',type=Path,default=Path('public_uci_independent_reconstruction'))
    parser.add_argument('--lr-c',type=float,default=1.,help='UNVERIFIED reconstruction assumption')
    parser.add_argument('--hgb-learning-rate',type=float,default=.1,help='UNVERIFIED reconstruction assumption')
    parser.add_argument('--draws',type=int,default=10)
    parser.add_argument('--n-jobs',type=int,default=2)
    parser.add_argument('--sample-diagnostics',action='store_true')
    parser.add_argument('--raw-dry-bean',action='store_true',help='Label as sensitivity analysis only')
    args=parser.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
    meta={'claim_scope':'NEW, INDEPENDENT, ASSUMPTION-BASED UCI RECONSTRUCTION — NOT ORIGINAL PAPER RUN',
        'software_versions':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
        'cv_seed_assumption':20261016,'paired_model_seed_assumption':True,'LR_penalty_assumption':'L2',
        'LR_C_assumption':args.lr_c,'HGB_rate_assumption':args.hgb_learning_rate,'CCPI_draws':args.draws,
        'seed_binding':'B0 and B1 model use the identical 20261016+fold random_state in this reconstruction',
        'CCPI_perturbation_protocol':'train-fold conditional KNN, local interpolation 0.10-0.30, 10 accepted vectors',
        'interpretive_caveat':'reconstruction of a public-data test, not the original author historical run'}
    for name,path in [('DryBean',args.dry_bean),('Rice',args.rice)]:
        if not path.is_file():raise FileNotFoundError(f'Missing local source file: {path}. Download authentic UCI file yourself, no synthetic substitution.')
        meta[f'{name}_source_path']=str(path)
        meta[f'{name}_source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    states=[]
    states.append(run('DryBean_RAW' if args.raw_dry_bean else 'DryBean',args.dry_bean,args.outdir,args,raw=args.raw_dry_bean))
    states.append(run('Rice',args.rice,args.outdir,args,raw=False))
    for tag in ('oof_probabilities','fold_ccpi','fold_scores'):
        dfs=[pd.read_csv(args.outdir/f'{d["dataset"]}_{tag}.csv') for d in states]
        pd.concat(dfs,ignore_index=True).to_csv(args.outdir/f'{tag}.csv',index=False)
    meta['dataset_states']=states
    (args.outdir/'RUN_MANIFEST.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('Finished independent reconstruction. DO NOT replace historical tables without author reconciliation.')

if __name__=='__main__':main()
