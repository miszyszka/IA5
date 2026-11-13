import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import numpy as np, pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
R = pd.read_parquet(paths.DATA / 'out' / 'd1scan2_yahoo.parquet'); R = R[R.per != 'O']
E = pd.read_parquet(paths.DATA / 'out' / 'd1scan2_ej.parquet')
k = ['h', 'wyzw', 'tryb', 'filtr']
W = R[R.per == 'A'].merge(R[R.per == 'B'], on=k, suffixes=('_A', '_B'))
e = E.groupby(k).apply(lambda g: pd.Series({'n_E': g.n.sum(), 'brutto_E': (g.brutto * g.n).sum() / max(g.n.sum(), 1), 't_E': g.t.sum() / np.sqrt(2)}), include_groups=False).reset_index()
W = W.merge(e, on=k)
W = W[(W.n_A >= 150) & (W.n_B >= 150)]
W['netA'] = W.brutto_A.abs() - W.koszt_A; W['netB'] = W.brutto_B.abs() - W.koszt_B
own = ~W.filtr.str.contains('vix') & ~W.wyzw.str.startswith(('dolar', 'wlasny', 'skrajna_para', 'kup_')) & ~W.filtr.str.contains('dzien_')
W = W[own]
W['s'] = np.sign(W.brutto_A)
ok = (np.sign(W.brutto_B) == W.s) & (np.sign(W.brutto_E) == W.s) & (W.netA > 0) & (W.netB > 0)
W['min_t'] = np.minimum(np.minimum(W.t_A.abs(), W.t_B.abs()), W.t_E.abs())
c = k + ['n_A', 'netA', 't_A', 'n_B', 'netB', 't_B', 'n_E', 'brutto_E', 't_E', 'min_t']
print('— poza poniedziałkiem, znak zgodny w A, B i na niezależnych, netto > 0, min |t| z trzech ≥ 1,5:')
X = W[ok & ~W.filtr.str.contains('pon') & (W.min_t >= 1.5)].sort_values('min_t', ascending=False)
print(len(X)); print(X[c].round(3).head(40).to_string(index=False))
print('— wyzwalacze poniedziałkowe h=1, wszystkie: pełna lista')
X = W[(W.h == 1) & (W.filtr == 'wejscie_pon') & (W.tryb == 'wszystkie')].sort_values('min_t', ascending=False)
print(X[['wyzw', 'n_A', 'brutto_A', 't_A', 'n_B', 'brutto_B', 't_B', 'n_E', 'brutto_E', 't_E']].round(3).head(45).to_string(index=False))
