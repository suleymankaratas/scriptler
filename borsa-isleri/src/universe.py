"""Nasdaq-100 ve S&P 500 sembol/şirket adı listelerini güvenilir kaynaklardan
çeker.

Önemli: bu listeler LLM ile elle transkript edilmiyor — gerçek `pandas`
fonksiyonları (`read_csv`/`read_html`) ile yapısal veriden okunuyor, bu da
"Q", "FDXF" gibi anlamsız/hatalı sembollerin karışma riskini ortadan
kaldırıyor.

Sonuçlar `data/universe_*.json` içine (sembol + şirket adı + zaman damgası)
önbelleğe alınır. Çekme başarısız olursa (kaynak site değişmiş, ağ sorunu
vb.) son iyi önbelleğe düşülür; hiçbir durumda uygulama çökmez.
"""

import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

try:
    from .config import UNIVERSE_CACHE_DIR
except ImportError:
    from config import UNIVERSE_CACHE_DIR

SNP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
NASDAQ100_URL = "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies"

SNP500_CACHE = UNIVERSE_CACHE_DIR / "universe_snp500.json"
NASDAQ100_CACHE = UNIVERSE_CACHE_DIR / "universe_nasdaq100.json"

# Bir günden eski önbellek varsa yeniden çekmeyi dener (yine de başarısız
# olursa eski önbelleği kullanmaya devam eder).
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60


def _to_yahoo_symbol(raw: str) -> str:
    """Wikipedia/GitHub'daki '.' ayraçlı sınıf hisselerini (örn. BRK.B) Yahoo
    Finance formatına ('-' ayraçlı, örn. BRK-B) çevirir.
    """
    return raw.strip().replace(".", "-")


def _load_cache(cache_path: Path) -> list[dict] | None:
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("items")
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(cache_path: Path, items: list[dict]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.time(), "items": items}, f, ensure_ascii=False, indent=2)


def _cache_is_fresh(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return (time.time() - data.get("fetched_at", 0)) < CACHE_MAX_AGE_SECONDS
    except (json.JSONDecodeError, OSError):
        return False


def _get_items(
    cache_path: Path, fetch_fn, force_refresh: bool, label: str
) -> list[dict]:
    """Ortak önbellek/çekme mantığı. `fetch_fn` () -> list[dict] (symbol/name)."""
    if not force_refresh and _cache_is_fresh(cache_path):
        cached = _load_cache(cache_path)
        if cached:
            return cached

    try:
        items = fetch_fn()
        if items:
            _save_cache(cache_path, items)
            return items
    except Exception as exc:  # noqa: BLE001
        print(f"[universe] {label} listesi çekilemedi: {exc}")

    cached = _load_cache(cache_path)
    if cached:
        print(f"[universe] {label} için son iyi önbellek kullanılıyor.")
        return cached
    return []


def _fetch_snp500_items() -> list[dict]:
    df = pd.read_csv(SNP500_URL)
    return [
        {"symbol": _to_yahoo_symbol(row["Symbol"]), "name": str(row["Security"]).strip()}
        for _, row in df.dropna(subset=["Symbol"]).iterrows()
    ]


def _fetch_nasdaq100_items() -> list[dict]:
    # Wikipedia, User-Agent'sız isteklere 403 ile yanıt verebiliyor;
    # tarayıcı benzeri bir başlıkla çekip HTML'i pandas'a öyle veriyoruz.
    response = requests.get(
        NASDAQ100_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; scriptler-borsa-takip/1.0)"},
        timeout=15,
    )
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))

    for table in tables:
        cols = [str(c).strip().lower() for c in table.columns]
        ticker_col = name_col = None
        for candidate in ("ticker", "symbol"):
            if candidate in cols:
                ticker_col = table.columns[cols.index(candidate)]
                break
        for candidate in ("company", "name"):
            if candidate in cols:
                name_col = table.columns[cols.index(candidate)]
                break

        if ticker_col is not None and len(table) >= 90:
            sub = table.dropna(subset=[ticker_col])
            return [
                {
                    "symbol": _to_yahoo_symbol(row[ticker_col]),
                    "name": str(row[name_col]).strip() if name_col is not None else "",
                }
                for _, row in sub.iterrows()
            ]
    return []


def get_snp500_items(force_refresh: bool = False) -> list[dict]:
    """S&P 500 bileşenlerini [{"symbol":..., "name":...}, ...] olarak döner."""
    return _get_items(SNP500_CACHE, _fetch_snp500_items, force_refresh, "S&P 500")


def get_nasdaq100_items(force_refresh: bool = False) -> list[dict]:
    """Nasdaq-100 bileşenlerini [{"symbol":..., "name":...}, ...] olarak döner."""
    return _get_items(NASDAQ100_CACHE, _fetch_nasdaq100_items, force_refresh, "Nasdaq-100")


def get_snp500_symbols(force_refresh: bool = False) -> list[str]:
    """S&P 500 bileşen sembollerini döner (Yahoo formatında)."""
    return [item["symbol"] for item in get_snp500_items(force_refresh)]


def get_nasdaq100_symbols(force_refresh: bool = False) -> list[str]:
    """Nasdaq-100 bileşen sembollerini döner (Yahoo formatında)."""
    return [item["symbol"] for item in get_nasdaq100_items(force_refresh)]


def get_snp500_name_map(force_refresh: bool = False) -> dict[str, str]:
    """S&P 500 sembol -> şirket adı eşlemesini döner."""
    return {item["symbol"]: item["name"] for item in get_snp500_items(force_refresh) if item["name"]}


def get_nasdaq100_name_map(force_refresh: bool = False) -> dict[str, str]:
    """Nasdaq-100 sembol -> şirket adı eşlemesini döner."""
    return {item["symbol"]: item["name"] for item in get_nasdaq100_items(force_refresh) if item["name"]}
