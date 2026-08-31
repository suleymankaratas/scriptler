"""Çalışma ortamı — ana sayfa.

Bu, çok sayfalı bir Streamlit uygulamasının giriş noktasıdır. Sol menüden
mevcut sayfalar arasında geçiş yapılır. Yeni bir iş/araç eklemek için
`src/pages/` klasörüne yeni bir dosya eklemek yeterli (Streamlit otomatik
olarak menüye ekler).

Çalıştırmak için proje kökünden:
    streamlit run src/Home.py
"""

import streamlit as st

st.set_page_config(page_title="Çalışma Ortamı", layout="wide")

st.title("Çalışma Ortamı")
st.write(
    "Sol menüden mevcut sayfalara geçebilirsin. Zamanla buraya yeni işlerin "
    "için yeni sayfalar eklenecek."
)

st.subheader("Mevcut Sayfalar")
st.markdown(
    "- **Borsa Takip** — BIST/döviz-emtia/kripto/global piyasa verisi ve grafik"
)
