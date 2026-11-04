#!/usr/bin/env python3
import pandas as pd, numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr
from reconstruct_real_public import B0,read_data,to_b1,estimators
from pathlib import Path
p=Path(__file__).resolve().parent.parent;df=read_data(p/'data/Dry_Bean_Dataset.csv').drop_duplicates().reset_index(drop=True)
x=df[B0].to_numpy(float);z=to_b1(x);y=LabelEncoder().fit_transform(df.Class)
out=[]
for fold,(tr,te) in enumerate(StratifiedKFold(n_splits=5,shuffle=True,random_state=20261016).split(x,y)):
 imps=[]
 for rep,X in [('B0',x),('B1',z)]:
  mdl=estimators(20261016+fold,1.,.1,2)['LR'].fit(X[tr],y[tr])
  pi=permutation_importance(mdl,X[te],y[te],scoring='neg_log_loss',random_state=20261016+fold,n_repeats=5,n_jobs=1)
  imps.append(pi.importances_mean)
  for i,b in enumerate(B0):out.append({'fold':fold,'representation':rep,'block_paired_by_convention':b,
     'mean_importance':float(pi.importances_mean[i]),'sd_repeats':float(pi.importances_std[i])})
 a,b=imps;rho=spearmanr(a,b).statistic;overlap=len(set(np.argsort(-a)[:3])&set(np.argsort(-b)[:3]))/3
 print(fold,'rho',rho,'overlap',overlap)
outdf=pd.DataFrame(out);outdf.to_csv(p/'results/extended/LR_permutation_DryBean_folds.csv',index=False)
summary=[]
for fold,g in outdf.groupby('fold'):
 a=g[g.representation=='B0'].sort_values('block_paired_by_convention').mean_importance.to_numpy()
 b=g[g.representation=='B1'].sort_values('block_paired_by_convention').mean_importance.to_numpy()
 summary.append((spearmanr(a,b).statistic,len(set(np.argsort(-a)[:3])&set(np.argsort(-b)[:3]))/3))
s=np.asarray(summary);print('mean rho',s[:,0].mean(),'sd',s[:,0].std(ddof=1),'top3',s[:,1].mean());
(p/'results/extended/LR_permutation_DryBean_summary.csv').write_text('mean_rho,sd_rho,mean_top3_overlap\n'+','.join(map(str,[s[:,0].mean(),s[:,0].std(ddof=1),s[:,1].mean()]))+'\n')
