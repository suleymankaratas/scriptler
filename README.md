# Borsa/Piyasa Takip ve Analiz Projesi

BIST hisseleri, döviz/emtia, kripto ve global hisseleri tek yerden takip edip
analiz etmek için kişisel bir proje. Local MVP: veri çekme + SQLite + Streamlit
dashboard.

Veri kaynağı olarak [yfinance](https://github.com/ranaroussi/yfinance)
kullanılıyor (ücretsiz, API key gerektirmez). investing.com ve TradingView'ın
resmi/bireysel kullanıcılar için veri-çekme API'si olmadığından ve
scraping'in ToS riski taşıdığından (investing.com 2022'de `investpy`
kütüphanesini hukuki yolla kapattırdı) bu proje için tercih edilmedi.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Kullanım

1. Takip etmek istediğin sembolleri [src/config.py](src/config.py) içindeki
   `TICKERS` sözlüğünde düzenle.
2. Veriyi çek ve SQLite'a kaydet:
   ```powershell
   python scripts/run_fetch.py
   ```
3. Dashboard'u aç:
   ```powershell
   streamlit run src/dashboard.py
   ```

## Proje Yapısı

- `src/config.py` — takip listesi ve ayarlar
- `src/fetch.py` — yfinance ile veri çekme
- `src/storage.py` — SQLite okuma/yazma
- `src/dashboard.py` — Streamlit arayüzü
- `scripts/run_fetch.py` — manuel veri çekme script'i
- `data/market_data.db` — SQLite veritabanı (git'e dahil değil)

## Yol Haritası

- [ ] Teknik indikatörler (RSI, MACD, SMA/EMA) — `pandas-ta`
- [ ] Telegram bot ile fiyat/indikatör alarmları
- [ ] Geçmiş veriyle backtest
- [ ] Domain + VPS'e taşıma, TradingView webhook alarmları
