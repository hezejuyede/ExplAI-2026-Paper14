from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

out=Path(__file__).resolve().parent.parent/'response'; out.mkdir(exist_ok=True)

def style_document(doc):
 sec=doc.sections[0];sec.top_margin=Inches(.78);sec.bottom_margin=Inches(.70);sec.left_margin=Inches(.85);sec.right_margin=Inches(.85)
 sec.page_height=Inches(11.69);sec.page_width=Inches(8.27)
 normal=doc.styles['Normal'];normal.font.name='Liberation Serif';normal.font.size=Pt(10.5)
 normal.paragraph_format.space_after=Pt(5)
 for s,sz in [('Title',16),('Heading 1',13),('Heading 2',11)]:
  st=doc.styles[s];st.font.name='Liberation Sans';st.font.size=Pt(sz);st.font.bold=True

def add_point(doc, reviewer, n, title, status, evidence, response):
 doc.add_heading(f'{reviewer}.{n}  {title}',level=2)
 p=doc.add_paragraph();r=p.add_run(f'Status: {status}');r.bold=True
 p=doc.add_paragraph(f'Revision: {response}')
 p=doc.add_paragraph(f'Evidence / location: {evidence}');p.style=doc.styles['Normal']

responses={
'R1':[
(1,'Rank stability and null calibration','Addressed in independent rerun','Tables 5 and 5b; fold-level rank CSV; 720-permutation exact null','Reported fold SD/range, B0/B1 ten fold-pair mean Spearman correlations and top-three chance expectation 0.5. Explained that observed 1/3 overlap has exact null Pr(overlap≤1/3)=0.5 and is not evidence of significance.'),
(2,'Nonunique SHAP block pairing and B0-defined CCPI','Addressed','Abstract; Sections 4, 6.4, 7.6','Clarified that composite B1 coordinates mix primitives; Table 1 correspondences are conventional, and the conditional kernel is defined in B0. Native SHAP ranking differences do not imply failure for an unchanged function.'),
(3,'Loose 2ε inequality; empirical TV–drift association','Addressed descriptively','Section 4.3, Section 6.2; sample_TV_drift_diagnostics.csv','Retained 2ε as a worst-case statement, removed claims of empirical tightness, reported local sample-specific TV bound and 298,183 verified diagnostics (0 violations). Descriptive Spearman associations range 0.581–0.897; overlapping samples are not independent tests.'),
(4,'Six-block appendix, max drift and raw duplicates','Addressed','Appendix A, Tables 5b/7; 180-row fold_ccpi.csv; raw-vs-dedup CSV','Added all six blocks × three models × two datasets as mean±fold SD; included complete fold-level records. Table 5b reports maximum absolute foldwise block drift. Independently reran all 13,611 Dry Bean rows vs 13,543 deduplicated; positive Area/ConvexArea directions persist 15/15 in each run.'),
(5,'Conditional-feature importance prior literature','Addressed','Section 2.2; Refs [18,21–24,27–28,30–33]','Explicitly linked CCPI with Strobl, Watson–Wright, Molnar, Hooker, Kindermans, variable-importance clouds and underspecification. CCPI is characterized as one shared physically defined kernel applied to separately fitted representations—not a first conditional importance method.'),
(6,'Software settings, versions, reproducibility, datasets','Partly addressed; public deposit pending','Sections 5.2–5.3; Data and Code Availability; SHA256 / provenance manifest','Documented Python, NumPy, SciPy, pandas, sklearn and SHAP versions; LR L2/C=1, HGB rate=0.1, paired seeds, ten CCPI draws and 1,000 paired bootstrap resamples for the new independently run audit. Input SHA-256, CC BY 4.0 attribution and UCI source years recorded. Public persistent GitHub/Zenodo URL must still be created by the corresponding author.'),
(7,'Coordinate-shift mechanism (suggested)','Addressed descriptively','Section 7.2; B1_geometry_support_mechanism.csv','Reported exact induced B1-coordinate changes and actual perturbation step sizes in training-SD units, together with out-of-marginal-range frequencies; no causal mechanism asserted.'),
(8,'Figures and mathematics (suggested)','Partly addressed','Figure 1 refreshed; redundant rank figures omitted','Rebuilt paired F1 interval figure from newly executed bootstrap outputs; avoided duplicative bar charts. Equations remain readable symbolic text and are not yet official CEURART numbered formula objects.'),
(9,'CEURART A4/Libertinus and legal footnotes','Partly addressed; template certification pending','Final PDF preflight; first-page footnotes','The 12-page PDF uses A4 and embedded Libertinus Serif/Sans. Author and event lines and copyright are restored. This ODT has not been directly transplanted into the organizer-hosted official ODT template; that final template conformity check remains required.'),
(10,'References and SDG context','Addressed subject to bibliographic author check','Reference section, Sections 1 and 7.4','Numbered 33 references in first citation order, included UCI years/licenses, restored relevant DOI data, cited model/bootstrap methods in Section 5 and named the UN 2030 Agenda/SDG 2.4/12.3. Authors should spot-check each external bibliographic record.'),
(11,'DBLP paper threshold','Waived by chair decision','Decision email 3 November 2026','The chairs explicitly stated this comment is not a condition of acceptance; no new author or claim was added.')],
'R2':[
(1,'Original held-out mean TV and narrower interpretation','Addressed','Table 4, abstract and conclusion','Mean original-point TV is 0.0358/0.0627/0.0539 on Dry Bean LR/RF/HGB and 0.0159/0.0397/0.0493 on Rice. The manuscript distinguishes fitted-function change from attribution-method error.'),
(2,'Chance-calibrated rank statistics','Addressed','Tables 5,5b; exact rank enumeration','Five-fold SD and ranges, 0.5 random top-three baseline and exact six-block 5% permutation cutoff |ρ|≥0.886 provided; no independent-trial p-values claimed.'),
(3,'Prior art conditional importance','Addressed','Section 2.2','Explicitly positioned shared-coordinate CCPI against the conditional importance/predictive impact/extrapolation/input-invariance literature; avoided novelty overclaim.'),
(4,'Standardized perturbation and off-range diagnostics','Addressed descriptively','Section 7.2; B1_geometry_support_mechanism.csv','Measured maximal B1 coordinate displacement in B1 training-SD units and fractions outside training minima/maxima. Dry Bean Area/ConvexArea ~0.96/0.94 SD and 11.2%/11.9% out-of-range; Rice ~0.55/0.50 SD and ~2.0%/2.9%.'),
(5,'Fixed-function positive control and common-coordinate SHAP (optional)','Partly addressed; optional extension remains','model_preserving_positive_control.csv','Evaluated inverse-composed B0 model on held-out examples and Area perturbations. LR/RF gaps are at numerical precision; HGB exhibits isolated floating-point threshold artifacts (max original-point discrepancy 0.0101 on Rice). Did not claim a complete shared-primitive SHAP run for all models.'),
(6,'Versions, data integrity, signed archive','Partly addressed; public versioned URL pending','Sections 5.2–5.3, Section 7.5, Data and Code Availability','Performed independent live UCI source-file run (not merely synthetic smoke test), reported all required versions/seeds and raw-vs-dedup sensitivity. Archive and hashes prepared locally; immutable public deposit still requires an author-controlled account.'),
(7,'Figure revisions and equation typesetting (optional)','Partly addressed','Figure 1; Sections 3–4','Replaced F1 plot using the new bootstrap confidence intervals; tables report fold dispersions. Mathematical expressions retained as readable notation, not official numbered equation objects.'),
(8,'UN SDG agenda','Addressed','Sections 1 and 7.4, Ref [17]','Added UN resolution A/RES/70/1 and targets 2.4/12.3, clearly limited to enabling reliability rather than measured SDG benefits.'),
(9,'In-text citations, DOI and ordered bibliography','Addressed subject to author check','Section 5; References','Breiman, Friedman, Pedregosa and Efron–Tibshirani are cited at relevant methods; unused references removed; all remaining references in first-citation order.'),
(10,'A4 CEURART official one-column with required footnotes','Partly addressed; template certification pending','R5 PDF preflight; organizer CEURART template link','A4, correct year/event line and embedded Libertinus fonts verified. Exact official ODT master template equivalence has not been verified due inaccessible Drive template bytes.'),
(11,'DBLP author threshold','Waived by chair decision','Decision email 3 November 2026','Chair email clarifies that this item is not a condition; no action needed.')]
}
doc=Document();style_document(doc)
p=doc.add_paragraph('ExplAI-2026 · Paper 14');p.style='Subtitle'
doc.add_heading('Point-by-Point Response to Reviewers',level=0)
doc.add_paragraph('Manuscript: Do XAI Explanations Survive Information-Equivalent Coordinates? A Cross-Dataset Morphometric Audit')
doc.add_paragraph('Author-review draft · 4 November 2026 · Scientific computations on frozen public UCI data; final author approval is required before uploading.')
doc.add_heading('Overview of evidence added',level=1)
doc.add_paragraph('We completed a separately labeled five-fold public-data reconstruction on Dry Bean (13,543 deduplicated observations) and Rice (3,810 observations) using three model families, two invertible representations and 10 CCPI draws per supported case/block. We added original-point TV, paired macro-F1 uncertainty, 180 per-fold CCPI records, six-block mean±SD tables, fold rank agreement, a uniform-rank combinatorial null, raw-release sensitivity, sample-level TV bounds, linear SHAP and permutation comparators. Method settings not documented in the original version are identified as reconstruction assumptions; the original results and new run are contrasted rather than silently conflated.')
doc.add_paragraph('Important: the revised author-review PDF is not yet an unconditional CEURART camera-ready submission. An official template comparison, an author-controlled public immutable archive URL, a hand-signed CEUR agreement and all authors’ approval remain to be completed. The chairs waived the separate DBLP publication-count comment.')
for reviewer in ['R1','R2']:
 doc.add_heading(f'Comments from Reviewer {1 if reviewer=="R1" else 2}',level=1)
 for n,title,status,evidence,response in responses[reviewer]:add_point(doc,reviewer,n,title,status,evidence,response)
