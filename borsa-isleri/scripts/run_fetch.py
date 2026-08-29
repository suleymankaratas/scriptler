"""Manuel çalıştırma: config.py'deki tüm sembolleri çekip SQLite'a yazar.

Kullanım:
    python scripts/run_fetch.py
"""

import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle ki "src" paketi import edilebilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TICKERS, all_symbols
from src.fetch import fetch_many
from src.storage import get_connection, upsert_prices


def main() -> None:
    symbols = all_symbols()
    print(f"{len(symbols)} sembol çekilecek: {', '.join(symbols)}")

    data = fetch_many(symbols)

    conn = get_connection()
    total_rows = 0
    for symbol, df in data.items():
        written = upsert_prices(conn, symbol, df)
        total_rows += written
        status = f"{written} satır yazıldı" if written else "veri yok / hata"
        print(f"  - {symbol}: {status}")
    conn.close()

    print(f"Bitti. Toplam {total_rows} satır yazıldı/güncellendi.")


if __name__ == "__main__":
    main()
