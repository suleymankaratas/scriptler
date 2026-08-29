"""Fırsat tarama (screener) — iki farklı bakış açısı sunar.

1. `screen_symbols` — "uzun süredir ucuz" (52 haftalık dibe yakın) VE
   "yatay" (son N ayda dar bantta) hisseleri RSI ile birlikte değerlendirir.
2. `screen_chart_opportunities` ("Grafik Fırsatı") — temel verilerden (defter
   değeri vb.) bağımsız, sadece fiyat grafiğine bakarak: dolar bazında 2 veya
   5 yıl önceki seviyesine gerilemiş, zirveden ciddi düşmüş VE şu an yatayda
   olan sembolleri işaretler. BIST hisseleri için TL fiyatı USDTRY=X ile
   dolar bazına çevrilir (Türk hisselerinin TL bazında "yükseliyormuş gibi"
   görünüp aslında enflasyon/kur nedeniyle reel olarak gerilemiş olmasını
   hesaba katmak için).

İkisi de sadece fiyat/hacim verisiyle çalışır (elimizdeki veri bu). Eşikler
`config.SCREENER_SETTINGS`'te tutulur — ileride birlikte ince ayar
yapılabilir. Her iki tarama da adaylar için okunabilir bir "aciklama"
(neden aday işaretlendiği) üretir.

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

    # Her sembol için (aday olsun olmasın) betimleyici bir yorum üretilir —
    # dibe/zirveye uzaklık, yatay/oynak olup olmadığı, RSI bölgesi.
    yakinlik = "yakın" if pct_from_low <= settings["near_low_threshold_pct"] else "uzak"
    bant_durumu = "dar/yatay" if sideways_range_pct <= settings["sideways_threshold_pct"] else "geniş/oynak"
    if rsi_value < settings["rsi_min"]:
        rsi_durumu = "aşırı satım bölgesinde"
    elif rsi_value > settings["rsi_max"]:
        rsi_durumu = "aşırı alım bölgesinde"
    else:
        rsi_durumu = "nötr bölgede"

    aciklama = (
        f"52 haftalık dibin %{pct_from_low:.1f} üzerinde ({yakinlik}, zirveden %{abs(pct_from_high):.0f} geride), "
        f"son ~{sideways_window} günde %{sideways_range_pct:.1f} bandında ({bant_durumu}) seyrediyor, "
        f"RSI {rsi_value:.0f} ({rsi_durumu})."
    )
    if is_candidate:
        aciklama += " → Fırsat kriterlerinin hepsini karşılıyor."

    return {
        "current_price": current_price,
        "pct_from_52w_low": round(pct_from_low, 1),
        "pct_from_52w_high": round(pct_from_high, 1),
        "sideways_range_pct": round(sideways_range_pct, 1),
        "rsi": round(rsi_value, 1),
        "aday_mi": is_candidate,
        "aciklama": aciklama,
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
                "sira", "symbol", "kategori", "current_price", "pct_from_52w_low",
                "pct_from_52w_high", "sideways_range_pct", "rsi", "aday_mi", "aciklama",
            ]
        )

    result = pd.DataFrame(rows)

    # "Fırsat skoru": düşük olması daha avantajlı demek (dibe daha yakın,
    # daha dar/yatay bant, daha nötr/düşük RSI). Sadece sıralama ve "Sıra"
    # numarası için kullanılır, ekranda ayrı bir sütun olarak gösterilmez.
    # TÜM semboller (aday olsun olmasın) bu skora göre en avantajlıdan en
    # avantajsıza sıralanır — "aday_mi" ayrı, sabit bir eşik bilgisidir.
    score = result["pct_from_52w_low"] + result["sideways_range_pct"] + result["rsi"]
    result = result.assign(_skor=score).sort_values("_skor", ascending=True).drop(columns="_skor").reset_index(drop=True)
    result.insert(0, "sira", range(1, len(result) + 1))
    return result


def _to_usd(df: pd.DataFrame, usdtry_df: pd.DataFrame | None) -> pd.Series:
    """BIST (TL bazlı) sembollerin kapanış fiyatını USDTRY kuruna bölerek
    dolar bazına çevirir. usdtry_df yoksa/boşsa TL fiyatı olduğu gibi döner
    (dolara çevrilmeden) — bu durumda çağıran taraf sonucu yorumlarken dikkatli
    olmalı.
    """
    if usdtry_df is None or usdtry_df.empty:
        return df["close"]

    merged = pd.merge(
        df[["date", "close"]],
        usdtry_df[["date", "close"]].rename(columns={"close": "usdtry"}),
        on="date",
        how="left",
    )
    merged["usdtry"] = merged["usdtry"].ffill().bfill()
    return merged["close"] / merged["usdtry"]


def compute_chart_opportunity(
    df: pd.DataFrame,
    usdtry_df: pd.DataFrame | None,
    is_try_denominated: bool,
    settings: dict | None = None,
) -> dict | None:
    """"Grafik Fırsatı": temel verilerden (defter değeri vb.) bağımsız,
    sadece fiyat grafiğine bakarak — dolar bazında 2 veya 5 yıl önceki
    seviyesine gerilemiş, zirveden ciddi düşmüş VE şu an yatayda olan
    sembolleri işaretler.
    """
    settings = settings or SCREENER_SETTINGS
    sideways_window = settings["sideways_window_days"]

    if df.empty or len(df) < 60:
        return None

    close = _to_usd(df, usdtry_df) if is_try_denominated else df["close"]
    current_price = float(close.iloc[-1])
    if not current_price:
        return None

    lookbacks = settings["chart_opportunity_lookback_days"]
    flat_threshold = settings["flat_vs_past_threshold_pct"]

    pct_vs_past: dict[str, float | None] = {}
    near_past: dict[str, bool] = {}
    for label, days in lookbacks.items():
        if len(close) > days:
            past_price = float(close.iloc[-days])
            pct = (current_price - past_price) / past_price * 100 if past_price else None
        else:
            pct = None
        pct_vs_past[label] = round(pct, 1) if pct is not None else None
        near_past[label] = pct is not None and abs(pct) <= flat_threshold

    peak = float(close.max())
    drawdown_from_peak_pct = (current_price - peak) / peak * 100 if peak else 0.0

    window = close.iloc[-sideways_window:]
    sw_low, sw_high = float(window.min()), float(window.max())
    sideways_range_pct = (sw_high - sw_low) / sw_low * 100 if sw_low else float("nan")

    has_major_decline = drawdown_from_peak_pct <= settings["major_decline_threshold_pct"]
    is_sideways = sideways_range_pct <= settings["sideways_threshold_pct"]
    returned_to_old_price = any(near_past.values())

    is_candidate = returned_to_old_price and has_major_decline and is_sideways

    # Her sembol için (aday olsun olmasın) betimleyici bir yorum üretilir.
    vs_parcalari = [
        f"{label} önceye göre %{pct:+.1f}" for label, pct in pct_vs_past.items() if pct is not None
    ]
    vs_ozeti = ", ".join(vs_parcalari) if vs_parcalari else "yeterli geçmiş veri yok"
    bant_durumu = "dar/yatay" if is_sideways else "geniş/oynak"
    dusus_durumu = "ciddi bir düşüş yaşamış" if has_major_decline else "zirveden belirgin uzaklaşmamış"

    aciklama = (
        f"Dolar bazlı fiyat: {vs_ozeti}. Zirveden %{abs(drawdown_from_peak_pct):.0f} geride "
        f"({dusus_durumu}), son ~{sideways_window} günde %{sideways_range_pct:.1f} bandında ({bant_durumu}) "
        "(temel veriden bağımsız, sadece fiyat grafiğine bakılmıştır)."
    )
    if is_candidate:
        seviye_parcalari = [label for label, near in near_past.items() if near]
        seviyeler = " ve ".join(seviye_parcalari)
        aciklama += f" → {seviyeler} önceki seviyeye dönüş + ciddi düşüş + yatay: fırsat kriterlerinin hepsini karşılıyor."

    result = {
        "current_price_usd": round(current_price, 2),
        "drawdown_from_peak_pct": round(drawdown_from_peak_pct, 1),
        "sideways_range_pct": round(sideways_range_pct, 1),
        "aday_mi": is_candidate,
        "aciklama": aciklama,
    }
    for label in lookbacks:
        result[f"vs_{label}"] = pct_vs_past[label]
    return result


def screen_chart_opportunities(
    symbol_category_pairs: list[tuple[str, str]], storage_module, conn
) -> pd.DataFrame:
    """Tüm sembolleri "Grafik Fırsatı" mantığıyla tarar (bkz.
    `compute_chart_opportunity`). BIST sembolleri (".IS") otomatik olarak
    USDTRY=X ile dolar bazına çevrilir.
    """
    usdtry_df = storage_module.read_prices(conn, "USDTRY=X")

    rows = []
    for symbol, category in symbol_category_pairs:
        if symbol == "USDTRY=X":
            continue
        df = storage_module.read_prices(conn, symbol)
        is_try = symbol.endswith(".IS")
        metrics = compute_chart_opportunity(df, usdtry_df if is_try else None, is_try)
        if metrics is None:
            continue
        rows.append({"symbol": symbol, "kategori": category, **metrics})

    if not rows:
        return pd.DataFrame(
            columns=[
                "sira", "symbol", "kategori", "current_price_usd", "vs_2 yıl", "vs_5 yıl",
                "drawdown_from_peak_pct", "sideways_range_pct", "aday_mi", "aciklama",
            ]
        )

    result = pd.DataFrame(rows)

    # "Fırsat skoru": düşük olması daha avantajlı demek (eski fiyat seviyesine
    # daha tam gelmiş VE daha dar/yatay bant). TÜM semboller bu skora göre
    # sıralanır — "aday_mi" ayrı, sabit bir eşik bilgisidir.
    proximity = result[["vs_2 yıl", "vs_5 yıl"]].apply(pd.to_numeric, errors="coerce").abs().min(axis=1, skipna=True)
    score = result["sideways_range_pct"] + proximity.fillna(proximity.max() if proximity.notna().any() else 0)
    result = result.assign(_skor=score).sort_values("_skor", ascending=True).drop(columns="_skor").reset_index(drop=True)
    result.insert(0, "sira", range(1, len(result) + 1))
    return result
