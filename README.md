# scriptler

Kişisel çalışma ortamı — birden fazla bağımsız projeyi tek repo altında tutar.

## Çalıştırma (tek menü)

Tüm projelere tek bir arayüzden, sol menüden geçerek erişilir:

```powershell
workspace\.venv\Scripts\python.exe -m streamlit run workspace\Home.py
```

Bu, **workspace/** klasöründeki merkezi Streamlit uygulamasıdır — her proje
kendi sayfası olarak menüde görünür.

## Klasörler

- **[workspace/](workspace/)** — merkezi menü/arayüz. Tüm projelerin
  sayfalarını (`workspace/pages/`) barındırır. Yeni bir proje eklerken
  buraya da bir sayfa eklenir (bkz. `workspace/project_loader.py`).
- **[borsa-isleri/](borsa-isleri/)** — BIST/döviz-emtia/kripto/global piyasa
  takip ve analiz projesi (yfinance + SQLite + Streamlit). Menüden
  "Borsa Takip" sayfası olarak erişilir; ayrıca kendi başına da çalıştırılabilir.
- **[kurum-scriptleri/](kurum-scriptleri/)** — iş/kurumla ilgili script ve
  araçlar. İlk proje: `router-ariza-kontrol/` (menüde "Router Arıza Kontrol").

## Yeni Proje Eklemek

1. Kökte yeni bir klasör aç (ör. `kurum-scriptleri/yeni-arac/`), kendi
   bağımsız yapısını kur (kendi `requirements.txt`, `.venv`'i, README'si).
2. Klasör kökünde boş bir `__init__.py` oluştur (paket haline getirir —
   menünün isim çakışması olmadan içe aktarabilmesi için gerekli).
3. `workspace/pages/` altına yeni bir sayfa dosyası ekle; `project_loader.py`
   içindeki talimatları ve mevcut sayfaları (`1_Borsa_Takip.py`,
   `2_Router_Ariza_Kontrol.py`) örnek al.
4. Projenin bağımlılıkları `workspace/requirements.txt`'te yoksa oraya da ekle
   (workspace kendi venv'inde tüm sayfaları aynı süreçte çalıştırır).
5. Menüde görünmesi için sol menüdeki **Menü Yönetimi** sayfasından "Yeni
   Sayfa Kaydet" formuyla (başlık + sayfa dosyası yolu) kaydet — istersen
   yeni bir klasöre de ata. Menünün klasör/sıra yapısı `workspace/menu_config.json`
   içinde tutulur; hiçbir menü işlemi (taşıma, kaldırma) diskteki proje
   dosyalarını etkilemez.

Her proje klasörü ayrıca kendi başına da (kendi `.venv`'i ile) çalıştırılabilir
kalır — menü sadece bir üst katman arayüzdür, projelerin bağımsızlığını
bozmaz.