doc.add_heading('Reconstruction provenance and version policy',level=1)
doc.add_paragraph('The file SHA-256 digests, implementation source, executed fold scores, OOF probabilities, per-observation CCPI diagnostics, SHAP log and comparison against the historical manuscript are enclosed in the R5 reproducibility archive. Model choices explicitly declared as assumptions are not represented as verified historical hyperparameters. All empirical tables in the R5 manuscript use one consistent newly executed reconstruction.')
doc.add_paragraph('The present response must be checked against the reviewer reports and manuscript by the human authors, who remain responsible for the underlying science and the accuracy of the Declaration on Generative AI.')
response_docx=out/'P14_R5_POINT_BY_POINT_AUTHOR_REVIEW.docx';doc.save(response_docx)

# Compact actual three-file CMT modification summary
short=Document();style_document(short);short.add_heading('ExplAI-2026 Paper 14 — Summary of Changes',0)
short.add_paragraph('Paper: Do XAI Explanations Survive Information-Equivalent Coordinates? A Cross-Dataset Morphometric Audit')
short.add_paragraph('Authors: Xin Li, Bojian Guo, Asel Kartanova | Corresponding author: Xin Li | Prepared: 4 November 2026')
short.add_heading('Scientific revisions',level=1)
for s in [
'Executed a fully traceable independent UCI five-fold reconstruction (13,543 deduplicated Dry Bean samples; 3,810 Rice samples; LR, RF, HGB) and reconciled numeric differences against the original submission.',
'Updated paired OOF macro-F1 / bootstrap 95% intervals and added mean held-out probability total-variation (TV) distance to Table 4. Rewrote abstract, discussion and conclusion to avoid describing probability-function divergence as fixed-function explainer failure.',
'Added fold SD/range, chance-calibrated top-three overlap, ten-pair within-B0/B1 fold-rank agreement and maximum absolute block drift (Tables 5–5b). Appendix A now reports full six-block CCPI mean±SD; 180 detailed fold/block records are in the reproducibility files.',
'Checked a local TV–CCPI inequality against 298,183 sample-block records (no violations), added numerical SHAP/permutation reruns, a model-preserving control, and raw-versus-deduplicated Dry Bean sensitivity.',
'Added conditional importance/extrapolation/model-multiplicity literature, reproducible versions/seeds/regularization settings, source licenses, source hashes, data/code availability limitations, UN SDG references and a truthful author-review generative-AI disclosure.'
]: short.add_paragraph(s,style='List Bullet')
short.add_heading('Format and final compliance',level=1)
short.add_paragraph('A4 single-column PDF, Libertinus fonts embedded, restored authors and first-page event/copyright notes; PDF length 12 pages. The final author-signed CEUR agreement must accompany upload. The locally versioned code/data ZIP still needs an author-controlled immutable public deposit link; final official template conformity and AI disclosure must be checked by all authors. The DBLP-count comment was expressly waived by the chairs.')
short.add_paragraph('This summary accompanies the revised PDF for chair review; it does not claim that author-dependent actions are complete.')
short_path=out/'P14_R5_CMT_SHORT_SUMMARY_OF_CHANGES_AUTHOR_REVIEW.docx';short.save(short_path)

