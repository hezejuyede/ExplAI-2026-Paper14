#!/usr/bin/env python3
"""Build AUTHOR-REVIEW CEUR-like ODT from the existing anonymous/source authors' manuscript.
All numbers in manuscript derived from local UCI CSV re-execution, with discrepancy trail.
Does not claim to be certified against the official organizer ODT template.
"""
from odf.opendocument import load
from odf import text, table, draw
from odf.teletype import extractText
from pathlib import Path
from copy import deepcopy

def clone(e):
    return deepcopy(e,{id(e.parentNode):None,id(e.previousSibling):None,id(e.nextSibling):None,id(e.ownerDocument):None})
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parent.parent;dest=root/'paper';dest.mkdir(exist_ok=True)
source=root/'r3src/manuscript/ExplAI2026_P14_R2_AUTHOR_REVIEW.odt';doc=load(str(source));parent=doc.text
real=root/'results/real_reconstruction';der=root/'results/derived';ext=root/'results/extended'
score=pd.read_csv(real/'fold_scores.csv'); corr=pd.read_csv(der/'Table5_descriptive_with_null.csv');tv=pd.read_csv(der/'Table4_original_point_TV.csv')
boot=pd.read_csv(der/'paired_bootstrap.csv'); sig=pd.read_csv(ext/'Table6_new_signed_changes.csv');detail=pd.read_csv(ext/'Table7_new_two_blocks.csv')
block=pd.read_csv(der/'Appendix_sixblock_CCPI_mean_sd.csv');shap=pd.read_csv(ext/'Table8_new_LR_SHAP.csv')
perm=pd.read_csv(ext/'LR_permutation_DryBean_summary.csv').iloc[0]

def get_p(s):
 return next(e for e in parent.childNodes if e.qname[1]=='p' and s in extractText(e))

def change_paragraph(q, new):
 el=get_p(q)
 el.childNodes = []
 el.addText(new)
 return el

def mkpar(txt,style='P6'):
 return text.P(stylename=style,text=txt)

def after(el, newel):
 ix=parent.childNodes.index(el)
 if ix==len(parent.childNodes)-1:parent.addElement(newel)
 else:parent.insertBefore(newel, parent.childNodes[ix+1]);
 return newel

def replace_table(tname,rows,template=None):
 old=next(e for e in parent.childNodes if e.qname[1]=='table' and e.getAttribute('name')==tname)
 if template:
  tem=next(e for e in parent.childNodes if e.qname[1]=='table' and e.getAttribute('name')==template)
  new=clone(tem);new.setAttribute('name',tname+'_revised')
 else:
  new=clone(old);new.setAttribute('name',tname+'_revised')
 oldrows=new.getElementsByType(table.TableRow)
 if not oldrows:raise ValueError('No template rows')
 hdr=clone(oldrows[0]); data=clone(oldrows[1]);
 for e in list(new.childNodes):
  if e.qname[1] in ('table-row','table-header-rows','table-rows','table-row-group'):
   new.removeChild(e)
 for i,row in enumerate(rows):
  tmp=clone(hdr if i==0 else data)
  cells=[c for c in tmp.childNodes if c.qname[1]=='table-cell']
  if len(cells)!=len(row):raise ValueError(f'{tname} row {i} length: {len(cells)} != {len(row)}')
  for cell,val in zip(cells,row):
   # Replace cell content, preserve table-border styles and paragraph style from cloned row.
   orig_ps=[c for c in cell.childNodes if c.qname[1] in ('p','h')]
   pstyle=orig_ps[0].getAttribute('stylename') if orig_ps else None
   for c in list(cell.childNodes):cell.removeChild(c)
   p=text.P(stylename=pstyle,text=str(val)) if pstyle else text.P(text=str(val))
   cell.addElement(p)
  if i==0:
   headergroup=table.TableHeaderRows(); headergroup.addElement(tmp); new.addElement(headergroup)
  else:new.addElement(tmp)
 parent.insertBefore(new,old);parent.removeChild(old)
 return new

