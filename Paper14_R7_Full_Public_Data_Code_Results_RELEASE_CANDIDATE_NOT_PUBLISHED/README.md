# ExplAI-2026 Paper 14 — R7 independent public-data reconstruction

## Public availability
This scientific reproducibility folder is **public on GitHub** at `hezejuyede/ExplAI-2026-Paper14`. Its historical name ending in `RELEASE_CANDIDATE_NOT_PUBLISHED` came from the original local ZIP and does not reflect the present GitHub visibility. A full Git commit SHA provides an immutable snapshot; a separately named GitHub Release or DOI is not yet asserted.

## Scientific scope
This archive documents a new, independently executed reanalysis of UCI Dry Bean (13,611 raw / 13,543 after 68 exact duplicates) and Rice (Cammeo/Osmancik; 3,810 observations). It **does not** claim to match the original October 2026 manuscript environment bit-for-bit: missing historical algorithm settings were chosen and documented for the new runs. Differences from earlier numerical reports remain in `results/discrepancy/`.

## Materials
- `data/`: two frozen CSVs with documented SHA-256 source hashes;
- `scripts/`: executable Python reconstruction, statistical summaries and audit tests;
- `results/real_reconstruction/`: 180 fold–block CCPI records, 52,059 out-of-fold model/sample predictions and saved sample/block diagnostics;
- `results/derived/`: fold-wise rank stability, mean original-point TV, full six-block summaries and bootstrap intervals;
- `results/extended/`: SHAP and permutation comparators, model-preserving check and B1 transformed-coordinate perturbation diagnostics;
- `results/raw_sensitivity/`: deduplicated versus full-release Dry Bean analysis;
- `results/discrepancy/`: transparent comparisons with the historical draft;
- `provenance/`: saved execution logs and *historical* audit states. Some old status flags predate publication to GitHub.

## Run

Use Python 3.13 and run the following from this directory:

```bash
python -m pip install -r requirements.txt
python VERIFY_EXISTING_RESULTS.py
```

To rerun full CCPI, use `bash RUN_REAL_UCI_UNIX.sh` or `RUN_REAL_UCI_WINDOWS.bat`. The program creates a new `NEW_REPRODUCTION/` output directory rather than overwriting frozen results.

## Attribution and rights
UCI Dry Bean (https://doi.org/10.24432/C50S4B) and UCI Rice (https://doi.org/10.24432/C5MW4Z) are CC BY 4.0 datasets. Retain original provenance and attribution. Code/paper licensing remains subject to rightsholders' approval; GitHub public visibility alone does not grant additional software-license permissions.
