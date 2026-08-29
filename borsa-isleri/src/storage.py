"""SQLite depolama yardımcıları: tablo oluşturma ve upsert."""

import sqlite3

import pandas as pd

try:
    # Bir paketin parçası olarak (örn. merkezi workspace menüsünden) yüklendiğinde
    # isim çakışmasını önlemek için göreli import kullanılır.
    from .config import DB_PATH
except ImportError:
    # Tek başına çalıştırıldığında (scripts/run_fetch.py, src/pages/... üzerinden)
    # paket bağlamı olmadığı için düz import'a düşer.
    from src.config import DB_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prices (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    PRIMARY KEY (symbol, date)
)
"""


def get_connection() -> sqlite3.Connection:
    """data/ klasörünü garanti eder ve bir SQLite bağlantısı döner."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    return conn


def upsert_prices(conn: sqlite3.Connection, symbol: str, df: pd.DataFrame) -> int:
    """Bir sembolün fiyat verisini prices tablosuna yazar (var olanı günceller).

    df, yfinance'ten gelen ve index'i tarih olan bir DataFrame olmalı;
    Open/High/Low/Close/Volume sütunlarını içerir.

    Döner: yazılan satır sayısı.
    """
    if df.empty:
        return 0

    rows = [
        (
            symbol,
            index.strftime("%Y-%m-%d"),
            float(row["Open"]),
            float(row["High"]),
            float(row["Low"]),
            float(row["Close"]),
            float(row["Volume"]),
        )
        for index, row in df.iterrows()
    ]

    conn.executemany(
        """
        INSERT INTO prices (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, date) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def read_prices(conn: sqlite3.Connection, symbol: str) -> pd.DataFrame:
    """Bir sembolün tüm fiyat geçmişini tarih sırasıyla döner."""
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM prices "
        "WHERE symbol = ? ORDER BY date",
        conn,
        params=(symbol,),
        parse_dates=["date"],
    )
    return df


def all_symbols_in_db(conn: sqlite3.Connection) -> list[str]:
    """Veritabanında verisi bulunan tüm sembolleri döner."""
    cursor = conn.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol")
    return [row[0] for row in cursor.fetchall()]
