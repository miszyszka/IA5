"""Wejście od N-tego dnia z rzędu za progiem RSI w trendzie SMA200, bez dni-szoków; siatka wokół wyniku diagnozy.
Użycie: D1=<katalog d1> python streak.py [--oos]   (wybór po min(Sharpe A, Sharpe B); OOS tylko z --oos)"""
import itertools
import os
import sys

import ia5.indicators as ind
import numpy as np
import pandas as pd

sys.argv = [sys.argv[0], os.environ.get("D1", "d1_fixed")] + sys.argv[1:]
import refine as R

SHOW_OOS = "--oos" in sys.argv


def entries_st(x, n_, lvl, min_st, rng_cut):
    c, r = x["c"], x["rsi"][n_]
    with np.errstate(invalid="ignore"):
        up, dn = c > x["sma200"], c < x["sma200"]
        zl, zs = up & (r < lvl), dn & (r > 100 - lvl)
        stl, sts = R.streak(zl), R.streak(zs)
        L, S = zl & (stl >= min_st), zs & (sts >= min_st)
        if rng_cut:
            calm = x["rng"] < rng_cut * x["atr"]
            L &= calm
            S &= calm
    sig = L.astype(int) - S.astype(int)
    st = np.where(sig > 0, stl, np.where(sig < 0, sts, 0))
    return sig, st


for x in R.PRE.values():
    x["rsi"][2] = ind.rsi(pd.Series(x["c"]), 2).to_numpy()


def run(spec, ex, pyr, weight):
    n_,lvl,mst,rc=spec
    rows=[]
    from ia5 import engine
    from ia5.config import PAIRS
    for pair,x in R.PRE.items():
        sig,st=entries_st(x,n_,lvl,mst,rc); P=x['P']
        ent=engine.find_entries(P,sig); ent=ent[~ent.atr14.isna()].reset_index(drop=True)
        if ent.empty: continue
        i=ent.signal_i.to_numpy(); d=ent.dir.to_numpy(); e2=ent.copy()
        e2['tp_px']=np.nan; e2['sl_px']=x['c'][i]-d*ex[1]*x['atr'][i] if ex[1] else np.nan
        res=engine.simulate(P,e2,engine.Exit('level',cap=ex[0]),pair)
        xi=res.exit_i.to_numpy(float).copy(); xi[engine.data_cancel(P,i,ent.entry_i.to_numpy(),xi)]=np.nan
        keep=engine.no_overlap(ent.entry_i.to_numpy(),xi,d,pyr)
        pip=PAIRS[pair].pip
        net=res.pips_gross.to_numpy()-PAIRS[pair].spread_pips-0.5*np.nan_to_num(res.nights.to_numpy())
        w=np.clip(st[i]-mst+1,1,3).astype(float) if weight=='seria' else np.ones(len(i))
        rows.append(pd.DataFrame({'pair':pair,'ts':ent.entry_ts.to_numpy()[keep],'xts':res.exit_ts.to_numpy()[keep],
            'ret':(w*net*pip/ent.entry_px.to_numpy())[keep],'r':(net/(x['atr'][i]/pip))[keep],'w':w[keep]}))
    return pd.concat(rows)
specs=list(itertools.product((2,3,5),(10,15,20,25),(1,2,3),(None,1.5,2.0)))
exits=[(2,0),(3,0),(4,0),(5,0),(3,2),(5,2)]
out=[]
for spec in specs:
    for ex in exits:
        for pyr,wt in ((1,'stała'),(3,'stała'),(3,'seria')):
            t=run(spec,ex,pyr,wt)
            row={'rsi':spec[0],'próg':spec[1],'od_dnia':spec[2],'zakres':spec[3],'wyj':f'{ex[0]}d SL{ex[1]}','pyr':pyr,'waga':wt}
            for nm,m in (('A',t.ts<R.CUT_A),('B',(t.ts>=R.CUT_A)&(t.ts<R.CUT_IS))):
                row.update({f'{nm}_{k}':v for k,v in R.stats(t[m]).items()})
            if SHOW_OOS: row.update({f'O_{k}':v for k,v in R.stats(t[t.ts>=R.CUT_IS]).items()})
            out.append(row)
res=pd.DataFrame(out); res['min_sh']=res[['A_sh','B_sh']].min(axis=1)
res.to_csv(os.environ.get('D1','d1_fixed')+'_streak'+('_oos' if SHOW_OOS else '')+'.csv',index=False)
pd.set_option('display.width',280)
cols=[c for c in res.columns if not c.startswith('O_')]
print(len(res)); print(res[(res.A_n>=120)&(res.B_n>=80)].sort_values('min_sh',ascending=False)[cols].head(40).to_string())
