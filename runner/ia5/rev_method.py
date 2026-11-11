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

from .rev_config import (
    BAND,
    BASE,
    BRAKE_LONG,
    BRAKE_MULT,
    BRAKE_SHORT,
    CAP,
    ELIGIBLE_WEEKS,
    OVERLAYS,
    PLN_CAP_VALVE,
    START_PLN,
    SWITCH_EVERY,
    SWITCH_LOOKBACK,
    WINDOW_MAX_MISSING,
)

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

def _spill(w: np.ndarray, order: np.ndarray, cap, groups: list[np.ndarray]) -> np.ndarray:
    """Ucina wagi powyżej limitu (`cap`: liczba albo wektor — D-065: PLN może mieć inny limit), a nadwyżkę rozdziela grupami:
    w grupie najpierw proporcjonalnie do koszyków z wagą poniżej limitu, potem kolejno według `order`; co się nie zmieści —
    następna grupa. Kapitał nigdy nie znika (gdy nie ma gdzie — limit przekroczony z konieczności)."""
    w = np.asarray(w, float).copy()
    c = np.broadcast_to(np.asarray(cap, float), w.shape).copy()
    total = float(w.sum())
    cut_from = w > c + EPS
    excess = float(np.maximum(w - c, 0).sum())
    w = np.minimum(w, c)
    for g in groups:
        for _ in range(len(w) + 1):
            if excess <= EPS:
                break
            rec = g & (w > EPS) & (w < c - EPS)
            if not rec.any():
                break
            put = np.minimum(excess * w[rec] / w[rec].sum(), c[rec] - w[rec])
            w[rec] += put
            excess -= float(put.sum())
        for i in order:
            if excess <= EPS:
                break
            if g[i] and w[i] < c[i] - EPS:
                q = min(c[i] - w[i], excess)
                w[i] += q
                excess -= q
        if excess <= EPS:
            break
    if excess > EPS:
        back = cut_from & (w > EPS)          # nadwyżka wraca do koszyków, którym ją ucięto
        if not back.any():
            back = w > EPS
        if back.any():
            w[back] += excess * w[back] / w[back].sum()
    assert abs(w.sum() - total) < 1e-9, "podział zgubił kapitał"
    return w


def cap_fill(w: np.ndarray, order: np.ndarray, cap=CAP) -> np.ndarray:
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
              cap=CAP) -> np.ndarray:
    """Pasmo: koszyk zmieniamy, gdy cel różni się od udziału o ≥ `band` albo udział przekracza limit; koszyk zamrożony
    (bez ceny) zostaje. Wolny kapitał (1 − to, czego nie ruszamy) idzie na zmieniane koszyki proporcjonalnie do celu,
    z limitem; gdy nadwyżki nie da się zmieścić — do kolejnych niezamrożonych w `order`."""
    cur = np.asarray(cur, float)
    target = np.asarray(target, float)
    frozen = np.asarray(frozen, bool)
    cap = np.broadcast_to(np.asarray(cap, float), cur.shape)
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
    overlay: str = ""

    @property
    def base(self) -> str:
        return f"{self.score}-{self.how}"


_SCORE_LABEL = {"V3": "Przecena 3 lata", "V5": "Przecena 5 lat", "M3": "Trend 3 mies.", "M12": "Trend 12 mies.",
                "V3M3": "Tania i przestała tanieć (3 lata)", "V5M3": "Tania i przestała tanieć (5 lat)"}
_HOW_LABEL = {"P": "proporcjonalnie", "R": "ranking"}
OVERLAY_LABEL = {"": "", "Z26": " + zawór złotówkowy 6 mies.", "Z52": " + zawór złotówkowy 12 mies.",
                 "H": " + hamulec zmienności", "S": " + nie sprzedawaj na stracie"}
