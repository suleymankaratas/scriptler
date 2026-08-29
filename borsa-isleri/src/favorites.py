"""Favori (izleme listesi) sembollerin kalıcı deposu.

Basit bir JSON dosyasında symbol -> kategori eşlemesi olarak tutulur
(`data/favorites.json`, git'e dahil değil — kişisel/yerel kullanım verisi).
"""

import json
from pathlib import Path

try:
    from .config import BASE_DIR
except ImportError:
    from config import BASE_DIR

FAVORITES_PATH = BASE_DIR / "data" / "favorites.json"


def load_favorites() -> dict[str, str]:
    """symbol -> kategori eşlemesi olarak tüm favorileri döner."""
    if not FAVORITES_PATH.exists():
        return {}
    try:
        with open(FAVORITES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_favorites(favorites: dict[str, str]) -> None:
    FAVORITES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FAVORITES_PATH, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def set_favorite(symbol: str, kategori: str, is_favorite: bool) -> None:
    """Bir sembolü favorilere ekler (is_favorite=True) veya kaldırır (False)."""
    favorites = load_favorites()
    if is_favorite:
        favorites[symbol] = kategori
    else:
        favorites.pop(symbol, None)
    save_favorites(favorites)


def is_favorite(symbol: str) -> bool:
    return symbol in load_favorites()