pretty=lambda ds:'Dry Bean' if ds=='DryBean' else 'Rice'
ms={'LR':0,'RF':1,'HGB':2}
order=[('DryBean','HGB'),('DryBean','LR'),('DryBean','RF'),('Rice','HGB'),('Rice','LR'),('Rice','RF')]
res=[]
for ds,m in order:
 b=boot[(boot.dataset==ds)&(boot.model==m)].iloc[0]
 t=tv[(tv.dataset==ds)&(tv.model==m)].iloc[0]
 # derive macro-F1 from original per-sample OOF for use in new table (not fold-mean)
 oo=pd.read_csv(real/f'{ds}_oof_probabilities.csv');g=oo[oo.model==m]
 import json
 from sklearn.metrics import f1_score
 y=g.true_class.to_numpy(int)
 p0=np.vstack([json.loads(x) for x in g.proba_b0_json]);p1=np.vstack([json.loads(x) for x in g.proba_b1_json])
 f0=f1_score(y,p0.argmax(axis=1),average='macro');f1=f1_score(y,p1.argmax(axis=1),average='macro')
 res.append([pretty(ds),m,f'{f0:.4f}',f'{f1:.4f}',f'{b.paired_dF1_pp:+.3f}',f'[{b.CI_low_pp:+.3f}, {b.CI_high_pp:+.3f}]',f'{t.agreement*100:.2f}%',f'{t.mean_TV:.4f}'])
T4=replace_table('Table4',[['Dataset','Model','F1 B0','F1 B1','ΔF1 (pp)','95% paired CI','Agree','Mean TV']]+res,template='Table5')
change_paragraph('Table 4. Paired out-of-fold prediction transport.','Table 4. Independently recomputed paired out-of-fold prediction transport and original-point TV (1,000 paired bootstrap resamples).')
# Distinct six-model CCPI rank table with spread
new5=[]
for ds,m in order:
 g=corr[(corr.dataset==ds)&(corr.model==m)].iloc[0]
 sup=pd.read_csv(real/f'{ds}_fold_ccpi.csv');ss=sup[sup.model==m]
 new5.append([pretty(ds),m,f'{g.rho_mean:+.3f}±{g.rho_sd:.3f}',f'[{g.rho_min:+.3f}, {g.rho_max:+.3f}]',f'{g.top3_mean:.3f}',f'{ss.assign(ad=(ss.ccpi_b1-ss.ccpi_b0).abs()).ad.mean():.4f}',f'{ss.perturbed_tv_p95.mean():.3f}',f'{ss.support_rate.min()*100:.2f}%'])
T5=replace_table('Table5',[['Dataset','Model','ρ mean±SD','ρ range','Top-3','Mean |Δ|','TV p95','Min supp.']]+new5)
change_paragraph('Table 5. CCPI transport diagnostics.','Table 5. CCPI foldwise rank transport (independent public-data reconstruction). Five-fold SD is descriptive, not an independent-trial uncertainty interval.')
# Insert second table of within representation stability and max per-sample block drift
oldcap=get_p('Table 5. CCPI foldwise rank transport')
T5brows=[['Dataset','Model','Within B0 ρ','Within B1 ρ','Max block |Δ|']]
for ds,m in order:
 g=corr[(corr.dataset==ds)&(corr.model==m)].iloc[0]
 T5brows.append([pretty(ds),m,f'{g.B0_within_foldpair_rho_mean:.3f}',f'{g.B1_within_foldpair_rho_mean:.3f}',f'{g.max_abs_drift_over_folds:.4f}'])
# 5-column table: adapt 6-column Table7 by eliminating 6th cell + using same styles
T7tmp=next(e for e in parent.childNodes if e.qname[1]=='table' and e.getAttribute('name')=='Table7')
newtbl=clone(T7tmp);newtbl.setAttribute('name','Table5b_R5')
for e in list(newtbl.childNodes):
 if e.qname[1] in ('table-row','table-header-rows','table-rows','table-row-group'):newtbl.removeChild(e)
