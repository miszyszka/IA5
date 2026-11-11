"""REV (D-063): oceny przeceny i trendu względem koszyka — bez look-ahead, odporne na pułapkę inflacji."""
import numpy as np
import pandas as pd
import pytest
from ia5 import rev_method as rm


def panel(cols: dict[str, np.ndarray]) -> pd.DataFrame:
    n = len(next(iter(cols.values())))
    idx = 1_700_000_000 + 7 * 86400 * np.arange(n)
    df = pd.DataFrame(cols, index=idx)
    df["PLN"] = 1.0
    return df


def test_basket_index_no_jump_when_currency_joins():
    n = 40
    c = np.full(n, np.nan)
    c[20:] = 7.0
    p = panel({"A": np.full(n, 2.0), "B": np.full(n, 0.5), "C": c})
    assert np.allclose(rm.basket_index(p).to_numpy(), 0.0)


def test_pln_is_minus_basket():
    rng = np.random.default_rng(0)
    p = panel({"A": np.exp(np.cumsum(rng.normal(0, 0.01, 60))), "B": np.exp(np.cumsum(rng.normal(0, 0.01, 60)))})
    x = rm.relative(p)
    assert np.allclose(x["PLN"].to_numpy(), -rm.basket_index(p).to_numpy())
    assert np.allclose((np.log(p["A"]) - rm.basket_index(p)).to_numpy(), x["A"].to_numpy())


def test_inflation_trend_is_not_cheap():
    rng = np.random.default_rng(1)
    n = 400
    k = np.arange(n)
    x = pd.DataFrame({"TRY": -0.25 * k / 52 + rng.normal(0, 0.01, n)})   # −25%/rok, szum 1%/tydz. wokół trendu
    v = rm.score_value(x, 5)["TRY"]
    assert v.abs().iloc[-60:].max() < 3.5                                # stały spadek to trend, nie przecena
    naive = -(x["TRY"] - x["TRY"].rolling(260).mean()) / x["TRY"].rolling(260).std()
    assert naive.iloc[-60:].min() > 1.6                                   # średnia z 5 lat widziałaby wieczną przecenę
    flat = np.log(1 + rng.normal(0, 0.003, n))
    flat[-8:] += np.linspace(0, np.log(0.85), 8)                          # płasko 5 lat, potem −15% w 8 tygodni
    v = rm.score_value(pd.DataFrame({"CHF": flat}), 5)["CHF"].iloc[-1]
    assert v > 2


def test_momentum_skip_month():
    x = np.zeros(60)
    x[-4:] = np.linspace(0.01, 0.04, 4)
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 1e-4, 60)
    df = pd.DataFrame({"A": x + noise})
    df.iloc[:-4, 0] = noise[:-4]                       # stałe 48+ tygodni, potem rośnie przez 4
    m12 = rm.score_momentum(df, 12)["A"].iloc[-1]
    m3 = rm.score_momentum(df, 3)["A"].iloc[-1]
    assert abs(m12) < 0.1 and m3 > 2                    # ostatni miesiąc nie wchodzi do trendu rocznego


def test_combo_is_mean_of_cross_section_z():
    rng = np.random.default_rng(3)
    p = panel({c: np.exp(np.cumsum(rng.normal(0, 0.01, 300))) for c in "ABCDE"})
    x = rm.relative(p)
    v, t = rm.score_value(x, 3), rm.score_momentum(x, 3)
    combo = rm.score(x, "V3M3")
    row = combo.index[-1]
    zv = (v.loc[row] - v.loc[row].mean()) / v.loc[row].std(ddof=0)
    zt = (t.loc[row] - t.loc[row].mean()) / t.loc[row].std(ddof=0)
    assert np.allclose(combo.loc[row].to_numpy(), (0.5 * zv + 0.5 * zt).to_numpy())


@pytest.mark.parametrize("name", rm.SCORES)
def test_scores_no_lookahead(name):
    rng = np.random.default_rng(4)
    n = 420
    p = panel({c: np.exp(np.cumsum(rng.normal(0, 0.012, n))) for c in "ABCDEF"})
    p.iloc[50:70, 2] = np.nan
    full = rm.score(rm.relative(p), name)
    for t in rng.choice(np.arange(300, n - 2), 15, replace=False):
        q = p.copy()
        q.iloc[t + 1:, :-1] *= np.exp(rng.normal(0, 0.2, (n - t - 1, p.shape[1] - 1)))
        cut = rm.score(rm.relative(q), name)
        a, b = full.iloc[: t + 1].to_numpy(), cut.iloc[: t + 1].to_numpy()
        assert np.allclose(a, b, equal_nan=True), (name, t)


def test_eligible_after_260_weeks():
    n = 600
    a = np.ones(n)
    b = np.full(n, np.nan)
    b[100:] = 1.0
    c = np.ones(n)
    c[300:340] = np.nan                                   # 40 tygodni braku > 8% okna
    e = rm.eligible(panel({"A": a, "B": b, "C": c}))
    assert not e["A"].iloc[259] and e["A"].iloc[260]
    assert not e["B"].iloc[359] and e["B"].iloc[360]
    assert e["C"].iloc[299] and not e["C"].iloc[339] and e["C"].iloc[-1]
    assert e["PLN"].all()
