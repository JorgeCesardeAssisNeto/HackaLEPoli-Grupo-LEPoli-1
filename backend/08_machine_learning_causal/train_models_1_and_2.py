import pyreadstat
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import statsmodels.api as sm

# 1. Prepare 2017-2020 Data
demo = pyreadstat.read_xport('Dados NHANHES/P_DEMO.xpt')[0][['SEQN', 'RIDAGEYR', 'RIAGENDR']]
bpxo = pyreadstat.read_xport('Dados NHANHES/P_BPXO.xpt')[0]
cbc = pyreadstat.read_xport('Dados NHANHES/P_CBC.xpt')[0][['SEQN', 'LBXHGB']]
fer = pyreadstat.read_xport('Dados NHANHES/P_FERTIN.xpt')[0][['SEQN', 'LBXFER']]
bmx = pyreadstat.read_xport('Dados NHANHES/P_BMX.xpt')[0][['SEQN', 'BMXBMI', 'BMXWT', 'BMXHT']]
slq = pyreadstat.read_xport('Dados NHANHES/P_SLQ.xpt')[0][['SEQN', 'SLD012']]
paq = pyreadstat.read_xport('Dados NHANHES/P_PAQ.xpt')[0][['SEQN', 'PAD680']]
ghb = pyreadstat.read_xport('Dados NHANHES/P_GHB.xpt')[0][['SEQN', 'LBXGH']]
glu = pyreadstat.read_xport('Dados NHANHES/P_GLU.xpt')[0][['SEQN', 'LBXGLU']]

bpxo['pulse_avg'] = bpxo[['BPXOPLS1', 'BPXOPLS2', 'BPXOPLS3']].mean(axis=1)
bpxo['sys_avg'] = bpxo[['BPXOSY1', 'BPXOSY2', 'BPXOSY3']].mean(axis=1)
bpxo['dia_avg'] = bpxo[['BPXODI1', 'BPXODI2', 'BPXODI3']].mean(axis=1)
bpx_sub = bpxo[['SEQN', 'pulse_avg', 'sys_avg', 'dia_avg']]

df = demo.merge(bpx_sub, on='SEQN').merge(bmx, on='SEQN').merge(slq, on='SEQN', how='left').merge(paq, on='SEQN', how='left')
df = df.merge(cbc, on='SEQN', how='left').merge(fer, on='SEQN', how='left').merge(ghb, on='SEQN', how='left').merge(glu, on='SEQN', how='left')

# Impute sleep and sedentary with medians if missing
df['SLD012'] = df['SLD012'].fillna(df['SLD012'].median())
df['PAD680'] = df['PAD680'].fillna(df['PAD680'].median())

# Targets
df['target_anemia'] = np.where(
    df['LBXHGB'].isna(), np.nan,
    np.where((df['RIAGENDR'] == 1) & (df['LBXHGB'] < 13.0), 1,
    np.where((df['RIAGENDR'] == 2) & (df['LBXHGB'] < 12.0), 1, 0))
)
df['target_low_ferritin'] = np.where(df['LBXFER'].isna(), np.nan, np.where(df['LBXFER'] < 30.0, 1, 0))
df['target_high_hba1c'] = np.where(df['LBXGH'].isna(), np.nan, np.where(df['LBXGH'] >= 5.7, 1, 0))
df['target_high_glu'] = np.where(df['LBXGLU'].isna(), np.nan, np.where(df['LBXGLU'] >= 100.0, 1, 0))

features_m1 = ['pulse_avg', 'RIDAGEYR', 'RIAGENDR', 'BMXBMI', 'sys_avg', 'dia_avg', 'PAD680', 'SLD012']

