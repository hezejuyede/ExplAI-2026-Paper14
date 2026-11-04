# ExplAI-2026 Paper 14 — R7 independent public-data replication and author review package

## Scope
The files present an independently executed computational audit of UCI Dry Bean (13,611 raw, 13,543 unique) and Rice Cammeo/Osmancik (3,810) data. Dataset versions are frozen with SHA-256. The R7 results are **not** claimed to be byte-identical to the originally submitted October 2026 analysis. The original parameters not recorded in the historical draft were selected and disclosed for this reconstruction. The full discrepancy spreadsheets remain available under `results/discrepancy/`.

## Reproduction
Install `requirements.txt`; run the Windows/Unix driver with the frozen CSVs; run `VERIFY_EXISTING_RESULTS.py`. The `results` tree stores actual executed OOF probabilities (52,059 model-sample pairs), 180 model-fold-block CCPI cells, original-point TV, bootstrap F1 uncertainty, exact random-rank chance, per-fold stability, SHAP and LR permutation, model-preserving control, raw-vs-deduplicated Dry Bean and diagnostic records.

## Author/release state
This is a completed **technical research package** but a **human-review publication candidate**, not a final CMT submission. A public DOI has **not** been minted; this ZIP is a candidate for upload to a public repository. Its internal hashes authenticate local bits but are not a persistent internet URL. The CEURART official source template has not been obtained for direct comparison. A wet-ink signed agreement, author approval and presenter identification require the human authors. The AI declaration in the manuscript acknowledges use of AI assistance but must be reviewed by the authors against actual use.

## License and attribution
UCI Dry Bean DOI 10.24432/C50S4B and UCI Rice DOI 10.24432/C5MW4Z were publicly released with CC BY 4.0 attribution. Keep both original dataset attributions. Code/paper publication licensing requires the rightsholders' human approval; this ZIP is not a grant of additional ownership rights by the AI assistant.