hdr=clone(T7tmp.getElementsByType(table.TableRow)[0])
body=clone(T7tmp.getElementsByType(table.TableRow)[1])
for i,row in enumerate(T5brows):
 rr=clone(hdr if i==0 else body);cells=[e for e in rr.childNodes if e.qname[1]=='table-cell']
 for c in cells[len(row):]:rr.removeChild(c)
 for c,v in zip(cells,row):
  p=c.getElementsByType(text.P)[0];sty=p.getAttribute('stylename')
  for node in list(c.childNodes):c.removeChild(node)
  c.addElement(text.P(stylename=sty,text=str(v)) if sty else text.P(text=str(v)))
 if i==0:
  h=table.TableHeaderRows();h.addElement(rr);newtbl.addElement(h)
 else:newtbl.addElement(rr)
# remove one extra table column only if present
cols=[e for e in newtbl.childNodes if e.qname[1]=='table-column']
# source has a repeated single column declaration with 6, so leave, table has 5 cells with some extra implicit padding
T5end=next(e for e in parent.childNodes if e.qname[1]=='table' and e.getAttribute('name')=='Table5_revised')
cap=after(T5end,mkpar('Table 5b. Within-representation rank stability (mean of ten fold-pair Spearman correlations) and maximum absolute foldwise block drift.','P11'))
after(cap,newtbl)

# signed table values
label={'Area':'Area (A)','ConvexArea':'ConvexArea (C)','MajorAxisLength':'Major axis (L)','MinorAxisLength':'Minor axis (l)','Perimeter':'Perimeter (P)','Extent':'Extent (Ex)'}
sigrows=[]
for b in ['Area','ConvexArea','MajorAxisLength','MinorAxisLength','Perimeter','Extent']:
 g=sig[sig.block==b].iloc[0]
 sigrows.append([label[b],str(int(g.n)),str(int(g.positive)),f'{g.fraction_positive:.3f}',f'{g.mean_signed_change:+.5f}',f'{g.mean_absolute_change:.5f}'])
replace_table('Table6',[['Block','Comparisons','B1>B0','Frac. positive','Mean signed Δ','Mean |Δ|']]+sigrows)
change_paragraph('Table 6. Cross-dataset signed CCPI block changes.','Table 6. Signed CCPI physical-block changes in the fully executed independent public-data reconstruction (30 paired model-fold-dataset comparisons).')
# Table7 new
large=[]
for ds,m in order:
 for b in ['Area','ConvexArea']:
  g=detail[(detail.dataset==ds)&(detail.model==m)&(detail.block==b)].iloc[0]
  large.append([pretty(ds),m,b,f'{g.B0_mean:.5f}',f'{g.B1_mean:.5f}',f'{g.signed_change:+.5f}'])
replace_table('Table7',[['Dataset','Model','Block','CCPI B0','CCPI B1','Signed Δ']]+large)
change_paragraph('Table 7. Area and ConvexArea CCPI magnitudes.','Table 7. Area/ConvexArea CCPI mean magnitudes from the new independent five-fold UCI reconstruction.')
# Table8 independent SHAP and permutation
shaprows=[['Dataset','Comparator','ρ mean±SD','Top-3 overlap']]
for ds in ['DryBean','Rice']:
 g=shap[shap.dataset==ds].iloc[0]
 shaprows.append([pretty(ds),'LR linear SHAP',f'{g.mean_rho:+.3f}±{g.sd_rho:.3f}',f'{g.mean_top3_overlap:.3f}'])
shaprows.append(['Dry Bean','LR permutation',f'{perm.mean_rho:+.3f}±{perm.sd_rho:.3f}',f'{perm.mean_top3_overlap:.3f}'])
replace_table('Table8',shaprows)
change_paragraph('Table 8. Native attribution transport for LR.','Table 8. LR native feature-credit ranks under the six-block pairing convention (new SHAP and permutation computations, 5 folds).')

