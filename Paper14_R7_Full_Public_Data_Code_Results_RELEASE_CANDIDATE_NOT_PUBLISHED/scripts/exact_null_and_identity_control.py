#!/usr/bin/env python3
"""Exact finite six-block null and an algorithmic identity-control TEST.

No real UCI observations are accessed. All manufactured vectors are solely
pre-specified unit-test fixtures and MUST NOT be reported as real-data evidence.
"""
import itertools, csv, json, math
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parent

def forward(x):
    a,p,L,l,C,ex=np.asarray(x).T
    ed=np.sqrt(4*a/np.pi)
    return np.column_stack([ed,4*np.pi*a/p**2,ed/L,L/l,a/C,ex])

def inverse(z):
    ed,r,co,ar,s,ex=np.asarray(z).T
    a=np.pi*ed**2/4
    return np.column_stack([a,np.sqrt(4*np.pi*a/r),ed/co,ed/co/ar,a/s,ex])

def null_top3():
    return [{'shared':k,'fraction':k/3,'probability':math.comb(3,k)*math.comb(3,3-k)/20}
             for k in range(4)]

def null_spearman():
    basis=np.arange(6)
    rhos=np.array([spearmanr(basis,p).statistic for p in itertools.permutations(range(6))]);
    vals,counts=np.unique(np.round(rhos,12),return_counts=True)
    return [{'rho':float(v),'count':int(count),'p_exact_two_sided':float(np.mean(np.abs(rhos)>=abs(v)-1.e-11))}
            for v,count in zip(vals,counts)]

def softmax(a):
    a=np.asarray(a);b=np.exp(a-np.max(a,axis=-1,keepdims=True));return b/b.sum(axis=-1,keepdims=True)

def original_p(x):
    x=np.asarray(x)
    a,p,L,l,C,ex=x.T
    # Arbitrary FIXTURE function. This is NOT fitted and NOT an empirical classifier.
    return softmax(np.column_stack([(a-100)/25+3*ex, (p-40)/10+(C-110)/40, L/20-l/20]))

def composite_p(z):return original_p(inverse(z))

def run():
    x=np.array([[100,40,15,9,110,.7],[112,43,16,9.8,124,.75],
                [90,37,13.5,8,103,.65],[119,45,16.5,10.2,134,.62]],float)
    xprime=[]
    for row in x:
        for j in range(6):
            v=row.copy();v[j]*=1.002 if j<5 else 0.999
            xprime.append(v)
    xprime=np.asarray(xprime)
    z=forward(x);zp=forward(xprime)
    inv_error=np.max(np.abs(inverse(z)-x))
    original_gap=np.max(np.abs(original_p(x)-composite_p(z)))
    pert_gap=np.max(np.abs(original_p(xprime)-composite_p(zp)))
    assert inv_error<1.e-10 and original_gap<1.e-10 and pert_gap<1.e-10
    # Exact CCPI identity: when both predictors equal the same composed function,
    # their absolute response under identical primitive perturbations is equal.
    ccpi0=np.abs(original_p(xprime)-original_p(np.repeat(x,6,axis=0)))
    ccpi1=np.abs(composite_p(zp)-composite_p(np.repeat(z,6,axis=0)))
    ccpi_gap=float(np.max(np.abs(ccpi0-ccpi1)))
    assert ccpi_gap<1.e-10
    top=null_top3();spearman=null_spearman()
    with open(ROOT/'EXACT_top3_null.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=top[0].keys());w.writeheader();w.writerows(top)
    with open(ROOT/'EXACT_sixblock_spearman_null.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=spearman[0].keys());w.writeheader();w.writerows(spearman)
    const={
      'status':'ANALYTIC + SYNTHETIC UNIT TEST ONLY; NO UCI EMPIRICAL RESULT',
      'permutations_enumerated':720,
      'expected_top3_fraction':sum(q['fraction']*q['probability'] for q in top),
      'P_overlap_at_most_one':sum(q['probability'] for q in top[:2]),
      'P_overlap_equals_two':top[2]['probability'],
      'rho_two_sided_5pct_threshold':min(abs(q['rho']) for q in spearman if q['p_exact_two_sided']<=.05),
      'inverse_map_max_absolute_error_unit_test':float(inv_error),
      'original_probability_max_absolute_gap_unit_test':float(original_gap),
      'perturbed_probability_max_absolute_gap_unit_test':float(pert_gap),
      'ccpi_max_absolute_gap_unit_test':ccpi_gap,
      'note':'The identity check is a numerical verification of a mathematically composed function. It is not independent evidence that the original separately trained B0 and B1 models coincide.'}
    (ROOT/'EXACT_ANALYTICAL_CHECKS.json').write_text(json.dumps(const,indent=2),encoding='utf-8')
    print(json.dumps(const,indent=2))

if __name__=='__main__':run()
