from pathlib import Path
import hashlib, pandas as pd
root=Path(__file__).parent
sha={'Dry_Bean_Dataset.csv':'912c87ef3aead267e52e1f95b794f431a367827224edf39f33b4a5193d122350','Rice_Osmancik_Cammeo_Dataset.csv':'9d5e9f271b6ce6e644a33fdc4fd039b6d3f80dbc756aedc4fbe35d631457686a'}
for fn, expected in sha.items():
 assert hashlib.sha256((root/'data'/fn).read_bytes()).hexdigest()==expected
fold=pd.read_csv(root/'results/real_reconstruction/fold_ccpi.csv')
oof=pd.read_csv(root/'results/real_reconstruction/oof_probabilities.csv')
assert len(fold)==180 and len(oof)==52059
assert all(fold.max_sample_tv_bound_violation==0)
for block in ['Area','ConvexArea']:
 s=fold[fold.block==block];assert len(s)==30 and sum(s.ccpi_b1>s.ccpi_b0)==30
print('Input SHA256, 180 fold CCPI rows, 52,059 OOF rows, 30/30 size shifts and 0 bound violations VERIFIED')
