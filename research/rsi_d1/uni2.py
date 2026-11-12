import numpy as np
import pandas as pd

pd.set_option('display.width',250)
t=pd.read_parquet('diag.parquet'); t=t[t.period!='OOS'].copy()
for k in (1,3,5,10): t[f'w{k}']=t[f'ret{k}'].clip(-4,4)
feats=['r2','r5','r14','trend200','slope200','trend50_200','dist20','mom5','mom20','mom60','mom120','volr','rangeatr','clv','body','adx','di','pos250','pos20','usd_crowd']
res=[]
for f in feats:
    A=t[t.period=='A']; q=np.unique(np.nanquantile(A[f],[0,.2,.4,.6,.8,1]))
    b=pd.cut(t[f],q,include_lowest=True,duplicates='drop')
    for Y in ('w3','w5','w10'):
        g=t.assign(b=b).groupby(['b','period'],observed=True)[Y].mean().unstack()
        res.append((f,Y,g['A'].iloc[-1]-g['A'].iloc[0],g['B'].iloc[-1]-g['B'].iloc[0], g['A'].max()-g['A'].min()))
r=pd.DataFrame(res,columns=['f','Y','A','B','rngA'])
p=r.pivot(index='f',columns='Y',values=['A','B']).round(3)
print(p.to_string())