# Replace science narrative with strictly consistent rerun values
change_paragraph('Feature attributions are often interpreted',
  'Feature importance is often interpreted as a property of physical measurements, yet an invertible reparameterization changes the coordinates seen by a finite learner. We audit B0 (six primitive morphometrics) against an analytically bijective B1 (six derived descriptors) using one shared conditional perturbation kernel in primitive space. We report a newly executed and fully traceable five-fold reanalysis of 13,543 deduplicated Dry Bean observations and an independent 3,810-observation Rice dataset, comparing logistic regression, random forest and histogram gradient boosting. Hard-decision agreement is 95.57–98.56%, but fitted probability functions differ: mean out-of-fold total-variation (TV) distance ranges from 0.0159 to 0.0627. CCPI sensitivity of Area and ConvexArea increases under B1 in 30/30 model-fold-dataset comparisons for each block. Six-block rankings vary, but top-three overlap must be interpreted against a random-set expectation of 0.5. Recomputed linear-SHAP ranks also vary under a conventional, non-unique block pairing. The finding concerns representation-dependent fitted functions and physical-response diagnostics; it does not establish failure of an explainer under an unchanged predictor. All reanalysis settings and output records are provided for author validation.')
change_paragraph('We evaluate multinomial logistic regression',
  'The independently executed public-data reconstruction uses Python 3.13.5, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, scikit-learn 1.8.0 and SHAP 0.50.0. It fits logistic regression (LR: StandardScaler, L2 penalty, C=1, lbfgs, maximum 4,000 iterations), random forest (RF: 200 trees, minimum leaf size 2), and histogram gradient boosting (HGB: 250 iterations, learning rate 0.1, L2 regularization 1). Algorithm settings not specified in the initial submission are explicitly reconstruction choices, not verified historical settings. Such choices include LR C=1, HGB learning rate 0.1 and the detailed random-seed binding; differences from the initial submission are retained in the accompanying discrepancy audit [30].')
change_paragraph('A fixed five-fold stratified cross-validation split',
  'Each dataset is split by stratified, shuffled five-fold cross-validation with seed 20261016; the two representations share identical fold membership and use model seeds 20261016+fold (fold numbered from zero). The training fold alone determines scaling, nearest-neighbor donors and support radii, and no held-out labels enter CCPI donor selection. Original-point TV is computed on every held-out case; paired macro-F1 bootstrap intervals are computed over 1,000 OOF resamples with seed 20261104. Both data sources are frozen as local CSV files with SHA-256 checksums in the reproducibility manifest. Analyses are descriptive with respect to correlated folds, models and perturbed samples.')
change_paragraph('Each observation receives paired out-of-fold predictions',
  'Each observation receives paired out-of-fold predictions per representation and model. The paired classification bootstrap recomputes macro-F1 from the same resampled object indices; fold results are not treated as independent experimental trials. CCPI is computed separately within each fold with ten accepted local, constraint-respecting perturbations per supported sample and physical block; the same perturbations are mapped to B0 and B1. We report foldwise six-block CCPI values, sample-level TV diagnostics, cross-fold rank stability and within-representation rank stability. Linear SHAP (shap.LinearExplainer with up to 1,000 training-fold background observations; mean absolute values averaged across held-out samples and classes) is calculated for LR. A Dry Bean LR permutation comparator uses held-out negative log-loss, five repetitions, and fold-specific seeds. The block correspondence in Table 1 is a reporting convention, not a unique geometric attribution mapping.')
change_paragraph('Table 3. Experimental protocol.','Table 3. Design of the five-fold reanalysis; detailed settings and data checksums accompany the source archive.')
# Tables narrative update anchor strings from R2
change_paragraph('Table 4 reports paired',
 'Table 4 reports paired full out-of-fold macro-F1 and original-point TV from the independent reconstruction. B1 modestly improves Dry Bean F1 for all three learner families: +0.881, +0.663 and +0.776 percentage points for HGB, LR and RF, respectively, with positive paired bootstrap intervals. Agreement spans 95.57–97.56%, but the original-point mean TV spans 0.0358–0.0627. Thus approximate agreement of hard decisions does not establish identity of fitted probability functions.')
