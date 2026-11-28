"""D-076: prognoza zasięgu ruchu (ind.range_forecast) i ściśnięcie (ind.squeeze) — wzór, brak look-ahead, sens prognozy."""
import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind


def regime_days(n=2500, seed=5):
    """Świece dzienne z przełączaną zmiennością (spokój ↔ nerwowość, jak na rynku) — kierunek losowy."""
    rng = np.random.default_rng(seed)
    vol = np.empty(n)
    v = 0.006
    for i in range(n):
        v = np.exp(0.97 * np.log(v) + 0.03 * np.log(0.006) + rng.normal(0, 0.12))
        vol[i] = v
    c = 1.1 * np.exp(np.cumsum(rng.normal(0, vol)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.random(n) * vol)
    lo = np.minimum(o, c) * (1 - rng.random(n) * vol)
    idx = pd.date_range("2010-01-04", periods=n, freq="B", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c}, index=idx)


@pytest.fixture(scope="module")
def days():
    return regime_days()


def test_matches_plain_least_squares(days):
    h = 3
    f = ind.range_forecast(days, h)
    x, m20 = ind._range_features(days)
    real = ind.realized_range(days, h).to_numpy()
    y = np.log(real / (h * m20))
    for t in (400, 1200, 2400):
        rows = [s for s in range(t - h + 1) if np.isfinite(y[s]) and np.isfinite(x[s]).all()]
        beta = np.linalg.lstsq(x[rows], y[rows], rcond=None)[0]
        mid = h * m20[t] * np.exp(x[t] @ beta)
        assert f["mid"].iloc[t] == pytest.approx(mid, rel=1e-6)


def test_no_lookahead(days):
    full = ind.range_forecast(days, 3)
    for cut in (600, 1500, 2200):
        part = ind.range_forecast(days.iloc[:cut], 3)
        a, b = full.iloc[:cut].to_numpy(), part.to_numpy()
        assert np.array_equal(np.isnan(a), np.isnan(b))
        assert np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], rtol=1e-10)
    # zaburzenie przyszłości nie rusza prognoz sprzed niej
    up = days.copy()
    up.iloc[1800:] *= 1.3
    assert np.allclose(ind.range_forecast(up, 3).iloc[:1800].dropna(), full.iloc[:1800].dropna())


def test_forecast_beats_naive_and_band_covers(days):
    h = 3
    f = ind.range_forecast(days, h)
    real = ind.realized_range(days, h)
    ok = f["mid"].notna() & real.notna()
    err_model = np.abs(np.log(real[ok] / f["mid"][ok]))
    naive = f["base"][ok] * np.exp(np.median(np.log(real[ok] / f["base"][ok])))   # najlepsza stała wobec średniego zakresu
    err_naive = np.abs(np.log(real[ok] / naive))
    assert err_model.mean() < err_naive.mean()
    cover = ((real[ok] >= f["low"][ok]) & (real[ok] <= f["high"][ok])).mean()
    assert 0.72 < cover < 0.88


def test_squeeze_box():
    df = pd.DataFrame({"high": [5, 6, 7, 6.5, 6.2, 9.0], "low": [4, 5, 5.5, 5.8, 5.9, 6.1], "open": 5.0, "close": 5.0})
    s = ind.squeeze(df, 3, 3)
    assert s["upper"].iloc[4] == 7 and s["lower"].iloc[4] == 5.5 and s["height"].iloc[4] == pytest.approx(1.5)
    assert s["pct"].iloc[4] == pytest.approx(100 / 3)   # najwęższe z 3 ostatnich pudełek
