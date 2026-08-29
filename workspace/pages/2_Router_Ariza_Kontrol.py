"""Router Arıza Kontrol sayfası — kurum-scriptleri/router-ariza-kontrol paketini kullanır."""

import importlib
import sys
from pathlib import Path

import streamlit as st

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent
PROJECT_DIR = ROOT_DIR / "kurum-scriptleri" / "router-ariza-kontrol"

sys.path.insert(0, str(WORKSPACE_DIR))
from project_loader import load_project_package  # noqa: E402

load_project_package("kurum_router_ariza_kontrol", PROJECT_DIR)
config = importlib.import_module("kurum_router_ariza_kontrol.config")
runner = importlib.import_module("kurum_router_ariza_kontrol.runner")

st.title("Router Arıza Kontrol")

st.caption(
    f"{len(config.ROUTERS)} hedef tanımlı. Gerçek router listesini "
    "`kurum-scriptleri/router-ariza-kontrol/config.py` içinden düzenleyebilirsin."
)

if st.button("Şimdi Kontrol Et", type="primary"):
    runner.setup_logging()
    with st.spinner("Kontroller çalışıyor..."):
        st.session_state["router_last_results"] = runner.run_all_checks()

results = st.session_state.get("router_last_results")

if results is None:
    st.info("Henüz kontrol çalıştırılmadı. Yukarıdaki butona bas.")
else:
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Kontrol", len(results))
    col2.metric("Sorunsuz", ok_count)
    col3.metric("Arızalı", fail_count)

    st.subheader("Sonuçlar")
    for r in results:
        icon = "🟢" if r["ok"] else "🔴"
        st.write(f"{icon} **{r['name']}** ({r['ip']}) — {r['check']}: {r['detail']}")

st.subheader("Log Dosyası (son satırlar)")
if config.LOG_PATH.exists():
    lines = Path(config.LOG_PATH).read_text(encoding="utf-8").splitlines()
    st.code("\n".join(lines[-30:]) or "(log boş)")
else:
    st.write("Henüz log dosyası oluşmadı.")
