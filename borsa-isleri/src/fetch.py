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
    """Birden fazla sembol için geçmiş veriyi çeker (sembol başına tek tek).

    Az sayıda sembol için uygundur (örn. tek bir kategori sayfası). Çok
    sayıda sembol (yüzlerce) için `fetch_many_bulk` kullan — çok daha hızlı.

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


def fetch_many_bulk(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
    batch_size: int = 50,
    on_progress=None,
) -> dict[str, pd.DataFrame]:
    """Yüzlerce sembolü verimli biçimde toplu (batch) olarak çeker.

    `yf.download` ile bir seferde `batch_size` kadar sembol çekilir (tek tek
    `Ticker.history()` çağırmaktan çok daha hızlıdır). Bir batch tamamen
    başarısız olursa sadece o batch'teki semboller boş DataFrame ile işaretlenir,
    diğer batch'ler etkilenmez.

    `on_progress`, verilirse her batch sonunda `on_progress(tamamlanan, toplam)`
    şeklinde çağrılır (ilerleme göstermek için).
    """
    results: dict[str, pd.DataFrame] = {}
    total = len(symbols)

    for start in range(0, total, batch_size):
        batch = symbols[start : start + batch_size]
        try:
            raw = yf.download(
                batch,
                period=period,
                interval=interval,
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
            for symbol in batch:
                if len(batch) == 1:
                    df = raw
                elif symbol in raw.columns.get_level_values(0):
                    df = raw[symbol]
                else:
                    df = pd.DataFrame()
                # ÖNEMLİ: farklı piyasalardan (örn. BIST + ABD) semboller aynı
                # batch'te birleşince, yf.download hepsini ortak bir tarih
                # eksenine hizalıyor — bir sembolün o gün işlem görmediği
                # tarihlerde (farklı tatil takvimleri) NaN satır oluşuyor.
                # Bunları burada eleriz ki DB'ye asla NaN kapanış yazılmasın.
                if not df.empty and "Close" in df.columns:
                    df = df[df["Close"].notna()]
                results[symbol] = df
        except Exception as exc:  # noqa: BLE001 - bir batch hatası diğerlerini durdurmasın
            print(f"[fetch] Batch çekilemedi ({batch[0]}...{batch[-1]}): {exc}")
            for symbol in batch:
                results[symbol] = pd.DataFrame()

        if on_progress is not None:
            on_progress(min(start + batch_size, total), total)

    return results
