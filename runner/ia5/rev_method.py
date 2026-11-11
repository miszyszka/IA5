"""REV (D-063) — oceny przeceny i trendu, podział kapitału, limit 50%, pasmo i portfele tygodniowe.

Wszystko na panelu cen decyzji (`rev_data.weekly_panel`): wiersz = wtorek 08:00, kolumna = koszyk, PLN = 1.
Projekt: docs/superpowers/specs/2026-11-11-rev-design.md, §6.3. Oceny w tygodniu t zależą tylko od cen do t (R5).

Ceny względem koszyka: `y = ln P` (PLN: 0), indeks koszyka `b` łańcuchowo ze średnich tygodniowych zmian `y` koszyków
z ceną w obu tygodniach (PLN wliczony ze zmianą 0), `x = y − b`, `x_PLN = −b` — złoty jest oceniany tą samą miarą.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .rev_config import BAND, BASE, CAP, ELIGIBLE_WEEKS, START_PLN, SWITCH_EVERY, SWITCH_LOOKBACK, WINDOW_MAX_MISSING

EPS = 1e-12


# ---------- ceny względem koszyka ----------

def basket_index(prices: pd.DataFrame) -> pd.Series:
    """b(t0) = 0; b(t) − b(t−1) = średnia Δ ln P koszyków z ceną w obu tygodniach (PLN wliczony, Δ = 0)."""
    y = np.log(prices.to_numpy(float))
    d = y[1:] - y[:-1]
    ok = np.isfinite(d)
    n = ok.sum(axis=1)
    step = np.where(n > 0, np.where(ok, d, 0.0).sum(axis=1) / np.maximum(n, 1), 0.0)
    return pd.Series(np.r_[0.0, np.cumsum(step)], index=prices.index, name="basket")


def relative(prices: pd.DataFrame) -> pd.DataFrame:
    """x = ln P − b; dla PLN x = −b (złoty tani, gdy słaby wobec reszty)."""
    b = basket_index(prices)
    x = np.log(prices).sub(b, axis=0)
    if BASE in x:
        x[BASE] = -b
    return x


def eligible(prices: pd.DataFrame, weeks: int = ELIGIBLE_WEEKS, max_missing: float = WINDOW_MAX_MISSING) -> pd.DataFrame:
    """Koszyk gra w tygodniu t, gdy od jego pierwszej ceny minęło ≥ `weeks` tygodni, a w ostatnich `weeks` tygodniach
    brakuje ceny w najwyżej `max_missing` z nich. PLN gra zawsze."""
    have = prices.notna().to_numpy()
    T = len(prices)
    rows = np.arange(T)
    first = np.where(have.any(axis=0), have.argmax(axis=0), T)
    c = np.vstack([np.zeros((1, have.shape[1])), np.cumsum(have, axis=0)])
    lo = np.clip(rows - weeks + 1, 0, None)
    cnt = c[rows + 1] - c[lo]
    ok = (rows[:, None] - first[None, :] >= weeks) & (cnt >= weeks * (1 - max_missing) - 1e-9)
    out = pd.DataFrame(ok, index=prices.index, columns=prices.columns)
    if BASE in out:
        out[BASE] = True
    return out


# ---------- oceny ----------

def _window_sums(v: np.ndarray, w: int) -> np.ndarray:
    """Suma kroczącego okna `w` wierszy do t włącznie (krótsze okno na początku)."""
    c = np.vstack([np.zeros((1, v.shape[1])), np.cumsum(v, axis=0)])
    t = np.arange(len(v))
    return c[t + 1] - c[np.clip(t + 1 - w, 0, None)]


def score_value(x: pd.DataFrame, years: int) -> pd.DataFrame:
    """Przecena wobec własnego trendu: regresja liniowa x na numerze tygodnia w oknie 52·years tygodni do t włącznie
    (tylko tygodnie z ceną), V = −reszta_t / σ_reszt. Za mało tygodni z ceną (> 8% braków) albo brak ceny w t → NaN.
    Trend liniowy „zjada” stałą inflację: waluta tanieje stale → to trend, nie przecena."""
    X = x.to_numpy(float)
    M = np.isfinite(X)
    W = 52 * years
    k = (np.arange(len(X), dtype=float) / 52.0)[:, None] * np.ones((1, X.shape[1]))
    Xz = np.where(M, X, 0.0)
    kz = np.where(M, k, 0.0)
    n = _window_sums(M.astype(float), W)
    sk, skk = _window_sums(kz, W), _window_sums(kz * kz, W)
    sx, sxk, sxx = _window_sums(Xz, W), _window_sums(Xz * kz, W), _window_sums(Xz * Xz, W)
    with np.errstate(invalid="ignore", divide="ignore"):
        den = n * skk - sk * sk
        b = (n * sxk - sk * sx) / den
        a = (sx - b * sk) / n
        rss = np.maximum(sxx - a * sx - b * sxk, 0.0)
        sig = np.sqrt(rss / (n - 2))
        e = X - (a + b * k)
        v = -e / sig
    good = M & (n >= W * (1 - WINDOW_MAX_MISSING) - 1e-9) & (sig > EPS) & np.isfinite(v)
    return pd.DataFrame(np.where(good, v, np.nan), index=x.index, columns=x.columns)


def _weekly_sigma(x: pd.DataFrame, weeks: int = 52, min_n: int = 40) -> np.ndarray:
    d = x.diff().to_numpy(float)
    M = np.isfinite(d)
    dz = np.where(M, d, 0.0)
    n = _window_sums(M.astype(float), weeks)
    s1, s2 = _window_sums(dz, weeks), _window_sums(dz * dz, weeks)
    with np.errstate(invalid="ignore", divide="ignore"):
        var = (s2 - s1 * s1 / n) / (n - 1)
    return np.where((n >= min_n) & (var > 0), np.sqrt(np.maximum(var, 0)), np.nan)


def score_momentum(x: pd.DataFrame, months: int) -> pd.DataFrame:
    """Trend: months=3 → (x_t − x_{t−13}) / (σ·√13); months=12 → (x_{t−4} − x_{t−52}) / (σ·√48) (bez ostatniego miesiąca);
    σ = odchylenie tygodniowych zmian x z 52 tygodni."""
    X = x.to_numpy(float)
    sig = _weekly_sigma(x)
    T = len(X)

    def lag(k: int) -> np.ndarray:
        out = np.full_like(X, np.nan)
        if k < T:
            out[k:] = X[: T - k]
        return out

    if months == 3:
        num, scale = X - lag(13), math.sqrt(13)
    elif months == 12:
        num, scale = lag(4) - lag(52), math.sqrt(48)
    else:
        raise ValueError(f"nieznany trend: {months} mies.")
    with np.errstate(invalid="ignore", divide="ignore"):
        v = num / (sig * scale)
    return pd.DataFrame(np.where(np.isfinite(v), v, np.nan), index=x.index, columns=x.columns)


SCORES = ("V3", "V5", "M3", "M12", "V3M3", "V5M3")


def zcross(s: pd.DataFrame) -> pd.DataFrame:
    """Standaryzacja w przekroju (wiersz) po komórkach z wartością; odchylenie 0 → 0."""
    m = s.mean(axis=1)
    sd = s.std(axis=1, ddof=0).replace(0, np.nan)
    return s.sub(m, axis=0).div(sd, axis=0).where(s.notna()).fillna(s * 0)


def score(x: pd.DataFrame, name: str, mask: pd.DataFrame | None = None) -> pd.DataFrame:
    """Ocena wariantu (dodatnia = tania / rosnąca). `mask` = koszyki grające — tylko one wchodzą do standaryzacji
    w kombinacjach i do wyniku (reszta NaN)."""
    def m(df: pd.DataFrame) -> pd.DataFrame:
        return df if mask is None else df.where(mask)

    if name == "V3":
        return m(score_value(x, 3))
    if name == "V5":
        return m(score_value(x, 5))
    if name == "M3":
        return m(score_momentum(x, 3))
    if name == "M12":
        return m(score_momentum(x, 12))
    if name in ("V3M3", "V5M3"):
        v = m(score_value(x, 3 if name == "V3M3" else 5))
        t = m(score_momentum(x, 3))
        both = v.notna() & t.notna()
        return 0.5 * zcross(v.where(both)) + 0.5 * zcross(t.where(both))
    raise ValueError(f"nieznana ocena: {name}")


# ---------- podział, limit 50%, pasmo ----------

def _spill(w: np.ndarray, order: np.ndarray, cap: float, groups: list[np.ndarray]) -> np.ndarray:
    """Ucina wagi powyżej `cap`, a nadwyżkę rozdziela grupami: w grupie najpierw proporcjonalnie do koszyków z wagą
    w (0, cap), potem kolejno według `order` (każdy do `cap`); co się nie zmieści — następna grupa."""
    w = np.asarray(w, float).copy()
    total = float(w.sum())
    cut_from = w > cap + EPS
    excess = float(np.maximum(w - cap, 0).sum())
    w = np.minimum(w, cap)
    return _spill_groups(w, order, cap, groups, excess, total, cut_from)


def _spill_groups(w: np.ndarray, order: np.ndarray, cap: float, groups: list[np.ndarray], excess: float, total: float,
                  cut_from: np.ndarray) -> np.ndarray:
    for g in groups:
        for _ in range(len(w) + 1):
            if excess <= EPS:
                return w
            rec = g & (w > EPS) & (w < cap - EPS)
            if not rec.any():
                break
            put = np.minimum(excess * w[rec] / w[rec].sum(), cap - w[rec])
            w[rec] += put
            excess -= float(put.sum())
        for i in order:
            if excess <= EPS:
                return w
            if g[i] and w[i] < cap - EPS:
                p = min(cap - w[i], excess)
                w[i] += p
                excess -= p
    if excess > EPS:   # nie ma gdzie zmieścić (np. wszystko zamrożone poza PLN) — limit przekroczony z konieczności,
        back = cut_from & (w > EPS)          # kapitał nigdy nie znika: nadwyżka wraca do koszyków, którym ją ucięto
        if not back.any():
            back = w > EPS
        w[back] += excess * w[back] / w[back].sum() if back.any() else 0.0
    assert abs(w.sum() - total) < 1e-9, "podział zgubił kapitał"
    return w


def cap_fill(w: np.ndarray, order: np.ndarray, cap: float = CAP) -> np.ndarray:
    """Normalizuje wagi i ucina każdą powyżej `cap`; nadwyżka idzie proporcjonalnie do koszyków z wagą w (0, cap),
    a gdy takich brak — kolejno do następnych w `order` (od najlepszej oceny), każdy do `cap`."""
    w = np.asarray(w, float)
    s = w.sum()
    if s <= 0:
        return w.copy()
    return _spill(w / s, np.asarray(order), cap, [np.ones(len(w), bool)])


def _order(s: np.ndarray) -> np.ndarray:
    """Indeksy od najwyższej oceny; NaN na końcu (stabilnie)."""
    key = np.where(np.isfinite(s), -s, np.inf)
    return np.argsort(key, kind="stable")


def target_weights(s: pd.Series, how: str, cap: float = CAP) -> pd.Series:
    """`s` = oceny koszyków grających (NaN = koszyk nie gra, waga 0). P: w ∝ max(s − średnia, 0);
    R: w ∝ max((N+1)/2 − miejsce, 0), miejsce 1 = najwyższa ocena, remisy średnio. Wszystkie ≤ 0 → równo. Potem limit."""
    v = s.to_numpy(float)
    ok = np.isfinite(v)
    w = np.zeros(len(v))
    if not ok.any():
        if BASE in s.index:   # nikt nie gra (przed startem) — wszystko w złotówkach, ile pozwala limit
            w[list(s.index).index(BASE)] = 1.0
        else:
            w[:] = 1.0
        return pd.Series(cap_fill(w, np.arange(len(v)), cap), index=s.index)
    if how == "P":
        w[ok] = np.maximum(v[ok] - v[ok].mean(), 0.0)
    elif how == "R":
        n = int(ok.sum())
        rank = pd.Series(-v[ok]).rank(method="average").to_numpy()
        w[ok] = np.maximum((n + 1) / 2 - rank, 0.0)
    else:
        raise ValueError(f"nieznany podział: {how}")
    if w.sum() <= EPS:
        w[ok] = 1.0
    return pd.Series(cap_fill(w, _order(v), cap), index=s.index)


def rebalance(cur: np.ndarray, target: np.ndarray, order: np.ndarray, frozen: np.ndarray, band: float = BAND,
              cap: float = CAP) -> np.ndarray:
    """Pasmo: koszyk zmieniamy, gdy cel różni się od udziału o ≥ `band` albo udział przekracza limit; koszyk zamrożony
    (bez ceny) zostaje. Wolny kapitał (1 − to, czego nie ruszamy) idzie na zmieniane koszyki proporcjonalnie do celu,
    z limitem; gdy nadwyżki nie da się zmieścić — do kolejnych niezamrożonych w `order`."""
    cur = np.asarray(cur, float)
    target = np.asarray(target, float)
    frozen = np.asarray(frozen, bool)
    mask = ((np.abs(target - cur) >= band - 1e-12) | (cur > cap + EPS)) & ~frozen
    if not mask.any():
        return cur.copy()
    if target[mask].sum() <= EPS:
        mask |= (target > EPS) & ~frozen
    free = 1.0 - cur[~mask].sum()
    new = cur.copy()
    tm = target[mask]
    new[mask] = (tm / tm.sum() if tm.sum() > EPS else np.full(len(tm), 1.0 / len(tm))) * free
    if (new > cap + EPS).any():   # najpierw wewnątrz zmienianych koszyków, potem — gdy się nie mieści — inni niezamrożeni
        new = _spill(new, np.asarray(order), cap, [mask, ~frozen])
    return new


# ---------- warianty i portfele ----------

@dataclass(frozen=True)
class Variant:
    id: str
    score: str
    how: str
    label: str


_SCORE_LABEL = {"V3": "Przecena 3 lata", "V5": "Przecena 5 lat", "M3": "Trend 3 mies.", "M12": "Trend 12 mies.",
                "V3M3": "Tania i przestała tanieć (3 lata)", "V5M3": "Tania i przestała tanieć (5 lat)"}
_HOW_LABEL = {"P": "proporcjonalnie", "R": "ranking"}
VARIANTS: tuple[Variant, ...] = tuple(
    Variant(f"{s}-{h}", s, h, f"{_SCORE_LABEL[s]}, {_HOW_LABEL[h]}") for s in SCORES for h in ("P", "R")
) + (Variant("SW", "", "", "Przełącznik (co 13 tygodni najlepszy z 3 lat)"),)
STATIC = tuple(v for v in VARIANTS if v.id != "SW")
VARIANT_BY_ID = {v.id: v for v in VARIANTS}


@dataclass
class Sim:
    value: pd.Series        # wartość w PLN w chwili decyzji, przed przewalutowaniem (po cenach wykonania)
    units: pd.DataFrame     # jednostki po przewalutowaniu
    weights: pd.DataFrame   # udziały po przewalutowaniu
    ret: pd.Series          # ln value_{t+1} − ln value_t (indeks t)
    trades: int


def variant_targets(prices: pd.DataFrame, elig: pd.DataFrame, v: Variant) -> tuple[pd.DataFrame, np.ndarray]:
    """Cele i kolejność (od najwyższej oceny) dla wariantu statycznego, tydzień po tygodniu."""
    s = score(relative(prices), v.score, elig).where(elig)
    S = s.to_numpy(float)
    W = np.zeros_like(S)
    orders = np.zeros(S.shape, dtype=int)
    cols = list(prices.columns)
    for t in range(len(S)):
        row = pd.Series(S[t], index=cols)
        W[t] = target_weights(row, v.how).to_numpy()
        orders[t] = _order(S[t])
    return pd.DataFrame(W, index=prices.index, columns=cols), orders


def equal_targets(elig: pd.DataFrame) -> pd.DataFrame:
    """Równy podział: 1/N po koszykach grających (PLN gra zawsze)."""
    e = elig.astype(float)
    return e.div(e.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def trade(units: np.ndarray, raw_px: np.ndarray, last_px: np.ndarray, target: np.ndarray, order: np.ndarray,
          band: float = BAND, cap: float = CAP) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """Jedno przeliczenie (to samo w badaniu i na żywo): wycena jednostek po ostatnich znanych cenach, koszyk bez ceny
    w dniu decyzji zamrożony, `rebalance` do celu; zmieniają się tylko koszyki, którym zmienia się udział.
    Zwraca (nowe jednostki, wartość, zamrożone, zmienione)."""
    px = np.where(np.isfinite(last_px), last_px, 0.0)
    V = float(units @ px)
    frozen = ~np.isfinite(raw_px)
    cur = units * px / V if V > 0 else np.zeros(len(units))
    new = rebalance(cur, target, order, frozen, band, cap)
    chg = ~frozen & (px > 0) & (np.abs(new - cur) > 1e-12)
    nu = units.copy()
    nu[chg] = new[chg] * V / px[chg]
    assert V <= 0 or abs(float(nu @ px) - V) <= 1e-7 * V, "przeliczenie zmieniło wartość portfela (bez kosztów musi być ta sama)"
    return nu, V, frozen, chg


def simulate(exe: pd.DataFrame, targets: pd.DataFrame, orders: np.ndarray | None = None, band: float = BAND,
             cap: float = CAP, v0: float = START_PLN, start: int = 0, end: int | None = None) -> Sim:
    """Portfel tygodniowy od wiersza `start`: w t wycena jednostek po `exe` (brak ceny → ostatnia znana), koszyk bez ceny
    w t zamrożony, `rebalance` do celu, nowe jednostki. Pierwsza decyzja z całości w PLN. Bez kosztów (R3)."""
    cols = list(exe.columns)
    P = exe.to_numpy(float)
    T = len(P) if end is None else min(end, len(P))
    last = pd.DataFrame(P).ffill().to_numpy()
    Tg = targets.to_numpy(float)
    N = len(cols)
    units = np.zeros(N)
    units[cols.index(BASE)] = v0
    vals = np.full(len(P), np.nan)
    U = np.zeros((len(P), N))
    Wt = np.zeros((len(P), N))
    trades = 0
    for t in range(start, T):
        o = orders[t] if orders is not None else _order(Tg[t])
        units, V, _, chg = trade(units, P[t], last[t], Tg[t], o, band, cap)
        vals[t] = V
        trades += int(chg.sum())
        px = np.where(np.isfinite(last[t]), last[t], 0.0)
        U[t], Wt[t] = units, (units * px / V if V > 0 else 0)
    idx = exe.index
    value = pd.Series(vals, index=idx)
    nxt = np.full(len(P), np.nan)
    for t in range(start, T - 1):
        px1 = np.where(np.isfinite(last[t + 1]), last[t + 1], 0.0)
        nxt[t] = float(U[t] @ px1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = pd.Series(np.log(nxt / vals), index=idx)
    sl = slice(start, T)
    return Sim(value.iloc[sl], pd.DataFrame(U[sl], index=idx[sl], columns=cols),
               pd.DataFrame(Wt[sl], index=idx[sl], columns=cols), ret.iloc[start:max(T - 1, start)], trades)


def ir(x) -> float:
    """Wskaźnik IR tygodniowych nadwyżek w skali roku (NaN przy < 10 obserwacjach)."""
    a = np.asarray(x, float)
    a = a[np.isfinite(a)]
    if len(a) < 10:
        return float("nan")
    sd = a.std(ddof=1)
    return float(a.mean() / sd * math.sqrt(52)) if sd > 0 else float("nan")


def switcher_targets(excess: pd.DataFrame, static: dict[str, pd.DataFrame], equal: pd.DataFrame, start: int,
                     static_orders: dict[str, np.ndarray] | None = None, every: int = SWITCH_EVERY,
                     lookback: int = SWITCH_LOOKBACK) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """Przełącznik: co `every` tygodni od `start` wybiera wariant o najwyższym IR nadwyżki z ostatnich `lookback` tygodni
    (tylko wiersze < t — znane w chwili decyzji); remis → pierwszy w VARIANTS; przed `lookback` tygodniami — równy podział.
    Zwraca (cele, wybrany wariant w każdym tygodniu, kolejność)."""
    idx = equal.index
    T = len(idx)
    W = equal.to_numpy(float).copy()
    order = np.tile(np.arange(W.shape[1]), (T, 1))
    chosen = pd.Series("equal", index=idx, dtype=object)
    ids = [v.id for v in STATIC if v.id in static]
    pick = "equal"
    ex = excess.reindex(idx)
    for t in range(start, T):
        if (t - start) % every == 0:
            if t - start >= lookback:
                win = ex.iloc[t - lookback:t]
                scores = [ir(win[i].to_numpy()) if i in win else float("nan") for i in ids]
                best = int(np.nanargmax(scores)) if np.isfinite(scores).any() else -1
                pick = ids[best] if best >= 0 else "equal"
            else:
                pick = "equal"
        chosen.iloc[t] = pick
        if pick != "equal":
            W[t] = static[pick].iloc[t].to_numpy(float)
            if static_orders is not None:
                order[t] = static_orders[pick][t]
    return pd.DataFrame(W, index=idx, columns=equal.columns), chosen, order


def daily_equity(units: pd.DataFrame, daily: pd.DataFrame) -> pd.Series:
    """Wartość dzień po dniu: jednostki z ostatniej decyzji przed dniem × zamknięcie (brak ceny → ostatnia znana).
    Indeks `daily` = close_ts; zamknięcie poniedziałku (close_ts < wtorek 08:00) wycenia jeszcze stare jednostki —
    przy wymianie po tej samej cenie i bez kosztów wartość jest ta sama."""
    if units.empty or daily.empty:
        return pd.Series(dtype=float)
    d = daily.reindex(columns=units.columns).ffill()
    d = d[d.index >= units.index[0]]
    pos = np.searchsorted(units.index.to_numpy("int64"), d.index.to_numpy("int64"), side="left") - 1
    U = units.to_numpy(float)
    first = U[0]
    rows = np.where(pos[:, None] >= 0, U[np.clip(pos, 0, None)], first)
    px = np.where(np.isfinite(d.to_numpy(float)), d.to_numpy(float), 0.0)
    return pd.Series((rows * px).sum(axis=1), index=d.index)
