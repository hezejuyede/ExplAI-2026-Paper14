#!/usr/bin/env bash
set -euo pipefail
python scripts/reconstruct_real_public.py --dry-bean data/Dry_Bean_Dataset.csv --rice data/Rice_Osmancik_Cammeo_Dataset.csv --outdir NEW_REPRODUCTION --lr-c 1.0 --hgb-learning-rate 0.1 --draws 10 --n-jobs 2 --sample-diagnostics
python scripts/reanalyse_from_logs.py --fold-csv NEW_REPRODUCTION/fold_ccpi.csv --oof-csv NEW_REPRODUCTION/oof_probabilities.csv --outdir NEW_REPRODUCTION/derived_tables
