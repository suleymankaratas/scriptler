# scriptler

Kişisel çalışma ortamı — birden fazla bağımsız projeyi tek repo altında tutar.

## Klasörler

- **[borsa-isleri/](borsa-isleri/)** — BIST/döviz-emtia/kripto/global piyasa
  takip ve analiz projesi (yfinance + SQLite + Streamlit dashboard).
- **[kurum-scriptleri/](kurum-scriptleri/)** — iş/kurumla ilgili script ve
  araçlar (henüz boş, ilerledikçe dolacak).

Her klasör kendi bağımsız projesi olarak düşünülür: kendi `requirements.txt`,
kendi `.venv`'i ve kendi README'si olur. Yeni bir proje eklerken aynı deseni
izle — kökte yeni bir klasör aç, içine kendi bağımsız yapısını kur.
