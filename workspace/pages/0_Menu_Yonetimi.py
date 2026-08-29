"""Menü Yönetimi — sol menüdeki klasörleri, sırayı ve görünürlüğü düzenler.

Önemli: buradaki hiçbir işlem diskteki dosyaları taşımaz veya silmez. Sadece
`menu_config.json` içindeki gruplama/sıra/görünürlük bilgisini değiştirir.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from menu_store import (  # noqa: E402
    add_folder,
    add_page,
    assign_folder,
    delete_folder,
    hide_item,
    load_items,
    move_item,
    save_items,
    unhide_item,
)

st.title("Menü Yönetimi")
st.caption(
    "Buradaki değişiklikler sadece sol menünün görünümünü etkiler — diskteki "
    "proje dosyaları hiçbir zaman taşınmaz veya silinmez."
)

items = load_items()

# --- Yeni klasör oluştur ---
st.subheader("Yeni Klasör Oluştur")
with st.form("new_folder_form", clear_on_submit=True):
    folder_name = st.text_input("Klasör adı", placeholder="örn. Kurum")
    if st.form_submit_button("Klasör Oluştur") and folder_name.strip():
        items = add_folder(items, folder_name.strip())
        save_items(items)
        st.rerun()

# --- Yeni sayfa kaydet (ör. yeni bir proje eklendiğinde) ---
st.subheader("Yeni Sayfa Kaydet")
st.caption(
    "Yeni bir projeye workspace/pages/ altında bir sayfa ekledikten sonra, "
    "menüde görünmesi için burada kaydet."
)
with st.form("new_page_form", clear_on_submit=True):
    page_title = st.text_input("Başlık", placeholder="örn. Yeni Araç")
    page_file = st.text_input(
        "Sayfa dosyası yolu (workspace/'e göreli)",
        placeholder="örn. pages/3_Yeni_Arac.py",
    )
    if st.form_submit_button("Sayfayı Kaydet") and page_title.strip() and page_file.strip():
        items = add_page(items, page_title.strip(), page_file.strip())
        save_items(items)
        st.rerun()

# --- Sayfaları yönet: klasöre taşı, sırala, kaldır ---
st.subheader("Sayfalar")

folders = [i for i in items if i["type"] == "folder"]
folder_titles = ["(Genel — klasörsüz)"] + [f["title"] for f in folders]
folder_id_by_title = {"(Genel — klasörsüz)": None, **{f["title"]: f["id"] for f in folders}}
folder_title_by_id = {f["id"]: f["title"] for f in folders}

visible_pages = [i for i in items if i["type"] == "page" and not i["hidden"]]

if not visible_pages:
    st.write("Menüde görünür sayfa yok.")

for page in visible_pages:
    col_title, col_folder, col_up, col_down, col_hide = st.columns([3, 3, 1, 1, 2])

    col_title.write(f"**{page['title']}**")

    current_title = folder_title_by_id.get(page.get("parent_id"), "(Genel — klasörsüz)")
    new_title = col_folder.selectbox(
        "Klasör",
        options=folder_titles,
        index=folder_titles.index(current_title),
        key=f"folder_select_{page['id']}",
        label_visibility="collapsed",
    )
    new_parent_id = folder_id_by_title[new_title]
    if new_parent_id != page.get("parent_id"):
        items = assign_folder(items, page["id"], new_parent_id)
        save_items(items)
        st.rerun()

    if col_up.button("⬆️", key=f"up_{page['id']}"):
        items = move_item(items, page["id"], "up")
        save_items(items)
        st.rerun()

    if col_down.button("⬇️", key=f"down_{page['id']}"):
        items = move_item(items, page["id"], "down")
        save_items(items)
        st.rerun()

    if col_hide.button("Menüden Kaldır", key=f"hide_{page['id']}"):
        items = hide_item(items, page["id"])
        save_items(items)
        st.rerun()

# --- Menüden kaldırılanlar: geri getirme ---
hidden_pages = [i for i in items if i["type"] == "page" and i["hidden"]]
if hidden_pages:
    st.subheader("Menüden Kaldırılanlar")
    st.caption("Dosyalar silinmedi — istediğin zaman geri getirebilirsin.")
    for page in hidden_pages:
        col_title, col_restore = st.columns([4, 1])
        col_title.write(page["title"])
        if col_restore.button("Geri Getir", key=f"restore_{page['id']}"):
            items = unhide_item(items, page["id"])
            save_items(items)
            st.rerun()

# --- Klasör sil ---
if folders:
    st.subheader("Klasör Sil")
    st.caption("İçindeki sayfalar silinmez, Genel (klasörsüz) alana geri döner.")
    for folder in folders:
        col_title, col_delete = st.columns([4, 1])
        col_title.write(folder["title"])
        if col_delete.button("Klasörü Sil", key=f"delfolder_{folder['id']}"):
            items = delete_folder(items, folder["id"])
            save_items(items)
            st.rerun()
