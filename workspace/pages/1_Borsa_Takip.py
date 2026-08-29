"""Borsa Takip sayfası — borsa-isleri/src paketini menü üzerinden kullanır."""

import importlib
import sys
from pathlib import Path

import streamlit as st

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent

sys.path.insert(0, str(WORKSPACE_DIR))
from project_loader import load_project_package  # noqa: E402

load_project_package("borsa_isleri_src", ROOT_DIR / "borsa-isleri" / "src")
config = importlib.import_module("borsa_isleri_src.config")
storage = importlib.import_module("borsa_isleri_src.storage")

st.title("Borsa / Piyasa Takip")

conn = storage.get_connection()
available_symbols = storage.all_symbols_in_db(conn)

if not available_symbols:
    st.warning(
        "Veritabanında henüz veri yok. Önce şunu çalıştır:\n\n"
        "`borsa-isleri/.venv/Scripts/python.exe borsa-isleri/scripts/run_fetch.py`"
    )
    st.stop()

symbol_to_group = {
    symbol: group for group, symbols in config.TICKERS.items() for symbol in symbols
}

with st.sidebar:
    st.header("Sembol seç")
    selected_symbol = st.selectbox(
        "Sembol",
        options=available_symbols,
        format_func=lambda s: f"{s} ({symbol_to_group.get(s, 'diğer')})",
    )

df = storage.read_prices(conn, selected_symbol)
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
