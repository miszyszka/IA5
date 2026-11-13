import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import numpy as np, pandas as pd
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 200)
Y = pd.read_parquet(paths.DATA / 'out' / 'grid_yahoo.parquet'); Y = Y[Y.per != 'O']        # O zamknięte
E = pd.read_parquet(paths.DATA / 'out' / 'grid_ej.parquet')
k = ['wyzw', 'trend', 'dzien', 'zm', 'h']
W = Y[Y.per == 'A'].merge(Y[Y.per == 'B'], on=k, suffixes=('_A', '_B')).merge(
    E[E.per == 'EA'].merge(E[E.per == 'EB'], on=k, suffixes=('_EA', '_EB')), on=k)
W = W[(W.n_A >= 150) & (W.n_B >= 150)]
W['min_t'] = W[['t_A', 't_B']].min(axis=1)
W['min_tE'] = W[['t_EA', 't_EB']].min(axis=1)
W['min4'] = W[['t_A', 't_B', 't_EA', 't_EB']].min(axis=1)
W.to_parquet(paths.DATA / 'out' / 'grid_wide.parquet', index=False)
print('reguł:', len(W))
for thr in (2.0, 2.5, 3.0, 3.5):
    s = W[W.min_t >= thr]
    print(f'min(tA,tB) ≥ {thr}: {len(s)}; z nich dodatnie w obu połowach danych niezależnych: {(s.min_tE > 0).sum()}; min tE ≥ 1,5: {(s.min_tE >= 1.5).sum()}')
c = k + ['n_A', 'net_A', 't_A', 'lata_A', 'n_B', 'net_B', 't_B', 'lata_B', 't_EA', 't_EB']
print('— najlepsze wg min z 4 odcinków, po dniu wejścia:')
print(W.sort_values('min4', ascending=False).groupby('dzien').head(4).sort_values(['dzien', 'min4'], ascending=[True, False])[c].round(3).to_string(index=False))
