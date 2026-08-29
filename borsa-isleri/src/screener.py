"""Fiyat bazlı fırsat tarama (screener).

Sadece fiyat/hacim verisiyle çalışır (elimizdeki veri bu): bir hissenin
"uzun süredir ucuz" (52 haftalık dibe yakın) VE "yatay" (son N ayda dar
bantta) olup olmadığını, RSI ile birlikte değerlendirir. Eşikler
`config.SCREENER_SETTINGS`'te tutulur — ileride birlikte ince ayar
yapılabilir.

Not: Bu, YATIRIM TAVSİYESİ değildir — sadece dikkat çekici adayları öne
çıkaran basit bir filtredir. Karar kullanıcıya aittir.
"""

import pandas as pd

try:
    from .config import SCREENER_SETTINGS
except ImportError:
    from config import SCREENER_SETTINGS


def _rsi(close: pd.Series, period: int) -> pd.Series:
    """Basit (Wilder) RSI hesaplaması, ekstra bağımlılık gerektirmez."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_symbol_metrics(df: pd.DataFrame, settings: dict | None = None) -> dict | None:
    """Bir sembolün fiyat geçmişinden (storage.read_prices çıktısı) tarama
    metriklerini hesaplar. Yetersiz veri varsa None döner.
    """
    settings = settings or SCREENER_SETTINGS
    lookback = settings["lookback_days_52w"]
    sideways_window = settings["sideways_window_days"]

    if df.empty or len(df) < min(lookback, sideways_window, 30):
        return None

    close = df["close"]
    current_price = float(close.iloc[-1])

    window_52w = close.iloc[-lookback:]
    low_52w = float(window_52w.min())
    high_52w = float(window_52w.max())

    pct_from_low = (current_price - low_52w) / low_52w * 100 if low_52w else float("nan")
    pct_from_high = (current_price - high_52w) / high_52w * 100 if high_52w else float("nan")

    sideways_window_data = close.iloc[-sideways_window:]
    sw_low = float(sideways_window_data.min())
    sw_high = float(sideways_window_data.max())
    sideways_range_pct = (sw_high - sw_low) / sw_low * 100 if sw_low else float("nan")

    rsi_series = _rsi(close, settings["rsi_period"])
    rsi_value = float(rsi_series.iloc[-1])

    is_candidate = (
        pct_from_low <= settings["near_low_threshold_pct"]
        and sideways_range_pct <= settings["sideways_threshold_pct"]
        and settings["rsi_min"] <= rsi_value <= settings["rsi_max"]
    )

    return {
        "current_price": current_price,
        "pct_from_52w_low": round(pct_from_low, 1),
        "pct_from_52w_high": round(pct_from_high, 1),
        "sideways_range_pct": round(sideways_range_pct, 1),
        "rsi": round(rsi_value, 1),
        "aday_mi": is_candidate,
    }


def screen_symbols(symbol_category_pairs: list[tuple[str, str]], storage_module, conn) -> pd.DataFrame:
    """Verilen (sembol, kategori) çiftleri için tarama sonuçlarını döner.

    `storage_module`, `read_prices(conn, symbol)` fonksiyonuna sahip modül
    (borsa-isleri/src/storage.py) — çağıran taraf import edip geçirir, burada
    yeniden import edilmez (workspace tarafındaki paket takma adı çakışmasını
    önlemek için).
    """
    rows = []
    for symbol, category in symbol_category_pairs:
        df = storage_module.read_prices(conn, symbol)
        metrics = compute_symbol_metrics(df)
        if metrics is None:
            continue
        rows.append({"symbol": symbol, "kategori": category, **metrics})

    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol", "kategori", "current_price", "pct_from_52w_low",
                "pct_from_52w_high", "sideways_range_pct", "rsi", "aday_mi",
            ]
        )

    result = pd.DataFrame(rows)
    return result.sort_values(["aday_mi", "pct_from_52w_low"], ascending=[False, True]).reset_index(drop=True)
