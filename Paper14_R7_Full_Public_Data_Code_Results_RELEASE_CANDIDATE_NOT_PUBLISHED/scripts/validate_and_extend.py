#!/usr/bin/env python3
"""Validate independent public-UCI rerun; extend with actual LR linear SHAP and model-preserving control.
All empirical results use the local UCI dataset snapshots, not synthetic observations.
Author must verify assumptions before reusing them in scientific paper.
"""
from pathlib import Path
import json, hashlib
import numpy as np, pandas as pd, scipy, shap, sklearn
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from reconstruct_real_public import read_data, B0, to_b1,from_b1,estimators,supported_perturbations

root=Path(__file__).resolve().parent.parent; out=root/'results/extended';out.mkdir(exist_ok=True)
fol=pd.read_csv(root/'results/real_reconstruction/fold_ccpi.csv');oof=pd.read_csv(root/'results/real_reconstruction/oof_probabilities.csv')
D=pd.read_csv(root/'results/real_reconstruction/fold_scores.csv')
model_names=['LR','RF','HGB']; checks={}
assert len(fol)==180, len(fol)
assert len(D)==30, len(D)
assert oof.groupby(['dataset','model']).size().to_dict()=={(d,m):n for d,n in [('DryBean',13543),('Rice',3810)] for m in model_names}
checks['real_rerun_fold_rows']=int(len(fol));checks['real_rerun_oof_rows']=int(len(oof));checks['fold_models']=int(len(D))
checks['support_min']=float(fol.support_rate.min())
checks['CCPI_nonnegative']=bool((fol.ccpi_b0>=0).all() and (fol.ccpi_b1>=0).all())
assert checks['CCPI_nonnegative']
# Sample and original-probability TV audit
samp=pd.concat([pd.read_csv(root/'results/real_reconstruction'/f'{ds}_sample_diagnostics.csv') for ds in ['DryBean','Rice']],ignore_index=True)
checks['sample_diagnostic_count']=int(len(samp))
checks['tv_bound_violation_max']=int((samp.abs_drift-samp.tv_upper_bound>1e-10).sum())
assert checks['tv_bound_violation_max']==0
sample_corr=[]
for (ds,m),g in samp.groupby(['dataset','model'],sort=True):
    rho=spearmanr(g.abs_drift,g.original_tv+g.mean_tv_perturbed).statistic
    sample_corr.append({'dataset':ds,'model':m,'n_diagnostic_rows':len(g),'spearman_absCCPI_vs_localTVbound':rho,
                        'mean_abs_drift':g.abs_drift.mean(),'mean_TV_original':g.original_tv.mean(),'mean_TV_perturbed':g.mean_tv_perturbed.mean(),
                        'max_drift_minus_bound':(g.abs_drift-g.tv_upper_bound).max()})
pd.DataFrame(sample_corr).to_csv(out/'sample_TV_drift_diagnostics.csv',index=False)
# Historical raw release vs deduplicated, under new reconstruction
raw=pd.read_csv(root/'results/raw_sensitivity/DryBean_RAW_fold_ccpi.csv')
raw_scores=pd.read_csv(root/'results/raw_sensitivity/DryBean_RAW_fold_scores.csv')
checks['raw_release_fold_rows']=int(len(raw))
for tag,df in [('unique',fol[fol.dataset=='DryBean']),('raw',raw)]:
 for block in ['Area','ConvexArea']:
  ss=df[df.block==block];assert len(ss)==15
  checks[f'DryBean_{tag}_{block}_B1_greater_count']=int((ss.ccpi_b1>ss.ccpi_b0).sum())
raw_com=[]
for m in model_names:
  for block in B0:
   a=fol[(fol.dataset=='DryBean')&(fol.model==m)&(fol.block==block)]
   b=raw[(raw.model==m)&(raw.block==block)]
   raw_com.append({'dataset':'DryBean','model':m,'block':block,'n_folds':5,
                   'dedup_delta_mean':(a.ccpi_b1-a.ccpi_b0).mean(),
                   'raw_delta_mean':(b.ccpi_b1-b.ccpi_b0).mean(),
                   'raw_minus_dedup_delta':(b.ccpi_b1-b.ccpi_b0).mean()-(a.ccpi_b1-a.ccpi_b0).mean()})
