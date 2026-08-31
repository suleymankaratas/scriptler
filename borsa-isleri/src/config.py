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

# BIST 100 (yaklaşık/makul liste — bkz. yukarıdaki not): (kod, şirket adı).
# ".IS" son eki aşağıda otomatik ekleniyor.
_BIST100_RAW = [
    ("THYAO", "Türk Hava Yolları"), ("GARAN", "Garanti BBVA"), ("AKBNK", "Akbank"),
    ("ISCTR", "Türkiye İş Bankası (C)"), ("YKBNK", "Yapı Kredi Bankası"),
    ("VAKBN", "VakıfBank"), ("HALKB", "Halkbank"), ("TSKB", "TSKB"),
    ("SAHOL", "Sabancı Holding"), ("KCHOL", "Koç Holding"),
    ("SISE", "Şişecam"), ("EREGL", "Ereğli Demir Çelik"), ("TUPRS", "Tüpraş"),
    ("PETKM", "Petkim"), ("ASELS", "Aselsan"), ("TOASO", "Tofaş"),
    ("FROTO", "Ford Otosan"), ("OTKAR", "Otokar"), ("KARSN", "Karsan"),
    ("TTKOM", "Türk Telekom"), ("TCELL", "Turkcell"), ("ARCLK", "Arçelik"),
    ("VESTL", "Vestel"), ("BIMAS", "BİM"), ("MGROS", "Migros"),
    ("SOKM", "Şok Marketler"), ("ULKER", "Ülker"), ("CCOLA", "Coca-Cola İçecek"),
    ("AEFES", "Anadolu Efes"), ("TATGD", "Tat Gıda"), ("PGSUS", "Pegasus"),
    ("TAVHL", "TAV Havalimanları"), ("DOAS", "Doğuş Otomotiv"),
    ("CIMSA", "Çimsa"), ("AKCNS", "Akçansa"), ("ENKAI", "Enka İnşaat"),
    ("TKFEN", "Tekfen Holding"), ("GUBRF", "Gübre Fabrikaları"),
    ("AGHOL", "Anadolu Grubu Holding"), ("ALARK", "Alarko Holding"),
    ("ZOREN", "Zorlu Enerji"), ("AKSEN", "Aksa Enerji"), ("AKSA", "Aksa Akrilik"),
    ("KONTR", "Kontrolmatik"), ("ASTOR", "Astor Enerji"), ("SASA", "Sasa Polyester"),
    ("BRSAN", "Borusan Boru"), ("BRYAT", "Borusan Yatırım"), ("EGEEN", "Ege Endüstri"),
    ("HEKTS", "Hektaş"), ("TRGYO", "Torunlar GYO"), ("EKGYO", "Emlak Konut GYO"),
    ("ISGYO", "İş GYO"), ("KRDMD", "Kardemir"), ("ISDMR", "İskenderun Demir Çelik"),
    ("DOHOL", "Doğan Holding"), ("LOGO", "Logo Yazılım"), ("NETAS", "Netaş"),
    ("MAVI", "Mavi Giyim"), ("MPARK", "MLP Sağlık"), ("ECILC", "Eczacıbaşı İlaç"),
    ("DEVA", "Deva Holding"), ("SELEC", "Selçuk Ecza"), ("TMSN", "Tümosan"),
    ("YATAS", "Yataş"), ("ANHYT", "Anadolu Hayat Emeklilik"), ("ANSGR", "Anadolu Sigorta"),
    ("AGESA", "Agesa"), ("TURSG", "Türkiye Sigorta"), ("GESAN", "Girişim Elektrik"),
    ("ALFAS", "Alfa Solar"), ("SMRTG", "Smart Güneş Enerjisi"), ("ODAS", "Odaş Elektrik"),
    ("AYDEM", "Aydem Enerji"), ("NTHOL", "Net Holding"), ("CLEBI", "Çelebi Hava Servisi"),
    ("VESBE", "Vestel Beyaz Eşya"), ("PENTA", "Penta Teknoloji"),
    ("SDTTR", "SDT Uzay ve Savunma"), ("ISMEN", "İş Yatırım"), ("KLGYO", "Kiler GYO"),
    ("GLYHO", "Global Yatırım Holding"), ("BASGZ", "Başkent Doğalgaz"),
    ("AKGRT", "Aksigorta"), ("SUWEN", "Suwen Tekstil"), ("KARTN", "Kartonsan"),
    ("BANVT", "Banvit"), ("BFREN", "Bosch Fren Sistemleri"), ("CEMTS", "Çemtaş"),
    ("BURCE", "Burçelik"), ("DGATE", "Datagate"), ("KAREL", "Karel Elektronik"),
    ("INDES", "İndeks Bilgisayar"), ("ALCTL", "Alcatel Lucent Teletaş"),
    ("ISFIN", "İş Finansal Kiralama"), ("PSGYO", "Pasifik GYO"),
]