# Agreement guidance DOCX
ag=Document();style_document(ag);ag.add_heading('ExplAI-2026 Paper 14 · Author Agreement Completion',0)
ag.add_paragraph('Obtain the CURRENT ExplAI-2026 CEUR-WS NTP author agreement directly from the organizer’s website. Use the TP form instead only when permissioned third-party copyrighted content is reused in the paper.')
ag.add_paragraph('Exact title: Do XAI Explanations Survive Information-Equivalent Coordinates? A Cross-Dataset Morphometric Audit')
ag.add_paragraph('Author names in order: Xin Li; Bojian Guo; Asel Kartanova. Corresponding author: Xin Li.')
ag.add_paragraph('Print the agreement, fill in the paper details, and SIGN BY HAND IN INK (not a typed/electronic signature). Scan the entire completed form to PDF or JPEG. Confirm it matches exactly the authors and paper title appearing in CMT and the final manuscript.')
ag.add_paragraph('Official current form: https://drive.google.com/file/d/1VERSqTnCfOOI6T5enp-yl3Ziovsih4p5/view?usp=sharing')
ag.add_paragraph('The agreement is NOT included as signed in any delivered archive; no signature has been fabricated.')
ag.save(out/'P14_R5_CEUR_WET_INK_SIGNATURE_GUIDE.docx')
print(response_docx,short_path)