change_paragraph('Rice provides a different and especially informative regime',
 'On Rice, the bootstrap intervals for all three B1−B0 F1 differences include zero. LR changes by −0.025 percentage points and retains 98.56% decision agreement, yet the mean original-point TV is 0.0159. It is a descriptive near-invariant-score example, not a fixed-function positive control. The positive control in the reproducibility archive explicitly composes the B0 predictor with the inverse coordinate map; discontinuous tree learners may show finite-precision threshold effects under this numerical round trip.')
change_paragraph('Table 5 provides descriptive means',
 'Table 5 gives fold means, sample SDs and ranges of six-block Spearman CCPI rank correlation. Dry Bean LR and HGB remain moderately negative (−0.543±0.081 and −0.474±0.063), whereas RF is near zero (−0.063±0.096). Rice HGB and RF are negative on average but exhibit greater fold variability; Rice LR is weakly positive. All six groups have high within-representation fold-pair rank consistency relative to lower cross-representation agreement (Table 5b), but these statistics are descriptive, not six independent replications or evidence of explainer error.')
change_paragraph('Exact chance calibration for top-three overlap',
 'Chance calibration for six blocks is essential: if two top-three subsets are sampled independently from six, the expected fractional overlap is 0.5 and Pr(overlap ≤ 1/3)=0.5. Accordingly, the observed 1/3 overlap in several settings is not individually remarkable against this combinatorial reference. The 2/3 overlap of Rice LR and native SHAP is also not evidence of transport without an appropriate baseline.')
change_paragraph('Exact rank-null calibration',
 'For a single fixed pair of six distinct rank permutations, exact enumeration of all 720 permutations yields a two-sided 5% rank-correlation threshold |ρ|≥0.886; no inference is made from averaging correlated fold Spearman coefficients. Reported fold SD and within-representation agreement provide context rather than independent-sample standard errors.')
change_paragraph('The minimum fold/block support rate exceeds',
 'Minimum block support across the executed folds is 98.12% for Dry Bean and 97.90% for Rice. Mean TV on original held-out observations is 0.0159–0.0627 (Table 4), and probability functions differ further on perturbed support. At the sample level, the triangle inequality gives |CCPI₁−CCPI₀|≤TV(original)+E[TV(perturbed)], with zero violations among 298,183 computed block-level diagnostics (up to floating-point tolerance). Observed Spearman associations of absolute CCPI drift with this local TV-bound quantity range from 0.581 to 0.897 across model–dataset groups; these associations are descriptive, not tests of model equivalence or causal mechanisms. The earlier broad 2ε uniform bound is mathematically valid but too loose here to demonstrate a close empirical fit.')
change_paragraph('The most reproducible result is block specific',
 'Table 6 aggregates 30 genuinely executed fold–model–dataset comparisons for each of six primitive blocks. Area and ConvexArea show B1>B0 CCPI in all 30 comparisons for each block, with mean signed changes +0.02987 and +0.02373. These comparisons are correlated by training data and model family and are not treated as independent Bernoulli trials. The repeated direction provides a descriptive reproducibility finding across these two datasets, not an interventional or causal explanation.')
change_paragraph('The block magnitudes make the effect concrete',
 'Table 7 provides the re-executed paired magnitude comparison. On deduplicated Dry Bean LR, mean Area CCPI rises from 0.00053 to 0.03765 and ConvexArea from 0.00070 to 0.03292; on Rice LR the corresponding pairs are 0.00054→0.01479 and 0.00293→0.01751. The complete 36-row mean±SD table is included as Appendix A, with all 180 individual fold–block records in the source archive. This resolves the inability to reconstruct rank statistics from the previous Area/ConvexArea-only table.')
