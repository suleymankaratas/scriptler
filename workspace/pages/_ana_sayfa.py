"""Çalışma Ortamı — Ana Sayfa (karşılama içeriği)."""

import streamlit as st

st.title("Çalışma Ortamı")
st.write("Sol menüden mevcut projeler arasında geçiş yapabilirsin.")

st.subheader("Mevcut Projeler")
st.markdown(
    "- **Borsa Takip** — BIST/döviz-emtia/kripto/global piyasa verisi ve grafik\n"
    "- **Router Arıza Kontrol** — kurum router'larının erişilebilirlik kontrolü"
)

st.info(
    "Yeni klasör açmak, projeleri klasörlere taşımak, sıralamak veya menüden "
    "kaldırmak için sol menüdeki **Menü Yönetimi** sayfasını kullan."
)
