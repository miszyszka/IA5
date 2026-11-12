import numpy as np
import pandas as pd

pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
R = pd.read_parquet('out/scan_ej.parquet')
k = ['godz', 'h', 'wyzw', 'filtr']
W = R[R.per == 'A'].merge(R[R.per == 'B'], on=k, suffixes=('_A', '_B'))
W = W[(W.n_A >= 150) & (W.n_B >= 150)]
W['netto_A'] = W.brutto_A.abs() - W.spread_A; W['netto_B'] = W.brutto_B.abs() - W.spread_B
W['zgodne'] = np.sign(W.brutto_A) == np.sign(W.brutto_B)
print('reguł z ≥150 zdarzeń w obu połowach:', len(W))
for ta, tb in ((3.5, 2.0), (3.0, 2.0), (2.5, 2.5)):
    s = W[W.zgodne & (W.t_A.abs() >= ta) & (W.t_B.abs() >= tb)]
    n_a = (W.t_A.abs() >= ta).sum()
    print(f'|tA|≥{ta} & |tB|≥{tb} zgodny znak: {len(s)}  (z {n_a} po A; losowo ≈ {n_a*(1-0.9772 if tb==2.0 else 0.0062):.0f});  z tego netto>0 w obu: {((s.netto_A>0)&(s.netto_B>0)).sum()}')
S = W[W.zgodne & (W.t_A.abs() >= 3.0) & (W.t_B.abs() >= 2.0) & (W.netto_A > 0) & (W.netto_B > 0)].copy()
S['kier'] = np.where(S.brutto_A > 0, 'zgodnie', 'przeciw')
S['min_t'] = S[['t_A', 't_B']].abs().min(axis=1)
cols = k + ['kier', 'n_A', 'brutto_A', 'netto_A', 't_A', 'n_B', 'brutto_B', 'netto_B', 't_B']
print(S.sort_values('min_t', ascending=False)[cols].round(2).head(70).to_string())
print(S.groupby('wyzw').size().sort_values(ascending=False).head(25))
S.to_csv('out/survivors.csv', index=False)