change_paragraph('The LR SHAP comparator shows',
 'The newly recomputed LR linear-SHAP comparator confirms representation-specific native feature-credit rankings under the Table 1 pairing convention. Mean foldwise Spearman ρ is 0.406±0.031 for Dry Bean and 0.063±0.031 for Rice; top-three overlap is 2/3 in each dataset. Held-out Dry Bean LR permutation importance gives ρ=0.326±0.063 with top-three overlap 2/3 (Table 8). These values describe different coordinate-wise credits, and nonlinear derived coordinates have no uniquely matching primitive attribution; SHAP transport here does not test a fixed prediction function.')
change_paragraph('The experiments separate three statements',
 'The study separates (i) exact information equivalence by construction; (ii) high, but imperfect, hard-decision agreement; (iii) measurable mismatch between independently learned probability functions; and (iv) representation-dependent local physical sensitivity and native coordinate credits. In the new public-data run, original-point mean TV is strictly positive in every model–dataset group, and the local CCPI drift should therefore be attributed jointly to the choice of fitted model and coordinates, not to failure of an explainer with a fixed function.')
change_paragraph('The repeatable Area/ConvexArea response shift',
 'The Area/ConvexArea shift is consistent with changes in learned response surfaces and with how engineered features amplify or distribute one primitive-space intervention. In B1, ConvexArea affects solidity S=A/C; changing Area with other primitives fixed changes four derived coordinates. On average, maximum standardized B1 coordinate displacement for Area and ConvexArea perturbations is 0.96 and 0.94 training SD on Dry Bean, compared with 0.55 and 0.50 on Rice. Respectively 11.2% and 11.9% of these Dry Bean perturbations extend at least one B1 coordinate beyond its training-fold marginal min/max (Rice 2.0% and 2.9%). These are descriptive indicators of transformed-coordinate extrapolation, not a unique mechanistic proof.')
change_paragraph('The Dry Bean release contains 68 exact duplicate rows',
 'The public Dry Bean release contains 68 exact duplicate records. We reran a separate 13,611-row raw-release sensitivity analysis, using the same disclosed reconstruction settings, in addition to the 13,543-row deduplicated headline analysis. In both runs, Area and ConvexArea have positive B1−B0 CCPI shifts in 15/15 Dry Bean model–fold combinations each; absolute values differ modestly as documented in the raw-versus-deduplicated table. Because the raw random split may place identical samples across folds, the deduplicated result remains primary. This checks the persistence claim without presenting the raw run as leakage-free.')
change_paragraph('• The full 6×2 CCPI fold table',
 '• Appendix A reports the complete six-block B0/B1 mean and fold SD for all models and both datasets; all individual fold observations, probabilities and local-TV diagnostics are preserved in the accompanying reproducibility archive. This is an independent reconstruction, so historical hyperparameters not explicitly available in the original manuscript are declared as assumptions rather than retrospectively asserted as facts.')
change_paragraph('Analytically invertible morphology coordinates preserve',
 'Analytically invertible morphology coordinates preserve information about class labels, but the fitted functions of finite independently trained predictors need not coincide. Real-data five-fold reconstruction on Dry Bean and Rice confirms high decision agreement alongside nonzero probability TV and changes of shared-physical-space CCPI ranks. Area and ConvexArea increase in CCPI magnitude under B1 in all 30 correlated model–fold comparisons each. These changes cannot be interpreted as the failure of an explainer on an unchanged predictor.')
change_paragraph('The main finding is therefore not that SHAP',
 'The practical recommendation is to audit information equivalence, hard-decision agreement, probability-function transport and physically shared perturbation response separately. Native SHAP comparisons depend on a conventional pairing of composite and primitive features, and Top-3 overlap must be calibrated against chance. Public data and machine-verifiable code are provided in a locally packaged reproducibility bundle for external deposition and final author inspection; the paper does not claim an observed improvement in agricultural outcomes or SDG indicators.')