print('--- MODELO 1: ANEMIA ---')
sub_ane = df[features_m1 + ['target_anemia']].dropna()
X1 = sub_ane[features_m1]
y1 = sub_ane['target_anemia']
X1_tr, X1_te, y1_tr, y1_te = train_test_split(X1, y1, test_size=0.2, random_state=42, stratify=y1)
clf1 = HistGradientBoostingClassifier(random_state=42).fit(X1_tr, y1_tr)
probs1 = clf1.predict_proba(X1_te)[:, 1]
print('Anemia ROC-AUC:', roc_auc_score(y1_te, probs1))

logit1 = sm.Logit(y1, sm.add_constant(X1)).fit(disp=False)
print('Anemia Logit Odds Ratios (exp(beta)):')
for f, b, p in zip(['const'] + features_m1, logit1.params, logit1.pvalues):
    print(f'  {f}: OR = {np.exp(b):.3f}, p = {p:.4f}')

print('\n--- MODELO 1: FERRITINA BAIXA (< 30 ng/mL) ---')
sub_fer = df[features_m1 + ['target_low_ferritin']].dropna()
X2 = sub_fer[features_m1]
y2 = sub_fer['target_low_ferritin']
X2_tr, X2_te, y2_tr, y2_te = train_test_split(X2, y2, test_size=0.2, random_state=42, stratify=y2)
clf2 = HistGradientBoostingClassifier(random_state=42).fit(X2_tr, y2_tr)
probs2 = clf2.predict_proba(X2_te)[:, 1]
print('Ferritin ROC-AUC:', roc_auc_score(y2_te, probs2))

logit2 = sm.Logit(y2, sm.add_constant(X2)).fit(disp=False)
print('Ferritin Logit Odds Ratios:')
for f, b, p in zip(['const'] + features_m1, logit2.params, logit2.pvalues):
    print(f'  {f}: OR = {np.exp(b):.3f}, p = {p:.4f}')

print('\n--- MODELO 2: EIXO METABÓLICO (HBA1C >= 5.7%) ---')
features_m2_strict = ['BMXBMI', 'SLD012', 'PAD680', 'pulse_avg']
sub_m2 = df[features_m2_strict + ['target_high_hba1c']].dropna()
Xm2 = sub_m2[features_m2_strict]
ym2 = sub_m2['target_high_hba1c']
Xm2_tr, Xm2_te, ym2_tr, ym2_te = train_test_split(Xm2, ym2, test_size=0.2, random_state=42, stratify=ym2)
clf_m2 = HistGradientBoostingClassifier(random_state=42).fit(Xm2_tr, ym2_tr)
probs_m2 = clf_m2.predict_proba(Xm2_te)[:, 1]
print('Strict M2 (BMI, Sleep, Sedentary, Pulse) HbA1c ROC-AUC:', roc_auc_score(ym2_te, probs_m2))

logit_m2 = sm.Logit(ym2, sm.add_constant(Xm2)).fit(disp=False)
print('Strict M2 Odds Ratios:')
for f, b, p in zip(['const'] + features_m2_strict, logit_m2.params, logit_m2.pvalues):
    print(f'  {f}: OR = {np.exp(b):.3f}, p = {p:.4f}')

print('\n--- MODELO 2: EIXO METABÓLICO COM IDADE/SEXO ---')
features_m2_full = ['BMXBMI', 'SLD012', 'PAD680', 'pulse_avg', 'RIDAGEYR', 'RIAGENDR']
sub_m2_full = df[features_m2_full + ['target_high_hba1c']].dropna()
Xm2f_tr, Xm2f_te, ym2f_tr, ym2f_te = train_test_split(sub_m2_full[features_m2_full], sub_m2_full['target_high_hba1c'], test_size=0.2, random_state=42)
clf_m2f = HistGradientBoostingClassifier(random_state=42).fit(Xm2f_tr, ym2f_tr)
probs_m2f = clf_m2f.predict_proba(Xm2f_te)[:, 1]
print('Full M2 (with Age/Gender) HbA1c ROC-AUC:', roc_auc_score(ym2f_te, probs_m2f))
