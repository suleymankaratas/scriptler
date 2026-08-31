# Borsa/Piyasa Takip ve Analiz Projesi

BIST hisseleri, döviz/emtia, kripto ve global hisseleri (Nasdaq-100, S&P 500)
tek yerden takip edip analiz etmek, ayrıca uzun süredir ucuz/yatay kalmış
("fırsat") hisseleri taramak için kişisel bir proje.

> Bu proje artık ana `workspace/` menüsünden ("borsa" klasöründeki sayfalar)
> çalışıyor — bkz. kök [README.md](../README.md). Aşağıdaki adımlar bu projeyi
> tek başına (bağımsız) çalıştırmak içindir.

Veri kaynağı olarak [yfinance](https://github.com/ranaroussi/yfinance)
kullanılıyor (ücretsiz, API key gerektirmez). investing.com ve TradingView'ın
resmi/bireysel kullanıcılar için veri-çekme API'si olmadığından ve
scraping'in ToS riski taşıdığından (investing.com 2022'de `investpy`
kütüphanesini hukuki yolla kapattırdı) bu proje için tercih edilmedi.

Nasdaq-100 ve S&P 500 sembol listeleri `src/universe.py` tarafından güvenilir,
yapısal kaynaklardan (GitHub açık veri seti, Wikipedia — `pandas` ile,
LLM transkripsiyonu olmadan) otomatik çekilip önbelleğe alınır. BIST 100 için
böyle temiz bir kaynak bulunamadığından `src/config.py` içinde elle
düzenlenebilir, makul ama kesin güncelliği garanti edilmeyen bir liste
kullanılıyor.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Kullanım

1. Takip etmek istediğin statik sembolleri (BIST100, diğer BIST, emtia,
   kripto) [src/config.py](src/config.py) içindeki `TICKERS` sözlüğünde
   düzenle. Nasdaq-100/S&P 500 otomatik çekilir, elle düzenlemene gerek yok.
2. Veriyi çek ve SQLite'a kaydet (ilk çalıştırma ~700 sembol olduğu için
   birkaç dakika sürebilir):
   ```powershell
   python scripts/run_fetch.py
   ```
3. Dashboard'u ana `workspace/` menüsünden aç (bkz. kök README) — "borsa"
   klasöründe kategori sayfaları ve "Fırsat Taraması" bulunur.

## Proje Yapısı

- `src/config.py` — takip listeleri, `SCREENER_SETTINGS` (tarama eşikleri)
- `src/universe.py` — Nasdaq-100/S&P 500 sembollerini güvenilir kaynaklardan
  çekip önbelleğe alır (`data/universe_*.json`)
- `src/fetch.py` — yfinance ile veri çekme (`fetch_many_bulk`: yüzlerce
  sembolü toplu/batch olarak verimli çeker)
- `src/storage.py` — SQLite okuma/yazma
- `src/screener.py` — fiyat bazlı fırsat tarama (52 haftalık dip/zirve, yatay
  bant, RSI) — **yatırım tavsiyesi değildir**, sadece dikkat çekici adayları
  filtreler
- `scripts/run_fetch.py` — manuel veri çekme script'i (statik semboller +
  Nasdaq-100/S&P 500 evreni)
- `data/market_data.db` — SQLite veritabanı (git'e dahil değil)
- `src/Home.py`, `src/pages/` — bu projenin bağımsız (standalone) çalıştırma
  modu; asıl kullanım artık ana `workspace/` üzerinden

## Yol Haritası

- [x] Kategori bazlı sayfalar (BIST100, diğer BIST, emtia, Nasdaq-100, S&P 500, kripto)
- [x] Fiyat bazlı fırsat tarama (52 hafta dip/zirve + yatay bant + RSI)
- [ ] Canlı/gün-içi veri (örn. kripto için Binance API)
- [ ] Telegram bot ile fiyat/indikatör alarmları
- [ ] Geçmiş veriyle backtest
- [ ] Domain + VPS'e taşıma, TradingView webhook alarmları
