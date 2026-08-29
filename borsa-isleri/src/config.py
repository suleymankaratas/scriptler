"""Proje ayarları ve takip edilecek semboller.

Sembol formatı yfinance kurallarına göre:
- BIST hisseleri: "SEMBOL.IS" (örn. "THYAO.IS")
- Döviz paritesi: "USDTRY=X"
- Emtia (futures): "GC=F" (altın), "SI=F" (gümüş), "CL=F" (petrol), "NG=F"
  (doğalgaz), "HG=F" (bakır)
- Kripto: "BTC-USD", "ETH-USD"
- Global hisse/endeks: "AAPL", "^GSPC"

Kendi takip listeni oluşturmak için aşağıdaki listeleri düzenle.

Not (BIST100/diger_bist listeleri hakkında): Bu listeler genel bilgiye
dayanarak hazırlanmış, makul ama resmi/güncel endeks üyeliğini garanti
etmeyen listelerdir (BIST100 üyeliği periyodik olarak değişir). Nasdaq-100 ve
S&P 500 listeleri ise `universe.py` tarafından güvenilir kaynaklardan
(pandas ile, LLM transkripsiyonu olmadan) otomatik çekilir — bkz. o dosya.
"""

from pathlib import Path

# Proje kök dizini ve SQLite veritabanı yolu
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "market_data.db"
UNIVERSE_CACHE_DIR = BASE_DIR / "data"

# BIST 100 (yaklaşık/makul liste — bkz. yukarıdaki not). ".IS" son eki
# aşağıda otomatik ekleniyor.
_BIST100_RAW = [
    "THYAO", "GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB", "TSKB",
    "SAHOL", "KCHOL", "SISE", "EREGL", "TUPRS", "PETKM", "ASELS", "TOASO",
    "FROTO", "OTKAR", "KARSN", "TTKOM", "TCELL", "ARCLK", "VESTL", "BIMAS",
    "MGROS", "SOKM", "ULKER", "CCOLA", "AEFES", "TATGD", "PGSUS", "TAVHL",
    "DOAS", "CIMSA", "AKCNS", "ENKAI", "TKFEN", "GUBRF",
    "AGHOL", "ALARK", "ZOREN", "AKSEN", "AKSA", "KONTR", "ASTOR", "SASA",
    "BRSAN", "BRYAT", "EGEEN", "HEKTS", "TRGYO", "EKGYO", "ISGYO", "KRDMD",
    "ISDMR", "DOHOL", "LOGO", "NETAS", "MAVI", "MPARK", "ECILC", "DEVA",
    "SELEC", "TMSN", "YATAS", "ANHYT", "ANSGR", "AGESA", "TURSG", "GESAN",
    "ALFAS", "SMRTG", "ODAS", "AYDEM", "NTHOL", "CLEBI", "VESBE", "PENTA",
    "SDTTR", "ISMEN", "KLGYO", "GLYHO", "BASGZ", "AKGRT", "SUWEN", "KARTN",
    "BANVT", "BFREN", "CEMTS", "BURCE", "DGATE", "KAREL", "INDES", "ALCTL",
    "ISFIN", "PSGYO",
]

# BIST100 dışında bilinen, daha küçük/orta ölçekli örnek BIST hisseleri.
# Kapsamlı bir liste değil — kendi ilgi alanına göre genişlet.
_DIGER_BIST_RAW = [
    "BRISA", "VAKKO", "IZMDC", "TEKTU", "MERKO", "ARENA", "DESA", "ORGE",
    "PAGYO", "ATAGY", "METRO", "OZKGY", "USAK", "YUNSA", "KUTPO",
    "KONYA", "GOLTS",
]

TICKERS = {
    "bist100": [f"{code}.IS" for code in _BIST100_RAW],
    "diger_bist": [f"{code}.IS" for code in _DIGER_BIST_RAW],
    "emtia": ["USDTRY=X", "GC=F", "SI=F", "CL=F", "NG=F", "HG=F"],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD"],
    # nasdaq100 ve snp500 burada YOK — universe.py'den dinamik çekiliyor.
}

# Fırsat taraması (screener) ayarları — hepsi burada, kod içine gömülü değil,
# ki ileride birlikte ince ayar yapılabilsin.
SCREENER_SETTINGS = {
    # 52 haftalık (yaklaşık işlem günü) pencere
    "lookback_days_52w": 252,
    # Fiyat, 52 haftalık dibin en fazla bu yüzde üstündeyse "ucuz" sayılır
    "near_low_threshold_pct": 15.0,
    # "Yatay" kontrolü için son kaç işlem günü bakılacak (~6 ay)
    "sideways_window_days": 126,
    # Bu pencuredeki (max-min)/min yüzdesi bu eşiğin altındaysa "yatay" sayılır
    "sideways_threshold_pct": 20.0,
    # RSI periyodu ve "nötr/aşırı satım" kabul edilen bant
    "rsi_period": 14,
    "rsi_min": 20.0,
    "rsi_max": 55.0,
}


def all_symbols() -> list[str]:
    """Tüm statik gruplardaki sembolleri tek bir düz liste halinde döner.

    Nasdaq-100/S&P 500 dahil değildir — onlar için `universe.py` kullan.
    """
    symbols: list[str] = []
    for group_symbols in TICKERS.values():
        symbols.extend(group_symbols)
    return symbols