VARIANTS: tuple[Variant, ...] = tuple(
    Variant(f"{s}-{h}" + (f"+{o}" if o else ""), s, h, f"{_SCORE_LABEL[s]}, {_HOW_LABEL[h]}{OVERLAY_LABEL[o]}", o)
    for s in SCORES for h in ("P", "R") for o in OVERLAYS
) + (Variant("SW", "", "", "Przełącznik (co 13 tygodni najlepszy z 3 lat)"),)
STATIC = tuple(v for v in VARIANTS if v.id != "SW")
VARIANT_BY_ID = {v.id: v for v in VARIANTS}


# ---------- nakładki (D-065): zawór złotówkowy i hamulec zmienności ----------

def foreign_index(prices: pd.DataFrame) -> pd.Series:
    """Indeks walut obcych wobec PLN: łańcuchowa średnia tygodniowych zmian ln kursu koszyków poza PLN z ceną w obu
    tygodniach. Rośnie, gdy złoty słabnie; spada, gdy złoty się umacnia."""
    cols = [c for c in prices.columns if c != BASE]
    if not cols:
        return pd.Series(0.0, index=prices.index)
    y = np.log(prices[cols].to_numpy(float))
    d = y[1:] - y[:-1]
    ok = np.isfinite(d)
    n = ok.sum(axis=1)
    step = np.where(n > 0, np.where(ok, d, 0.0).sum(axis=1) / np.maximum(n, 1), 0.0)
    return pd.Series(np.r_[0.0, np.cumsum(step)], index=prices.index, name="foreign")


def valve_on(prices: pd.DataFrame, weeks: int) -> np.ndarray:
    """Zawór złotówkowy: indeks walut obcych niżej niż `weeks` tygodni temu (złoty się umacnia)."""
    f = foreign_index(prices)
    d = (f - f.shift(weeks)).to_numpy(float)
    return np.where(np.isfinite(d), d < 0, False)