change_paragraph('The original sources are Dry Bean',
 'Data provenance: Dry Bean, UCI ID 602 (2020), DOI 10.24432/C50S4B, CC BY 4.0, and Rice (Cammeo and Osmancik), UCI ID 545 (2019), DOI 10.24432/C5MW4Z, CC BY 4.0; dataset pages accessed and checked 4 November 2026. Local frozen CSV source SHA-256: Dry Bean 912c87ef3aead267e52e1f95b794f431a367827224edf39f33b4a5193d122350; Rice 9d5e9f271b6ce6e644a33fdc4fd039b6d3f80dbc756aedc4fbe35d631457686a. Full input data, audit code, foldwise scores, SHAP/CCPI tables, OOF probabilities and discrepancy reports accompany this author-review draft.')
change_paragraph('The accompanying R2 local ZIP provides',
 'The accompanying archive is reproducible and versioned locally, but no public, immutable release URL or DOI has yet been minted. It must be deposited in an author-controlled publicly accessible repository with a fixed tag or DOI and linked here before claiming complete compliance with the reviewers’ open-archive requirement. No restricted or personal data are involved. The independent audit uses newly declared numerical configuration assumptions, not an authenticated copy of the historical authors’ complete software environment.')
change_paragraph('During revision of this author-review draft',
 'During revision on 4 November 2026, OpenAI ChatGPT (GPT-6) was used to suggest text revisions, bibliography/format checks, and computational reanalysis scripts, including quality-control tests. The datasets were not synthesized by AI, and figures and numerical tables were generated by executing deterministic Python programs on public data. The corresponding author must independently inspect the scientific statements, computations and use categories, confirm whether these uses satisfy the CEUR-WS generative-AI policy, and revise this declaration as necessary before submission. The human authors take sole responsibility for the work. [AUTHOR APPROVAL REQUIRED]')

# Resolve superseded cautionary language carried forward from the pre-reanalysis R2 manuscript.
change_paragraph('CCPI uses training-only donor search, shared primitive perturbations',
 'CCPI uses training-only donor search and ten accepted primitive-space draws per eligible sample and block. Rank transport is computed on each fold\'s six physical blocks; the complete 180 fold–block score vectors and 298,183 sample-block diagnostics are in the reproducibility archive. The six-item rank null is explicitly enumerated; differences across the five overlapping CV training sets are not independent-trial significance tests. SHAP 0.50.0, scikit-learn 1.8.0 and all random-seed choices are documented for this reconstruction, rather than projected back onto unknown historical settings.')
change_paragraph('Exact induced-coordinate dependency under the stated one-primitive-at-a-time kernel',
 'The transformation makes the feature coupling explicit: changing Area (A) alters Ed, R, Co and S; changing Perimeter (P) alters R only; changing MajorAxisLength (L) alters Co and AR; changing MinorAxisLength (l) alters AR only; changing ConvexArea (C) alters S only; and changing Extent (Ex) alters Ex only. The executed standardized B1-step and out-of-training-marginal-range diagnostics above empirically probe, but do not isolate causally, the mechanism behind the repeated Area/ConvexArea direction.')
change_paragraph('• The 2ε bound is a worst-case support-level statement',
 '• The 2ε bound is a uniform support-level statement and is loose relative to observed mean CCPI drift; empirical TV p95 is not a population-uniform bound. This paper now reports fold-level SDs and within-representation rank stability, but these remain descriptive under overlapping training folds. The independent reconstruction cannot establish exact historical numerical equivalence without the original private experiment logs and their full hyperparameters.')
