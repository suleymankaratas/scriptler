"""Nasdaq-100 ve S&P 500 sembol listelerini güvenilir kaynaklardan çeker.

Önemli: bu listeler LLM ile elle transkript edilmiyor — gerçek `pandas`
fonksiyonları (`read_csv`/`read_html`) ile yapısal veriden okunuyor, bu da
"Q", "FDXF" gibi anlamsız/hatalı sembollerin karışma riskini ortadan
kaldırıyor.

Sonuçlar `data/universe_*.json` içine zaman damgasıyla önbelleğe alınır.
Çekme başarısız olursa (kaynak site değişmiş, ağ sorunu vb.) son iyi
önbelleğe düşülür; hiçbir durumda uygulama çökmez.
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


def _load_cache(cache_path: Path) -> list[str] | None:
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("symbols")
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(cache_path: Path, symbols: list[str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.time(), "symbols": symbols}, f, ensure_ascii=False, indent=2)


def _cache_is_fresh(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return (time.time() - data.get("fetched_at", 0)) < CACHE_MAX_AGE_SECONDS
    except (json.JSONDecodeError, OSError):
        return False


def get_snp500_symbols(force_refresh: bool = False) -> list[str]:
    """S&P 500 bileşen sembollerini döner (Yahoo formatında)."""
    if not force_refresh and _cache_is_fresh(SNP500_CACHE):
        cached = _load_cache(SNP500_CACHE)
        if cached:
            return cached

    try:
        df = pd.read_csv(SNP500_URL)
        symbols = [_to_yahoo_symbol(s) for s in df["Symbol"].dropna().tolist()]
        if symbols:
            _save_cache(SNP500_CACHE, symbols)
            return symbols
    except Exception as exc:  # noqa: BLE001
        print(f"[universe] S&P 500 listesi çekilemedi: {exc}")

    cached = _load_cache(SNP500_CACHE)
    if cached:
        print("[universe] S&P 500 için son iyi önbellek kullanılıyor.")
        return cached
    return []


def get_nasdaq100_symbols(force_refresh: bool = False) -> list[str]:
    """Nasdaq-100 bileşen sembollerini döner (Yahoo formatında)."""
    if not force_refresh and _cache_is_fresh(NASDAQ100_CACHE):
        cached = _load_cache(NASDAQ100_CACHE)
        if cached:
            return cached

    try:
        # Wikipedia, User-Agent'sız isteklere 403 ile yanıt verebiliyor;
        # tarayıcı benzeri bir başlıkla çekip HTML'i pandas'a öyle veriyoruz.
        response = requests.get(
            NASDAQ100_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; scriptler-borsa-takip/1.0)"},
            timeout=15,
        )
        response.raise_for_status()
        tables = pd.read_html(io.StringIO(response.text))
        symbols: list[str] = []
        for table in tables:
            cols = [str(c).strip().lower() for c in table.columns]
            ticker_col = None
            for candidate in ("ticker", "symbol"):
                if candidate in cols:
                    ticker_col = table.columns[cols.index(candidate)]
                    break
            if ticker_col is not None and len(table) >= 90:
                symbols = [_to_yahoo_symbol(s) for s in table[ticker_col].dropna().tolist()]
                break

        if symbols:
            _save_cache(NASDAQ100_CACHE, symbols)
            return symbols
    except Exception as exc:  # noqa: BLE001
        print(f"[universe] Nasdaq-100 listesi çekilemedi: {exc}")

    cached = _load_cache(NASDAQ100_CACHE)
    if cached:
        print("[universe] Nasdaq-100 için son iyi önbellek kullanılıyor.")
        return cached
    return []
