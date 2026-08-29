"""Proje ayarları ve takip edilecek semboller.

Sembol formatı yfinance kurallarına göre:
- BIST hisseleri: "SEMBOL.IS" (örn. "THYAO.IS")
- Döviz paritesi: "USDTRY=X"
- Emtia (futures): "GC=F" (altın), "SI=F" (gümüş)
- Kripto: "BTC-USD", "ETH-USD"
- Global hisse/endeks: "AAPL", "^GSPC"

Kendi takip listeni oluşturmak için aşağıdaki listeleri düzenle.
"""

from pathlib import Path

# Proje kök dizini ve SQLite veritabanı yolu
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "market_data.db"

# Varlık sınıfına göre gruplanmış örnek takip listesi.
# Bunu kendi ilgi alanına göre genişletebilir/daraltabilirsin.
TICKERS = {
    "bist": ["THYAO.IS", "GARAN.IS", "ASELS.IS"],
    "forex_commodity": ["USDTRY=X", "GC=F", "SI=F"],
    "crypto": ["BTC-USD", "ETH-USD"],
    "global": ["AAPL", "MSFT", "^GSPC"],
}


def all_symbols() -> list[str]:
    """Tüm gruplardaki sembolleri tek bir düz liste halinde döner."""
    symbols: list[str] = []
    for group_symbols in TICKERS.values():
        symbols.extend(group_symbols)
    return symbols