# appendix before Data and Code Availability, after conclusion; full 36×6 mean SD
anchor=get_p('Data and Code Availability')
heading=mkpar('Appendix A. Complete six-block CCPI magnitudes and fold spread','P5')
parent.insertBefore(heading,anchor)
par=mkpar('All values below are means ± sample SD over five folds of the new UCI reconstruction. Fold-specific observations and support/TV diagnostics are retained as CSV files in the source archive. Rankings in Table 5 are computed from fold-level six-block vectors, not from a six-block mean vector.','P6')
parent.insertBefore(par,anchor)
cap=mkpar('Table A1. Per-model, per-dataset six-block CCPI in B0/B1, with fold SD; Δ=B1−B0.','P11')
parent.insertBefore(cap,anchor)
rows=[['Dataset','Model','Block','B0 mean±SD','B1 mean±SD','Δ mean±SD']]
for ds,m in order:
 for b in ['Area','Perimeter','MajorAxisLength','MinorAxisLength','ConvexArea','Extent']:
  g=block[(block.dataset==ds)&(block.model==m)&(block.block==b)].iloc[0]
  short={'Area':'Area','Perimeter':'Perimeter','MajorAxisLength':'Major axis','MinorAxisLength':'Minor axis','ConvexArea':'Convex area','Extent':'Extent'}[b]
  rows.append([pretty(ds),m,short,f'{g.b0_mean:.4f}±{g.b0_sd:.4f}',f'{g.b1_mean:.4f}±{g.b1_sd:.4f}',f'{g.signed_diff_mean:+.4f}±{g.signed_diff_sd:.4f}'])
newtab=clone(T7tmp);newtab.setAttribute('name','AppendixA1_R5')
oldrows=newtab.getElementsByType(table.TableRow);header=clone(oldrows[0]);data=clone(oldrows[1]);
for e in list(newtab.childNodes):
 if e.qname[1] in ('table-row','table-header-rows','table-rows','table-row-group'):newtab.removeChild(e)
for i,row in enumerate(rows):
 r=clone(header if i==0 else data)
 for c,v in zip([c for c in r.childNodes if c.qname[1]=='table-cell'],row):
  p=c.getElementsByType(text.P)[0];st=p.getAttribute('stylename')
  for e in list(c.childNodes):c.removeChild(e)
  c.addElement(text.P(stylename=st,text=str(v)) if st else text.P(text=str(v)))
 if i==0:
  h=table.TableHeaderRows();h.addElement(r);newtab.addElement(h)
 else:newtab.addElement(r)
parent.insertBefore(newtab,anchor)

# replace figure 1 embedded PNG in ODT container, keep single column and original size
lab=['Bean HGB','Bean LR','Bean RF','Rice HGB','Rice LR','Rice RF']
pts=[boot[(boot.dataset==ds)&(boot.model==m)].iloc[0] for ds,m in order]
mu=np.array([v.paired_dF1_pp for v in pts]);lo=np.array([v.CI_low_pp for v in pts]);hi=np.array([v.CI_high_pp for v in pts]);
fig,ax=plt.subplots(figsize=(8.0,4.45));x=np.arange(len(lab)); ax.errorbar(x,mu,yerr=[mu-lo,hi-mu],fmt='o',capsize=3);ax.axhline(0,linewidth=1);ax.set_xticks(x,lab,rotation=26,ha='right');ax.set_ylabel('B1 − B0 OOF macro-F1 (percentage points)');ax.set_title('Paired public-data reconstruction: 1,000-bootstrap 95% intervals');ax.grid(axis='y',alpha=0.3);fig.tight_layout()
figpath=dest/'Figure1_R5_paired_F1_CI.png';fig.savefig(figpath,dpi=205);plt.close(fig)

outodt=dest/'ExplAI2026_P14_R5_PUBLIC_DATA_AUTHOR_REVIEW.odt'
doc.save(str(outodt))
# Replace ODT picture file of first figure with reproducible new plot
with ZipFile(outodt,'r') as inp:
 xml=inp.read('content.xml').decode('utf8')
 import re
 hrefs=re.findall(r'xlink:href="(Pictures/[^"]+)"',xml)
 if not hrefs: raise RuntimeError('No figure link found')
 figHref=hrefs[0]
 replaced=outodt.with_suffix('.replaced.odt')
 with ZipFile(replaced,'w') as oz:
  for inf in inp.infolist():
   if inf.filename==figHref: oz.writestr(inf,figpath.read_bytes())
   else:oz.writestr(inf,inp.read(inf.filename))
replaced.replace(outodt)
print('ODT:',outodt,'figure:',figHref,'rows appendix',len(rows), 'doc paragraphs',len(parent.childNodes))
