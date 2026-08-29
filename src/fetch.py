"""yfinance ile fiyat verisi çekme."""

import pandas as pd
import yfinance as yf


def fetch_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Bir sembol için geçmiş fiyat verisini çeker.

    period: "1mo", "3mo", "6mo", "1y", "5y", "max" vb.
    interval: "1d", "1h", "1wk" vb. (kısa interval'ler kısıtlı period ile gelir)
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    return df


def fetch_many(symbols: list[str], period: str = "1y", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """Birden fazla sembol için geçmiş veriyi çeker.

    Bir sembol başarısız olursa diğerlerini etkilemez; sonuç dict'inde
    o sembol için boş bir DataFrame yer alır ve hata konsola yazılır.
    """
    results: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        try:
            results[symbol] = fetch_history(symbol, period=period, interval=interval)
        except Exception as exc:  # noqa: BLE001 - tek bir sembol hatası tüm akışı durdurmasın
            print(f"[fetch] {symbol} çekilemedi: {exc}")
            results[symbol] = pd.DataFrame()
    return results
