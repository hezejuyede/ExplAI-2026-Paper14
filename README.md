# ExplAI-2026 Paper 14 — public reproducibility archive

**Paper:** *Do XAI Explanations Survive Information-Equivalent Coordinates? A Cross-Dataset Morphometric Audit*  
**Authors:** Xin Li, Bojian Guo, Asel Kartanova

The code, frozen data and independently executed results are available in [the R7 reproducibility folder](./Paper14_R7_Full_Public_Data_Code_Results_RELEASE_CANDIDATE_NOT_PUBLISHED/). The historical folder suffix `RELEASE_CANDIDATE_NOT_PUBLISHED` names the original local bundle; **the contents are now publicly accessible in this GitHub repository**.

## Contents
- `data/`: Dry Bean and Rice frozen UCI CSV sources.
- `scripts/`: reproducible computational and statistical audit scripts.
- `results/real_reconstruction/`: actual five-fold CCPI and out-of-fold predictions, with sample-level diagnostics.
- `results/derived/`, `extended/`, `raw_sensitivity/`, `discrepancy/`: fold SDs, original-point TV, SHAP, raw-versus-deduplicated tests and explicit historical-vs-reconstruction discrepancies.
- `provenance/`: execution logs and historical QC reports; `requirements.txt`, `CITATION.cff` and verification scripts.

## Verify and reproduce
From the nested reproducibility folder, install Python 3.13 dependencies:

```bash
python -m pip install -r requirements.txt
python VERIFY_EXISTING_RESULTS.py
```

For a full rerun use `bash RUN_REAL_UCI_UNIX.sh` (Linux/macOS) or `RUN_REAL_UCI_WINDOWS.bat` (Windows). Full reconstruction can be computationally expensive.

## Data sources and interpretation
- UCI Dry Bean (2020): https://doi.org/10.24432/C50S4B — CC BY 4.0.
- UCI Rice (Cammeo/Osmancik) (2019): https://doi.org/10.24432/C5MW4Z — CC BY 4.0.

This repository records a **new, independent public-data reconstruction** with fully disclosed hyperparameter assumptions. It is **not a claim of bitwise reproduction** of the original submitted experiment. Please review `results/discrepancy/` before comparing metrics.

## Versioned release (published 4 November 2026)

- **GitHub Release:** https://github.com/hezejuyede/ExplAI-2026-Paper14/releases/tag/v1.0.0
- **Pinned release commit:** `6e41b9a461217a4865b7dc49940c600acd59ea42`
- **Exact snapshot:** https://github.com/hezejuyede/ExplAI-2026-Paper14/tree/6e41b9a461217a4865b7dc49940c600acd59ea42/Paper14_R7_Full_Public_Data_Code_Results_RELEASE_CANDIDATE_NOT_PUBLISHED

The Release tag points to the above commit, providing a versioned archive. The full commit SHA identifies the exact content even if the moving `main` branch changes. No DOI has been minted. Private author agreements are not part of the public repository; older status flags in `provenance/` describe historical local bundle states.
