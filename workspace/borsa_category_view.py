"""Kategori bazlı borsa sayfaları (BIST 100, Nasdaq-100, S&P 500 vb.) için
ortak render fonksiyonu — 6 kategori sayfasının hepsi bunu çağırır, kod
tekrarını önler.
"""

import pandas as pd
import streamlit as st

# Aralık seçenekleri: (etiket, yfinance period, yfinance interval, resample)
# "resample" None değilse, çekilen veri o pandas kuralına göre yeniden
# örneklenir (Yahoo'da native olmayan aralıklar için, örn. "2 Saatlik").
INTERVAL_OPTIONS = {
    "Günlük (5 yıl)": ("5y", "1d", None),
    "Haftalık (5 yıl)": ("5y", "1wk", None),
    "Aylık (5 yıl)": ("5y", "1mo", None),
    "Saatlik (~2 yıl, Yahoo sınırı)": ("2y", "1h", None),
    "2 Saatlik (~2 yıl, saatlikten hesaplanır)": ("2y", "1h", "2h"),
}


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    resampled = df.resample(rule).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    # Piyasa kapalıyken (gece, hafta sonu) oluşan boş zaman dilimlerinde
    # Volume=0 olur ama fiyat NaN kalır — how="all" bunları elemez, bu yüzden
    # Close'a göre eleriz (fetch.py'deki aynı desen, bkz. fetch_many_bulk).
    return resampled[resampled["Close"].notna()]


def _load_chart_data(symbol: str, interval_label: str, storage, fetch, conn) -> pd.DataFrame:
    """Seçilen aralığa göre veriyi döner (date/open/high/low/close/volume,
    küçük harf sütun adlarıyla — hem DB'den hem canlı çekimden aynı format).
    """
    period, interval, resample_rule = INTERVAL_OPTIONS[interval_label]

    if interval == "1d":
        # Günlük veri zaten toplu çekimle SQLite'ta duruyor — tekrar ağa
        # gitmeye gerek yok.
        return storage.read_prices(conn, symbol)

    # Diğer aralıklar (haftalık/aylık/saatlik/2 saatlik) sadece incelenen bu
    # tek sembol için, o an canlı çekilir — 700 sembole toplu uygulanmaz.
    raw = fetch.fetch_history(symbol, period=period, interval=interval)
    if raw.empty:
        return pd.DataFrame()

    if resample_rule:
        raw = _resample_ohlcv(raw, resample_rule)

    df = raw.reset_index()
    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    return df[["date", "open", "high", "low", "close", "volume"]]


def render_category_page(title: str, symbols: list[str], config, storage, screener, fetch) -> None:
    st.title(title)

    conn = storage.get_connection()
    db_symbols = set(storage.all_symbols_in_db(conn))
    available = [s for s in symbols if s in db_symbols]

    if not available:
        conn.close()
        st.warning(
            "Bu kategori için veritabanında henüz veri yok. Önce şunu çalıştır:\n\n"
            "`borsa-isleri\\.venv\\Scripts\\python.exe borsa-isleri\\scripts\\run_fetch.py`"
        )
        return

    st.subheader("Fırsat Taraması (bu kategori)")
    st.caption(
        "Uzun süredir ucuz (52 haftalık dibe yakın) VE yatayda kalmış "
        "sembolleri işaretler. Yatırım tavsiyesi değildir — inceleyip karar "
        "sana ait."
    )
    pairs = [(s, title) for s in available]
    result = screener.screen_symbols(pairs, storage, conn)
    if result.empty:
        st.info("Yeterli geçmiş veri olan sembol bulunamadı (en az ~1 aylık veri gerekir).")
    else:
        candidate_count = int(result["aday_mi"].sum())
        st.caption(f"{len(result)} sembol tarandı, {candidate_count} aday bulundu.")
        st.dataframe(result, use_container_width=True, hide_index=True)

    st.subheader("Sembol İncele")
    col_sym, col_interval = st.columns([2, 2])
    with col_sym:
        selected_symbol = st.selectbox("Sembol", options=available, key=f"select_{title}")
    with col_interval:
        interval_label = st.selectbox(
            "Aralık", options=list(INTERVAL_OPTIONS.keys()), key=f"interval_{title}"
        )

    with st.spinner("Veri hazırlanıyor..."):
        df = _load_chart_data(selected_symbol, interval_label, storage, fetch, conn)
    conn.close()

    if df.empty:
        st.info("Bu sembol/aralık için veri bulunamadı.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{selected_symbol} — Kapanış Fiyatı ({interval_label})")
        st.line_chart(df.set_index("date")["close"])
    with col2:
        last_row = df.iloc[-1]
        st.metric("Son Kapanış", f"{last_row['close']:.2f}")
        if len(df) > 1:
            prev_close = df.iloc[-2]["close"]
            change_pct = (last_row["close"] - prev_close) / prev_close * 100
            st.metric("Değişim (son bar)", f"{change_pct:+.2f}%")

    st.subheader("Veri Tablosu")
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
