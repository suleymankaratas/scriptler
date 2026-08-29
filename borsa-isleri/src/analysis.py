"""Tek bir sembol için ayrıntılı teknik analiz: destek/direnç, Fibonacci,
trend ve bunları özetleyen yazılı bir yorum.

Sadece SEÇİLİ TEK BİR sembol için çağrılır (tüm evrende değil) — burada
kullanılan yerel tepe/dip taraması, yüzlerce sembolde çalıştırılamayacak
kadar ağırdır; `screener.py`'deki (tüm sembolleri tarayan) hafif/vektörel
metriklerden farklıdır.

Not: Bu bir YATIRIM TAVSİYESİ değildir. Destek/direnç/Fibonacci seviyeleri
"burada al/sat" emri değil, geçmişte fiyatın tepki verdiği veya standart
teknik analiz yöntemleriyle hesaplanan REFERANS noktalarıdır. Karar ve
inceleme kullanıcıya aittir.
"""

import pandas as pd

try:
    from .config import SCREENER_SETTINGS
except ImportError:
    from config import SCREENER_SETTINGS


def find_support_resistance(df: pd.DataFrame, window: int = 5, num_levels: int = 3) -> dict:
    """Yerel tepe/dip noktalarından güncel fiyata en yakın destek/direnç
    seviyelerini bulur.

    Yöntem: her nokta, kendisinden `window` gün önce ve sonraki en yüksek/
    düşük değerse yerel bir tepe/dip sayılır. Birbirine çok yakın (±%1.5)
    seviyeler tek bir seviyede kümelenir (aynı bölgeyi tekrar tekrar
    saymamak için).
    """
    close = df["close"].reset_index(drop=True)
    n = len(close)
    if n < window * 2 + 1:
        return {"support": [], "resistance": []}

    current_price = float(close.iloc[-1])
    highs: list[float] = []
    lows: list[float] = []

    for i in range(window, n - window):
        segment = close.iloc[i - window : i + window + 1]
        value = close.iloc[i]
        if value == segment.max():
            highs.append(float(value))
        if value == segment.min():
            lows.append(float(value))

    def cluster(levels: list[float]) -> list[float]:
        if not levels:
            return []
        levels = sorted(levels)
        clusters: list[list[float]] = [[levels[0]]]
        for lvl in levels[1:]:
            if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] <= 0.015:
                clusters[-1].append(lvl)
            else:
                clusters.append([lvl])
        return [sum(c) / len(c) for c in clusters]

    resistance = sorted(lvl for lvl in cluster(highs) if lvl > current_price)[:num_levels]
    support = sorted((lvl for lvl in cluster(lows) if lvl < current_price), reverse=True)[:num_levels]
    return {"support": support, "resistance": resistance}


def fibonacci_levels(df: pd.DataFrame, lookback_days: int = 252) -> dict:
    """Pencere içindeki en yüksek/düşük noktadan standart Fibonacci geri
    çekilme seviyelerini hesaplar (yüksekten alçağa doğru).
    """
    close = df["close"].iloc[-lookback_days:]
    if close.empty:
        return {}
    high = float(close.max())
    low = float(close.min())
    diff = high - low
    ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    return {f"%{r * 100:.1f}": round(high - diff * r, 2) for r in ratios}


def compute_trend(df: pd.DataFrame) -> str:
    """SMA50/SMA200 ilişkisine göre basit bir trend sınıflaması."""
    close = df["close"]
    if len(close) < 200:
        return "Yetersiz veri (uzun vadeli trend için en az ~200 günlük geçmiş gerekir)"

    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    current = float(close.iloc[-1])

    if sma50 > sma200 and current >= sma50:
        return "Yükseliş (kısa vadeli ortalama uzun vadelinin üzerinde, fiyat da öyle)"
    if sma50 < sma200 and current <= sma50:
        return "Düşüş (kısa vadeli ortalama uzun vadelinin altında, fiyat da öyle)"
    return "Yatay / Karışık (net bir yön yok)"


def analyze_symbol(
    df: pd.DataFrame,
    is_try_denominated: bool,
    usdtry_df: pd.DataFrame | None = None,
    settings: dict | None = None,
) -> dict | None:
    """Tek bir sembol için tüm teknik analizi birleştirir ve okunabilir bir
    yorum metni üretir.
    """
    if df.empty or len(df) < 30:
        return None

    settings = settings or SCREENER_SETTINGS
    current_price = float(df["close"].iloc[-1])

    sr = find_support_resistance(df)
    fib = fibonacci_levels(df, settings["lookback_days_52w"])
    trend = compute_trend(df)

    # --- Yazılı yorum ---
    parts = [f"Trend: {trend}."]

    if sr["support"]:
        destek_str = ", ".join(f"{lvl:.2f}" for lvl in sr["support"])
        parts.append(f"En yakın destek seviye(ler)i: {destek_str}.")
    else:
        parts.append("Yakın bir destek seviyesi tespit edilemedi.")

    if sr["resistance"]:
        direnc_str = ", ".join(f"{lvl:.2f}" for lvl in sr["resistance"])
        parts.append(f"En yakın direnç seviye(ler)i: {direnc_str}.")
    else:
        parts.append("Yakın bir direnç seviyesi tespit edilemedi.")

    if fib:
        # Fiyatın hangi iki Fibonacci seviyesi arasında olduğunu bul.
        sorted_fib = sorted(fib.items(), key=lambda kv: kv[1])
        below = [lvl for _, lvl in sorted_fib if lvl <= current_price]
        above = [lvl for _, lvl in sorted_fib if lvl >= current_price]
        if below and above:
            parts.append(
                f"Fibonacci geri çekilme seviyeleri arasında {below[-1]:.2f} ile {above[0]:.2f} bandında."
            )
        elif above:
            parts.append(f"Fibonacci bandının altında (%0 seviyesi {above[0]:.2f}).")
        elif below:
            parts.append(f"Fibonacci bandının üzerinde (%100 seviyesi {below[-1]:.2f}).")

    if is_try_denominated:
        parts.append(
            "BIST hissesi: TL bazlı fiyat enflasyon/kur etkisiyle yükeliyormuş gibi görünebilir — "
            "'Grafik Fırsatı' sekmesindeki dolar bazlı görünüme de bakmanı öneririz."
        )
    else:
        parts.append("Global hisse: fiyat zaten dolar bazlı, ek kur düzeltmesi gerekmez.")

    parts.append(
        "Destek/direnç/Fibonacci seviyeleri 'al/sat emri' değil, fiyatın geçmişte tepki verdiği veya "
        "standart yöntemlerle hesaplanan referans noktalarıdır — yatırım tavsiyesi değildir."
    )

    return {
        "current_price": current_price,
        "trend": trend,
        "support_levels": sr["support"],
        "resistance_levels": sr["resistance"],
        "fibonacci_levels": fib,
        "yorum": " ".join(parts),
    }