# BIST100 dışında bilinen, daha küçük/orta ölçekli örnek BIST hisseleri:
# (kod, şirket adı). Kapsamlı bir liste değil — kendi ilgi alanına göre genişlet.
_DIGER_BIST_RAW = [
    ("BRISA", "Brisa"), ("VAKKO", "Vakko"), ("IZMDC", "İzmir Demir Çelik"),
    ("TEKTU", "Tek-Art Turizm"), ("MERKO", "Merko Gıda"), ("ARENA", "Arena Bilgisayar"),
    ("DESA", "Desa Deri"), ("ORGE", "Orge Enerji"), ("PAGYO", "Panora GYO"),
    ("ATAGY", "Atakule GYO"), ("METRO", "Metro Ticaret"), ("OZKGY", "Özak GYO"),
    ("USAK", "Uşak Seramik"), ("YUNSA", "Yünsa"), ("KUTPO", "Kütahya Porselen"),
    ("KONYA", "Konya Çimento"), ("GOLTS", "Göltaş Çimento"),
]

# Emtia/döviz ve kripto: sembol -> görünen ad.
_EMTIA_RAW = [
    ("USDTRY=X", "Dolar/TL"), ("GC=F", "Altın (Futures)"), ("SI=F", "Gümüş (Futures)"),
    ("CL=F", "Ham Petrol (WTI)"), ("NG=F", "Doğalgaz"), ("HG=F", "Bakır"),
]
_CRYPTO_RAW = [
    ("BTC-USD", "Bitcoin"), ("ETH-USD", "Ethereum"), ("SOL-USD", "Solana"),
    ("XRP-USD", "Ripple (XRP)"), ("BNB-USD", "BNB (Binance Coin)"),
]

TICKERS = {
    "bist100": [f"{code}.IS" for code, _ in _BIST100_RAW],
    "diger_bist": [f"{code}.IS" for code, _ in _DIGER_BIST_RAW],
    "emtia": [symbol for symbol, _ in _EMTIA_RAW],
    "crypto": [symbol for symbol, _ in _CRYPTO_RAW],
    # nasdaq100 ve snp500 burada YOK — universe.py'den dinamik çekiliyor.
}

# Sembol -> şirket/varlık adı eşlemesi (statik gruplar için). Nasdaq-100/S&P 500
# isimleri `universe.py` tarafından kaynağından otomatik çekilir.
SYMBOL_NAMES: dict[str, str] = {}
SYMBOL_NAMES.update({f"{code}.IS": name for code, name in _BIST100_RAW})
SYMBOL_NAMES.update({f"{code}.IS": name for code, name in _DIGER_BIST_RAW})
SYMBOL_NAMES.update(dict(_EMTIA_RAW))
SYMBOL_NAMES.update(dict(_CRYPTO_RAW))

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

    # --- Grafik Fırsatı (dolar bazlı, uzun vadeli, temelden bağımsız) ---
    # BIST hisseleri USDTRY=X ile dolar bazına çevrilir; Nasdaq/S&P/kripto/
    # emtia zaten dolar bazlı olduğu için doğrudan kullanılır.
    # Karşılaştırılacak geçmiş noktalar (yaklaşık işlem günü sayısı olarak)
    "chart_opportunity_lookback_days": {"2 yıl": 504, "5 yıl": 1260},
    # Güncel fiyat, o geçmiş noktaya en fazla bu yüzde yakınsa "o seviyeye
    # geri gelmiş" sayılır
    "flat_vs_past_threshold_pct": 15.0,
    # Tüm geçmişteki zirveden dolar bazlı en az bu kadar (negatif) düşmüş
    # olmalı ki "ciddi düşüş yaşamış" sayılsın
    "major_decline_threshold_pct": -35.0,
}


def all_symbols() -> list[str]:
    """Tüm statik gruplardaki sembolleri tek bir düz liste halinde döner.

    Nasdaq-100/S&P 500 dahil değildir — onlar için `universe.py` kullan.
    """
    symbols: list[str] = []
    for group_symbols in TICKERS.values():
        symbols.extend(group_symbols)
    return symbols