pd.DataFrame(raw_com).to_csv(out/'DryBean_raw_vs_deduplicated.csv',index=False)
# Actual B1 standard train scale and extrapolation diagnostics
scale=fol.groupby(['dataset','block'],as_index=False).agg(
    mean_B1_max_coordinate_step_SD=('B1_step_max_coord_in_train_SD_mean','mean'),
    p95_B1_max_coordinate_step_SD=('B1_step_max_coord_in_train_SD_p95','mean'),
    fraction_any_B1_coordinate_outside_training_range=('B1_outside_train_marginal_range_fraction','mean'),
    inverse_max_relative_error=('B1_inverse_max_scaled_error','max'))
scale.to_csv(out/'B1_geometry_support_mechanism.csv',index=False)
# Entire 30 comparisons from cross-block signed change
block_table=fol.groupby('block').apply(lambda g:pd.Series({'n':len(g),'positive':int((g.ccpi_b1>g.ccpi_b0).sum()),
                         'fraction_positive':float((g.ccpi_b1>g.ccpi_b0).mean()),
                         'mean_signed_change':(g.ccpi_b1-g.ccpi_b0).mean(),
                         'mean_absolute_change':(g.ccpi_b1-g.ccpi_b0).abs().mean()}),include_groups=False).reset_index()
block_table.to_csv(out/'Table6_new_signed_changes.csv',index=False)
assert set(block_table.loc[block_table.block.isin(['Area','ConvexArea']),'positive'])=={30}
# Stable magnitude table for size and convexity
major=fol[fol.block.isin(['Area','ConvexArea'])].groupby(['dataset','model','block'],as_index=False).agg(B0_mean=('ccpi_b0','mean'),B1_mean=('ccpi_b1','mean'),
       B0_SD=('ccpi_b0','std'),B1_SD=('ccpi_b1','std'))
major['signed_change']=major.B1_mean-major.B0_mean
major.to_csv(out/'Table7_new_two_blocks.csv',index=False)
# Actual fresh SHAP LR across two datasets, paired B0 and B1, all folds; no spurious rank independence claims
shaprows=[]
for ds,data_file in [('DryBean',root/'data/Dry_Bean_Dataset.csv'),('Rice',root/'data/Rice_Osmancik_Cammeo_Dataset.csv')]:
 df=read_data(data_file)
 if ds=='DryBean': df=df.drop_duplicates().reset_index(drop=True)
 xx=df[B0].to_numpy(float); zz=to_b1(xx)
 from sklearn.preprocessing import LabelEncoder
 y=LabelEncoder().fit_transform(df.Class)
 cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=20261016)
 for fold,(tr,te) in enumerate(cv.split(xx,y)):
  importance={}
  for rep,x in [('B0',xx),('B1',zz)]:
   model=estimators(20261016+fold,1.0,.1,2)['LR'].fit(x[tr],y[tr])
   sc,lr=model.steps[0][1],model.steps[1][1]
   Xtr=sc.transform(x[tr]); Xte=sc.transform(x[te])
   rng=np.random.default_rng(20261016+fold)
   ibg=rng.choice(len(tr),size=min(1000,len(tr)),replace=False)
   bg=Xtr[ibg]
   # Full independent SHAP call using affine sklearn LR, independent-feature model semantics
   exp=shap.LinearExplainer(lr,bg)
   values=np.asarray(exp(Xte).values)
   if values.ndim==3: imp=np.abs(values).mean(axis=(0,2))
   elif values.ndim==2: imp=np.abs(values).mean(axis=0)
   else: raise ValueError(values.shape)
   assert len(imp)==6
   importance[rep]=imp
   for i,(block,iv) in enumerate(zip(B0,imp)):
    shaprows.append({'dataset':ds,'fold':fold,'representation':rep,'block_paired_by_convention':block,'importance_mean_abs_shap':float(iv),
      'shap_version':shap.__version__,'background_n':len(bg),'sample_n':len(te),'LR_C':1.0,'aggregation':'mean_abs_over_heldout_and_classes'})
  from scipy.stats import rankdata
  ro=spearmanr(importance['B0'],importance['B1']).statistic
  b0top=set(np.argsort(-importance['B0'])[:3]);b1top=set(np.argsort(-importance['B1'])[:3]);ov=len(b0top&b1top)/3
  print('SHAP',ds,fold,'rho',ro,'top3',ov,flush=True)
