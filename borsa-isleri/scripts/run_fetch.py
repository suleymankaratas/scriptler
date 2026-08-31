"""Manuel çalıştırma: config.py'deki tüm statik sembolleri + Nasdaq-100/S&P 500
evrenini (universe.py) çekip SQLite'a yazar.

Yüzlerce sembol olduğu için toplu (batch) çekme kullanılır — ilk çalıştırma
birkaç dakika sürebilir.

Kullanım:
    python scripts/run_fetch.py
"""

import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle ki "src" paketi import edilebilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TICKERS, all_symbols
from src.fetch import fetch_many_bulk
from src.storage import get_connection, upsert_prices, write_last_fetch_info
from src.universe import get_nasdaq100_symbols, get_snp500_symbols


def main() -> None:
    static_symbols = all_symbols()
    nasdaq100 = get_nasdaq100_symbols()
    snp500 = get_snp500_symbols()

    print(f"Nasdaq-100: {len(nasdaq100)} sembol, S&P 500: {len(snp500)} sembol.")

    # Kategori bilgisini de tutalım ki ekranda/screener'da işimize yarasın.
    symbol_category = {s: cat for cat, syms in TICKERS.items() for s in syms}
    symbol_category.update({s: "nasdaq100" for s in nasdaq100})
    symbol_category.update({s: "snp500" for s in snp500})

    all_symbols_list = list(dict.fromkeys(static_symbols + nasdaq100 + snp500))
    print(f"Toplam {len(all_symbols_list)} benzersiz sembol çekilecek.")

    def on_progress(done: int, total: int) -> None:
        print(f"  ilerleme: {done}/{total}")

    data = fetch_many_bulk(all_symbols_list, period="5y", on_progress=on_progress)

    conn = get_connection()
    total_rows = 0
    failed: list[str] = []
    for symbol, df in data.items():
        written = upsert_prices(conn, symbol, df)
        total_rows += written
        if not written:
            failed.append(symbol)
    conn.close()

    write_last_fetch_info(symbol_count=len(all_symbols_list) - len(failed), row_count=total_rows)

    print(f"\nBitti. Toplam {total_rows} satır yazıldı/güncellendi.")
    if failed:
        print(f"Veri alınamayan {len(failed)} sembol: {', '.join(failed)}")


if __name__ == "__main__":
    main()
