"""Sol menü ağacının (klasörler + sayfalar) kalıcı deposu ve navigasyon inşası.

Menü yapılandırması `menu_config.json` içinde tutulur. Bu dosya SADECE
menüdeki görünümü/gruplamayı tanımlar — diskteki proje klasörlerini
etkilemez. Bir sayfayı bir klasöre "taşımak" veya "menüden kaldırmak" hiçbir
zaman dosya silmez/taşımaz; sadece bu JSON'daki alanları değiştirir.

Öğe (item) şekli:
    {"type": "folder", "id": str, "title": str, "parent_id": None}
    {"type": "page", "id": str, "title": str, "page_file": str,
     "parent_id": str | None, "hidden": bool}

`page_file`, workspace/Home.py'ye göreli bir yoldur (örn. "pages/1_Borsa_Takip.py").
"""

import json
import re
import uuid
from pathlib import Path

import streamlit as st

WORKSPACE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = WORKSPACE_DIR / "menu_config.json"

DEFAULT_ITEMS = [
    {
        "type": "page",
        "id": "borsa_takip",
        "title": "Borsa Takip",
        "page_file": "pages/1_Borsa_Takip.py",
        "parent_id": None,
        "hidden": False,
    },
    {
        "type": "page",
        "id": "router_ariza_kontrol",
        "title": "Router Arıza Kontrol",
        "page_file": "pages/2_Router_Ariza_Kontrol.py",
        "parent_id": None,
        "hidden": False,
    },
]


def load_items() -> list[dict]:
    """menu_config.json'u okur; yoksa varsayılan içerikle oluşturur."""
    if not CONFIG_PATH.exists():
        save_items(DEFAULT_ITEMS)
        return [dict(item) for item in DEFAULT_ITEMS]

    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)["items"]


def save_items(items: list[dict]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "oge"


def _unique_id(base: str, items: list[dict]) -> str:
    existing_ids = {item["id"] for item in items}
    if base not in existing_ids:
        return base
    return f"{base}-{uuid.uuid4().hex[:6]}"


def add_folder(items: list[dict], title: str) -> list[dict]:
    new_id = _unique_id(_slugify(title), items)
    items = items + [{"type": "folder", "id": new_id, "title": title, "parent_id": None}]
    return items


def add_page(items: list[dict], title: str, page_file: str) -> list[dict]:
    new_id = _unique_id(_slugify(title), items)
    items = items + [
        {
            "type": "page",
            "id": new_id,
            "title": title,
            "page_file": page_file,
            "parent_id": None,
            "hidden": False,
        }
    ]
    return items


def move_item(items: list[dict], item_id: str, direction: str) -> list[dict]:
    """item_id'yi, AYNI parent_id ve AYNI type'a sahip kardeşleri arasında
    bir yukarı/aşağı taşır (örn. bir sayfayı sadece diğer sayfalara göre,
    bir klasörü sadece diğer klasörlere göre kaydırır).
    """
    items = list(items)
    target = next((i for i in items if i["id"] == item_id), None)
    if target is None:
        return items

    sibling_indices = [
        idx
        for idx, item in enumerate(items)
        if item["type"] == target["type"] and item.get("parent_id") == target.get("parent_id")
    ]
    pos = sibling_indices.index(items.index(target))

    if direction == "up" and pos > 0:
        swap_with = sibling_indices[pos - 1]
    elif direction == "down" and pos < len(sibling_indices) - 1:
        swap_with = sibling_indices[pos + 1]
    else:
        return items

    this_idx = items.index(target)
    items[this_idx], items[swap_with] = items[swap_with], items[this_idx]
    return items


def assign_folder(items: list[dict], page_id: str, new_parent_id: str | None) -> list[dict]:
    """Sayfayı yeni bir klasöre (veya None ise üst seviyeye) taşır; yeni
    ebeveynin mevcut çocuklarının hemen ardına yerleştirir ki sıralama
    tutarlı kalsın.
    """
    items = list(items)
    idx = next((i for i, item in enumerate(items) if item["id"] == page_id), None)
    if idx is None:
        return items

    item = items.pop(idx)
    item["parent_id"] = new_parent_id

    last_sibling_idx = None
    for i, other in enumerate(items):
        if other["type"] == "page" and other.get("parent_id") == new_parent_id:
            last_sibling_idx = i

    insert_at = last_sibling_idx + 1 if last_sibling_idx is not None else len(items)
    items.insert(insert_at, item)
    return items


def hide_item(items: list[dict], page_id: str) -> list[dict]:
    return [
        {**item, "hidden": True} if item["id"] == page_id and item["type"] == "page" else item
        for item in items
    ]


def unhide_item(items: list[dict], page_id: str) -> list[dict]:
    return [
        {**item, "hidden": False} if item["id"] == page_id and item["type"] == "page" else item
        for item in items
    ]


def delete_folder(items: list[dict], folder_id: str) -> list[dict]:
    """Klasörü siler; içindeki sayfalar SİLİNMEZ, üst seviyeye (parent_id=None)
    geri taşınır.
    """
    result = []
    for item in items:
        if item["id"] == folder_id and item["type"] == "folder":
            continue
        if item["type"] == "page" and item.get("parent_id") == folder_id:
            item = {**item, "parent_id": None}
        result.append(item)
    return result


def build_navigation(items: list[dict]) -> dict[str, list[object]]:
    """items listesinden st.navigation'a verilecek {bölüm: [st.Page, ...]} sözlüğünü kurar.

    Diskte bulunamayan bir page_file varsa o öğe sessizce atlanır (uygulama
    çökmez).
    """

    def page_exists(page_file: str) -> bool:
        return (WORKSPACE_DIR / page_file).exists()

    nav: dict[str, list[object]] = {}

    genel_pages = [
        st.Page("pages/_ana_sayfa.py", title="Ana Sayfa", default=True),
    ]
    for item in items:
        if item["type"] == "page" and item.get("parent_id") is None and not item["hidden"]:
            if page_exists(item["page_file"]):
                genel_pages.append(st.Page(item["page_file"], title=item["title"]))
    nav["Genel"] = genel_pages

    folders = [item for item in items if item["type"] == "folder"]
    for folder in folders:
        children = [
            st.Page(item["page_file"], title=item["title"])
            for item in items
            if item["type"] == "page"
            and item.get("parent_id") == folder["id"]
            and not item["hidden"]
            and page_exists(item["page_file"])
        ]
        if children:
            nav[folder["title"]] = children

    nav["Ayarlar"] = [st.Page("pages/0_Menu_Yonetimi.py", title="Menü Yönetimi")]
    return nav