pd.DataFrame(shaprows).to_csv(out/'LR_SHAP_all_folds_six_blocks.csv',index=False)
shapsum=[]
for (ds,fold),g in pd.DataFrame(shaprows).groupby(['dataset','fold']):
 a=g[g.representation=='B0'].sort_values('block_paired_by_convention').importance_mean_abs_shap.to_numpy()
 b=g[g.representation=='B1'].sort_values('block_paired_by_convention').importance_mean_abs_shap.to_numpy()
 ro=spearmanr(a,b).statistic;ov=len(set(np.argsort(-a)[:3])&set(np.argsort(-b)[:3]))/3
 shapsum.append({'dataset':ds,'fold':fold,'rho':ro,'top3_overlap':ov})
shapdf=pd.DataFrame(shapsum);shapdf.to_csv(out/'LR_SHAP_fold_transports.csv',index=False)
shap_ag=shapdf.groupby('dataset',as_index=False).agg(mean_rho=('rho','mean'),sd_rho=('rho','std'),mean_top3_overlap=('top3_overlap','mean'),sd_top3_overlap=('top3_overlap','std'))
shap_ag.to_csv(out/'Table8_new_LR_SHAP.csv',index=False)
# Positive-control model preserving invertible map: train B0 models only and compose f0(T^{-1}(z)).
control=[]
for ds,data_file in [('DryBean',root/'data/Dry_Bean_Dataset.csv'),('Rice',root/'data/Rice_Osmancik_Cammeo_Dataset.csv')]:
 df=read_data(data_file)
 if ds=='DryBean': df=df.drop_duplicates().reset_index(drop=True)
 X=df[B0].to_numpy(float);from sklearn.preprocessing import LabelEncoder
 y=LabelEncoder().fit_transform(df.Class)
 tr,te=next(iter(StratifiedKFold(n_splits=5,shuffle=True,random_state=20261016).split(X,y)))
 X_test=X[te]; Z_test=to_b1(X_test)
 for modelname,f0 in estimators(20261016,1.0,.1,2).items():
  f0.fit(X[tr],y[tr])
  p=f0.predict_proba(X_test)
  pctrl=f0.predict_proba(from_b1(Z_test))
  maxorig=float(np.max(np.abs(p-pctrl)))
  block=0
  idx,pert,cap=supported_perturbations(X[tr],X_test,block,seed=20261016,draws=10)
  sel=idx[:250];c=p[sel].argmax(axis=1)
  pert=pert[:len(sel)]
  predorig=f0.predict_proba(pert.reshape(-1,6)).reshape(len(sel),10,-1)
  predctrl=f0.predict_proba(from_b1(to_b1(pert.reshape(-1,6)))).reshape(len(sel),10,-1)
  v0=np.abs(predorig[np.arange(len(sel)),:,c]-p[sel,c,None]).mean(axis=1)
  v1=np.abs(predctrl[np.arange(len(sel)),:,c]-pctrl[sel,c,None]).mean(axis=1)
  control.append({'dataset':ds,'model':modelname,'fold':0,'n':len(sel),'block':'Area',
                   'max_original_point_prob_gap':maxorig,'max_positive_control_CCPI_gap':float(np.max(np.abs(v1-v0)))})
pd.DataFrame(control).to_csv(out/'model_preserving_positive_control.csv',index=False)
checks.update({'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'shap':shap.__version__,
               'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'data/Dry_Bean_Dataset.csv',root/'data/Rice_Osmancik_Cammeo_Dataset.csv')},
               'note':'NEW_INDEPENDENT_UCI_RECONSTRUCTION; configuration hypotheses not historical facts; SHAP first-party package actual execution.'})
(out/'EXTENDED_VALIDATION_MANIFEST.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print('VERIFICATION COMPLETE',json.dumps(checks,indent=2),flush=True)
