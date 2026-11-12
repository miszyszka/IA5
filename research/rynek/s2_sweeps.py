"""Polowania na stopy: wczorajszy szczyt/dołek (dzień FX od 17:00 NY) i zakres Azji naruszone, a potem odrzucone albo utrzymane."""
import ev
import pandas as pd


def pd_levels(d):
    g = d.groupby("fxday")
    hi, lo = g.high.max(), g.low.min()
    days = hi.index
    pdh = pd.Series(hi.shift(1).reindex(d.fxday).to_numpy(), index=d.index)
    pdl = pd.Series(lo.shift(1).reindex(d.fxday).to_numpy(), index=d.index)
    return pdh, pdl

def sweep_pd(mode, sess=None, first=True, depth=0.0):
    def f(d, p):
        pdh, pdl = pd_levels(d)
        a = d.atr
        up = (d.high > pdh + depth * a)
        dn = (d.low < pdl - depth * a)
        if mode == "reject":      # wybicie i zamknięcie z powrotem w zakresie → przeciw wybiciu
            s = -(up & (d.close < pdh)).astype(int) + (dn & (d.close > pdl)).astype(int)
        elif mode == "hold":      # zamknięcie za poziomem → z wybiciem
            s = (d.close > pdh).astype(int) - (d.close < pdl).astype(int)
        elif mode == "hold_fade":
            s = -(d.close > pdh).astype(int) + (d.close < pdl).astype(int)
        s = pd.Series(s, index=d.index)
        if first:                 # pierwsze takie zdarzenie w dniu FX i kierunku
            s = s.where(s.groupby([d.fxday, s]).cumcount() == 0, 0)
        if sess == "lon":
            s = s.where(d.h_lon.between(7, 11), 0)
        elif sess == "ny":
            s = s.where(d.h_lon.between(12, 16), 0)
        elif sess == "asia":
            s = s.where(d.h_lon.between(0, 6), 0)
        return s
    return f

for mode in ("reject", "hold"):
    for sess in (None, "asia", "lon", "ny"):
        ev.study(f"wczorajszy H/L {mode} sesja={sess}", sweep_pd(mode, sess))
for depth in (0.25, 0.5, 1.0):
    ev.study(f"wczorajszy H/L reject głębokość>{depth}ATR", sweep_pd("reject", None, True, depth))

def asia_sweep(mode, hours=(7, 9)):
    def f(d, p):
        asia = d.h_lon.between(0, 6)
        g = d[asia].groupby("londay")
        ah = pd.Series(g.high.max().reindex(d.londay).to_numpy(), index=d.index)
        al = pd.Series(g.low.min().reindex(d.londay).to_numpy(), index=d.index)
        win = d.h_lon.between(*hours)
        if mode == "reject":
            s = -((d.high > ah) & (d.close < ah)).astype(int) + ((d.low < al) & (d.close > al)).astype(int)
        else:
            s = (d.close > ah).astype(int) - (d.close < al).astype(int)
        s = pd.Series(s, index=d.index).where(win, 0)
        return s.where(s.groupby([d.londay, s]).cumcount() == 0, 0)
    return f

for mode in ("reject", "hold"):
    for hours in ((7, 9), (7, 11), (12, 15)):
        ev.study(f"zakres Azji {mode} godz. Londynu {hours}", asia_sweep(mode, hours))
print("hipotez:", ev.N_TESTS["n"])
