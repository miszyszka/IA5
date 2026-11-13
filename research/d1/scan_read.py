import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import numpy as np, pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
R = pd.read_parquet(paths.DATA / 'out' / 'd1scan2_yahoo.parquet'); R = R[R.per != 'O']      # O (OOS) zamknięte do zamrożenia projektu
E = pd.read_parquet(paths.DATA / 'out' / 'd1scan2_ej.parquet')
k = ['h', 'wyzw', 'tryb', 'filtr']
W = R[R.per == 'A'].merge(R[R.per == 'B'], on=k, suffixes=('_A', '_B'))
e = E.groupby(k).apply(lambda g: pd.Series({'n_E': g.n.sum(), 'brutto_E': (g.brutto * g.n).sum() / max(g.n.sum(), 1), 't_E': g.t.sum() / np.sqrt(2)}), include_groups=False).reset_index()
W = W.merge(e, on=k)
W = W[(W.n_A >= 150) & (W.n_B >= 150)]
W['zg'] = np.sign(W.brutto_A) == np.sign(W.brutto_B)
W['netA'] = W.brutto_A.abs() - W.koszt_A; W['netB'] = W.brutto_B.abs() - W.koszt_B
W['bez_vix'] = ~W.filtr.str.contains('vix') & ~W.wyzw.str.startswith(('dolar', 'wlasny', 'skrajna_para', 'kup_')) & ~W.filtr.str.contains('dzien_')
print('reguł:', len(W), 'tylko z własnych świec pary:', W.bez_vix.sum())
for ta, tb in ((3.5, 2.0), (3.0, 2.0), (2.5, 2.5), (3.0, 3.0)):
    nA = (W.t_A.abs() >= ta).sum(); s = W[W.zg & (W.t_A.abs() >= ta) & (W.t_B.abs() >= tb)]
    pr = {2.0: 0.0228, 2.5: 0.0062, 3.0: 0.00135}[tb]
    print(f'|tA|≥{ta}, |tB|≥{tb}, zgodny znak: {len(s)} (z {nA}; losowo ≈ {nA * pr:.0f}); netto>0 w obu: {((s.netA > 0) & (s.netB > 0)).sum()}; zgodny znak na niezależnych: {(np.sign(s.brutto_E) == np.sign(s.brutto_A)).sum()}')
S = W[W.zg & (W.t_A.abs() >= 2.5) & (W.t_B.abs() >= 2.0) & (W.netA > 0) & (W.netB > 0)].copy()
S['kier'] = np.where(S.brutto_A > 0, 'zgodnie', 'przeciw'); S['min_t'] = S[['t_A', 't_B']].abs().min(axis=1)
S.to_csv(paths.DATA / 'out' / 'd1scan2_survivors.csv', index=False)
print('ocalałe:', len(S), 'z własnych świec:', S.bez_vix.sum(), '· znak zgodny na niezależnych:', (np.sign(S.brutto_E) == np.sign(S.brutto_A)).mean().round(2))
c = k + ['kier', 'n_A', 'netA', 't_A', 'n_B', 'netB', 't_B', 'n_E', 'brutto_E', 't_E']
print(S[S.bez_vix].sort_values('min_t', ascending=False)[c].round(3).head(40).to_string(index=False))
print(S[S.bez_vix].groupby(['wyzw', 'kier']).size().sort_values(ascending=False).head(25).to_string())
