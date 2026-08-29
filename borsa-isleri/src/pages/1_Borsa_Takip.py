"""Streamlit sayfası: SQLite'taki fiyat verisini tablo + grafik olarak gösterir."""

import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle ki "src" paketi import edilebilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from src.config import TICKERS
from src.storage import all_symbols_in_db, get_connection, read_prices

st.title("Borsa / Piyasa Takip")

conn = get_connection()
available_symbols = all_symbols_in_db(conn)

if not available_symbols:
    st.warning(
        "Veritabanında henüz veri yok. Önce şunu çalıştır:\n\n"
        "`python scripts/run_fetch.py`"
    )
    st.stop()

# Sembolleri varlık sınıfına göre grupla (config.py'deki TICKERS sırasına göre)
symbol_to_group = {
    symbol: group for group, symbols in TICKERS.items() for symbol in symbols
}

with st.sidebar:
    st.header("Sembol seç")
    selected_symbol = st.selectbox(
        "Sembol",
        options=available_symbols,
        format_func=lambda s: f"{s} ({symbol_to_group.get(s, 'diğer')})",
    )

df = read_prices(conn, selected_symbol)
conn.close()

if df.empty:
    st.info("Bu sembol için veri bulunamadı.")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"{selected_symbol} — Kapanış Fiyatı")
    st.line_chart(df.set_index("date")["close"])

with col2:
    last_row = df.iloc[-1]
    st.metric("Son Kapanış", f"{last_row['close']:.2f}")
    if len(df) > 1:
        prev_close = df.iloc[-2]["close"]
        change_pct = (last_row["close"] - prev_close) / prev_close * 100
        st.metric("Günlük Değişim", f"{change_pct:+.2f}%")

st.subheader("Veri Tablosu")
st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
