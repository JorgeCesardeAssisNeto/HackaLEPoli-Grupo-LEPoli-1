# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import pyreadstat
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score, r2_score, mean_absolute_error

print("Testing all 3 models implementation...")

# 1. Test Metabolic Model
demo = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_DEMO.xpt'))[0][['SEQN', 'RIDAGEYR', 'RIAGENDR']]
bpx = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_BPXO.xpt'))[0]
bmx = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_BMX.xpt'))[0][['SEQN', 'BMXBMI']]
slq = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_SLQ.xpt'))[0][['SEQN', 'SLD012', 'SLQ030', 'SLQ040', 'SLQ120']]
paq = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_PAQ.xpt'))[0][['SEQN', 'PAD680']]
ghb = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_GHB.xpt'))[0][['SEQN', 'LBXGH']]
glu = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_GLU.xpt'))[0][['SEQN', 'LBXGLU']]
cbc = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_CBC.xpt'))[0][['SEQN', 'LBXHCT', 'LBXRBCSI', 'LBXHGB', 'LBXWBCSI', 'LBDNENO']]
hscrp = pyreadstat.read_xport(_os.path.join(_paths.NHANES_DATA_DIR, 'P_HSCRP.xpt'))[0][['SEQN', 'LBXHSCRP']]

bpx['sys_avg'] = bpx[['BPXOSY1', 'BPXOSY2', 'BPXOSY3']].mean(axis=1)
bpx['dia_avg'] = bpx[['BPXODI1', 'BPXODI2', 'BPXODI3']].mean(axis=1)
bpx['pulse_avg'] = bpx[['BPXOPLS1', 'BPXOPLS2', 'BPXOPLS3']].mean(axis=1)

df = demo.merge(bpx[['SEQN', 'sys_avg', 'dia_avg', 'pulse_avg']], on='SEQN')
df = df.merge(bmx, on='SEQN').merge(slq, on='SEQN', how='left').merge(paq, on='SEQN', how='left')
df = df.merge(ghb, on='SEQN', how='left').merge(glu, on='SEQN', how='left')
df = df.merge(cbc, on='SEQN', how='left').merge(hscrp, on='SEQN', how='left')

print("Unified dataset ready. Rows:", len(df))

# --- MODEL 1: METABOLIC ---
feats_m1 = ['SLD012', 'PAD680', 'pulse_avg', 'BMXBMI', 'RIDAGEYR', 'RIAGENDR']
df['SLD012_m'] = df['SLD012'].fillna(df['SLD012'].median())
df['PAD680_m'] = df['PAD680'].fillna(df['PAD680'].median())
df['BMXBMI_m'] = df['BMXBMI'].fillna(df['BMXBMI'].median())
df['pulse_m'] = df['pulse_avg'].fillna(df['pulse_avg'].median())
feats_m1_c = ['SLD012_m', 'PAD680_m', 'pulse_m', 'BMXBMI_m', 'RIDAGEYR', 'RIAGENDR']

df['target_hba1c_risk'] = np.where(df['LBXGH'].isna(), np.nan, np.where(df['LBXGH'] >= 5.7, 1.0, 0.0))
sub_m1 = df[feats_m1_c + ['target_hba1c_risk', 'LBXGH']].dropna()
m1_clf = HistGradientBoostingClassifier(random_state=42).fit(sub_m1[feats_m1_c], sub_m1['target_hba1c_risk'])
m1_reg = HistGradientBoostingRegressor(random_state=42).fit(sub_m1[feats_m1_c], sub_m1['LBXGH'])
auc_m1 = roc_auc_score(sub_m1['target_hba1c_risk'], m1_clf.predict_proba(sub_m1[feats_m1_c])[:, 1])
r2_m1 = r2_score(sub_m1['LBXGH'], m1_reg.predict(sub_m1[feats_m1_c]))
print(f"Model 1 Metabolic: AUC = {auc_m1:.3f}, Continuous HbA1c R2 = {r2_m1:.3f}")

# --- MODEL 2: APNEA / NOCTURNAL HYPOXIA ---
# Target: Stops breathing (SLQ040 in [1,2,3]) OR (Frequent snoring SLQ030 >= 2 AND excessive daytime sleepiness SLQ120 >= 3)
valid_slq = df[(df['SLQ040'].isin([0, 1, 2, 3])) & (df['SLQ030'].isin([0, 1, 2, 3]))].copy()
valid_slq['target_apnea'] = np.where(
    (valid_slq['SLQ040'] >= 1) | ((valid_slq['SLQ030'] >= 2) & (valid_slq['SLQ120'] >= 3)), 1.0, 0.0
)
feats_m2 = ['LBXHCT', 'LBXRBCSI', 'LBXHGB', 'BMXBMI', 'sys_avg', 'dia_avg', 'RIDAGEYR', 'RIAGENDR']
sub_m2 = valid_slq[feats_m2 + ['target_apnea']].dropna()
m2_clf = HistGradientBoostingClassifier(random_state=42).fit(sub_m2[feats_m2], sub_m2['target_apnea'])
auc_m2 = roc_auc_score(sub_m2['target_apnea'], m2_clf.predict_proba(sub_m2[feats_m2])[:, 1])
print(f"Model 2 Apnea/Hypoxia: AUC = {auc_m2:.3f}, N = {len(sub_m2)}")

# --- MODEL 3: INFLAMMATORY / AUTONOMIC ---
feats_m3 = ['LBXHSCRP', 'LBXWBCSI', 'LBDNENO', 'BMXBMI', 'RIDAGEYR', 'RIAGENDR']
sub_m3 = df[feats_m3 + ['pulse_avg', 'sys_avg', 'dia_avg']].dropna()
sub_m3 = sub_m3[sub_m3['LBXHSCRP'] <= 20.0]
m3_pulse_reg = HistGradientBoostingRegressor(random_state=42).fit(sub_m3[feats_m3], sub_m3['pulse_avg'])
m3_sys_reg = HistGradientBoostingRegressor(random_state=42).fit(sub_m3[feats_m3], sub_m3['sys_avg'])
r2_pulse = r2_score(sub_m3['pulse_avg'], m3_pulse_reg.predict(sub_m3[feats_m3]))
r2_sys = r2_score(sub_m3['sys_avg'], m3_sys_reg.predict(sub_m3[feats_m3]))
print(f"Model 3 Inflammatory Autonomic: Pulse R2 = {r2_pulse:.3f}, Systolic BP R2 = {r2_sys:.3f}, N = {len(sub_m3)}")