def brake_on(prices: pd.DataFrame, short: int = BRAKE_SHORT, long: int = BRAKE_LONG, mult: float = BRAKE_MULT) -> np.ndarray:
    """Hamulec zmienności: odchylenie tygodniowych zmian indeksu z `short` tygodni > `mult` × mediana tego odchylenia
    z `long` tygodni (bieżący tydzień wliczony — tylko przeszłość)."""
    sd = foreign_index(prices).diff().rolling(short, min_periods=short - 3).std()
    ref = sd.rolling(long, min_periods=long // 2).median()
    on = (sd > mult * ref).to_numpy()
    return np.where(np.isfinite(sd.to_numpy()) & np.isfinite(ref.to_numpy()), on, False)


def overlay_on(prices: pd.DataFrame, overlay: str) -> np.ndarray | None:
    if overlay in ("Z26", "Z52"):
        return valve_on(prices, int(overlay[1:]))
    if overlay == "H":
        return brake_on(prices)
    return None


def pln_floor(W: np.ndarray, on: np.ndarray, pln: int, floor: float = PLN_CAP_VALVE) -> tuple[np.ndarray, np.ndarray]:
    """W tygodniach z włączonym zaworem/hamulcem PLN ma co najmniej `floor`, reszta proporcjonalnie mniej (waluty obce dalej
    ≤ 50%). Zwraca (cele, limity): limit PLN = `floor` w tych tygodniach, inaczej CAP."""
    W = np.asarray(W, float).copy()
    caps = np.full(W.shape, CAP)
    for t in np.flatnonzero(on):
        p = W[t, pln]
        if p < floor:
            rest = 1.0 - p
            if rest > EPS:
                W[t] *= (1.0 - floor) / rest
            W[t, pln] = floor
        caps[t, pln] = floor
    return W, caps


@dataclass
class Plan:
    targets: pd.DataFrame
    orders: np.ndarray
    caps: np.ndarray | None = None        # T×N; None = CAP wszędzie
    no_loss: np.ndarray | bool = False    # tydzień po tygodniu: czy działa „nie sprzedawaj na stracie”
    on: np.ndarray | None = None          # tydzień po tygodniu: czy działa zawór / hamulec


@dataclass
class Sim:
    value: pd.Series        # wartość w PLN w chwili decyzji, przed przewalutowaniem (po cenach wykonania)
    units: pd.DataFrame     # jednostki po przewalutowaniu
    weights: pd.DataFrame   # udziały po przewalutowaniu
    ret: pd.Series          # ln value_{t+1} − ln value_t (indeks t)
    trades: int


def variant_plan(prices: pd.DataFrame, elig: pd.DataFrame, v: Variant, base: dict | None = None) -> Plan:
    """Plan wariantu statycznego: cele metody podstawowej (z `base`, gdy już policzone) i nakładka (D-065)."""
    key = v.base
    if base is not None and key in base:
        W, orders = base[key]
    else:
        W, orders = variant_targets(prices, elig, VARIANT_BY_ID[key])
        if base is not None:
            base[key] = (W, orders)
    on = overlay_on(prices, v.overlay)
    if on is not None:
        Wf, caps = pln_floor(W.to_numpy(float), on, list(prices.columns).index(BASE))
        return Plan(pd.DataFrame(Wf, index=W.index, columns=W.columns), orders, caps, False, on)
    return Plan(W, orders, None, v.overlay == "S", None)


def variant_targets(prices: pd.DataFrame, elig: pd.DataFrame, v: Variant) -> tuple[pd.DataFrame, np.ndarray]:
    """Cele i kolejność (od najwyższej oceny) metody podstawowej wariantu, tydzień po tygodniu (bez nakładki)."""
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


def loss_hold(units: np.ndarray, cost: np.ndarray, last_px: np.ndarray, target: np.ndarray, cap=CAP) -> np.ndarray:
    """D-065 „nie sprzedawaj na stracie”: koszyk z kursem poniżej średniej ceny zakupu, który metoda chce zmniejszyć,
    zostaje bez sprzedaży — chyba że jest ponad limitem (wtedy sprzedaż do limitu)."""
    px = np.where(np.isfinite(last_px), last_px, 0.0)
    V = float(units @ px)
    cur = units * px / V if V > 0 else np.zeros(len(units))
    c = np.broadcast_to(np.asarray(cap, float), cur.shape)
    with np.errstate(invalid="ignore"):
        loss = np.isfinite(cost) & (cost > 0) & (px > 0) & (px < cost)
    return loss & (target < cur - 1e-12) & (cur <= c + EPS) & (units > 0)


def update_cost(cost: np.ndarray, before: np.ndarray, after: np.ndarray, px: np.ndarray) -> np.ndarray:
    """Średnia cena zakupu: dokupienie uśrednia, sprzedaż jej nie zmienia, zero jednostek ją kasuje."""
    c = np.asarray(cost, float).copy()
    buy = after > before + 1e-12
    old = np.where(np.isfinite(c), c, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        c[buy] = (before[buy] * old[buy] + (after[buy] - before[buy]) * px[buy]) / after[buy]
    c[after <= 1e-12] = np.nan
    return c


def trade(units: np.ndarray, raw_px: np.ndarray, last_px: np.ndarray, target: np.ndarray, order: np.ndarray,
          band: float = BAND, cap=CAP, hold: np.ndarray | None = None) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """Jedno przeliczenie (to samo w badaniu i na żywo): wycena jednostek po ostatnich znanych cenach, koszyk bez ceny
    w dniu decyzji zamrożony (także `hold` — „nie sprzedawaj na stracie”), `rebalance` do celu; zmieniają się tylko
    koszyki, którym zmienia się udział. Zwraca (nowe jednostki, wartość, zamrożone, zmienione)."""
    px = np.where(np.isfinite(last_px), last_px, 0.0)
    V = float(units @ px)
    frozen = ~np.isfinite(raw_px)
    if hold is not None:
        frozen = frozen | np.asarray(hold, bool)
    cur = units * px / V if V > 0 else np.zeros(len(units))
    new = rebalance(cur, target, order, frozen, band, cap)
    chg = ~frozen & (px > 0) & (np.abs(new - cur) > 1e-12)
    nu = units.copy()
    nu[chg] = new[chg] * V / px[chg]
    assert V <= 0 or abs(float(nu @ px) - V) <= 1e-7 * V, "przeliczenie zmieniło wartość portfela (bez kosztów musi być ta sama)"
    return nu, V, frozen, chg


def simulate_plan(exe: pd.DataFrame, plan: Plan, band: float = BAND, v0: float = START_PLN, start: int = 0,
                  end: int | None = None) -> Sim:
    return simulate(exe, plan.targets, plan.orders, band, CAP, v0, start, end, caps=plan.caps, no_loss=plan.no_loss)


def simulate(exe: pd.DataFrame, targets: pd.DataFrame, orders: np.ndarray | None = None, band: float = BAND,
             cap: float = CAP, v0: float = START_PLN, start: int = 0, end: int | None = None,
             caps: np.ndarray | None = None, no_loss: np.ndarray | bool = False) -> Sim:
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
    cost = np.full(N, np.nan)
    nl = np.broadcast_to(np.asarray(no_loss, bool), (len(P),))
    for t in range(start, T):
        o = orders[t] if orders is not None else _order(Tg[t])
        cv = caps[t] if caps is not None else cap
        hold = loss_hold(units, cost, last[t], Tg[t], cv) if nl[t] else None
        before = units
        units, V, _, chg = trade(units, P[t], last[t], Tg[t], o, band, cv, hold)
        px = np.where(np.isfinite(last[t]), last[t], 0.0)
        cost = update_cost(cost, before, units, px)
        cost[cols.index(BASE)] = np.nan
        vals[t] = V
        trades += int(chg.sum())
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


def switcher_plan(rets: pd.DataFrame, plans: dict[str, Plan], equal: pd.DataFrame, start: int, every: int = SWITCH_EVERY,
                  lookback: int = SWITCH_LOOKBACK) -> tuple[Plan, pd.Series]:
    """Przełącznik: co `every` tygodni od `start` wybiera wariant o najwyższej mierze (Sharpe przekazanych tygodniowych
    zwrotów — D-065: zwroty kapitału w PLN) z ostatnich `lookback` tygodni (tylko wiersze < t — znane w chwili decyzji);
    remis → pierwszy w VARIANTS; przed `lookback` tygodniami — równy podział. Przejmuje cele, kolejność, limity
    i „nie sprzedawaj na stracie” wybranego wariantu."""
    idx = equal.index
    T = len(idx)
    N = equal.shape[1]
    W = equal.to_numpy(float).copy()
    order = np.tile(np.arange(N), (T, 1))
    caps = np.full((T, N), CAP)
    nl = np.zeros(T, bool)
    on = np.zeros(T, bool)
    chosen = pd.Series("equal", index=idx, dtype=object)
    ids = [v.id for v in STATIC if v.id in plans]
    pick = "equal"
    ex = rets.reindex(idx)
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
            pl = plans[pick]
            W[t] = pl.targets.iloc[t].to_numpy(float)
            order[t] = pl.orders[t]
            if pl.caps is not None:
                caps[t] = pl.caps[t]
            nl[t] = bool(np.broadcast_to(np.asarray(pl.no_loss, bool), (T,))[t])
            on[t] = bool(pl.on[t]) if pl.on is not None else False
    return Plan(pd.DataFrame(W, index=idx, columns=equal.columns), order, caps, nl, on), chosen


def switcher_targets(rets: pd.DataFrame, static: dict[str, pd.DataFrame], equal: pd.DataFrame, start: int,
                     static_orders: dict[str, np.ndarray] | None = None, every: int = SWITCH_EVERY,
                     lookback: int = SWITCH_LOOKBACK) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """Zgodność wstecz: przełącznik na samych celach (bez limitów i nakładek)."""
    T, N = equal.shape
    plans = {k: Plan(w, static_orders[k] if static_orders else np.tile(np.arange(N), (T, 1))) for k, w in static.items()}
    plan, chosen = switcher_plan(rets, plans, equal, start, every, lookback)
    return plan.targets, chosen, plan.orders


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
