"""Farklı proje klasörlerini isim çakışması olmadan içe aktarmak için yardımcı.

Her proje kendi klasöründe bağımsız çalışır ve kendi içinde istediği modül
adını kullanabilir (örn. borsa-isleri "src" paketini, router-ariza-kontrol
kendi kök klasörünü paket olarak kullanır). Menüden (workspace) birden
fazla projeyi AYNI Python sürecinde içe aktarmak istediğimizde, iki proje
aynı modül adını kullanırsa (örn. ikisi de "config.py" içeriyorsa) normal
`import` bunları birbirine karıştırabilir.

Bunu önlemek için her proje paketi, `load_project_package` ile BENZERSİZ bir
takma ad (alias) altında yüklenir; gerçek modül adları asla çakışmaz.

Yeni bir projeyi menüye eklerken:
1. Proje klasörünün kökünde bir `__init__.py` olduğundan emin ol (paket
   haline getir — içi boş olabilir).
2. `pages/` altına yeni bir sayfa dosyası ekle, bu dosyada:
   `pkg = load_project_package("benzersiz_takma_ad", PROJE_KLASORU)`
   ve `importlib.import_module("benzersiz_takma_ad.modul_adi")` kullan.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_project_package(alias: str, package_dir: Path) -> ModuleType:
    """`package_dir` klasörünü (bir `__init__.py` barındırmalı) `alias` adıyla yükler.

    Aynı alias ile daha önce yüklendiyse tekrar yüklemeden mevcut modülü döner
    (Streamlit her sayfa yenilemesinde script'i tekrar çalıştırdığı için önemli).
    """
    if alias in sys.modules:
        return sys.modules[alias]

    init_file = package_dir / "__init__.py"
    if not init_file.exists():
        raise ImportError(
            f"{package_dir} bir paket değil (__init__.py bulunamadı). "
            "Önce o klasöre boş bir __init__.py ekle."
        )

    spec = importlib.util.spec_from_file_location(
        alias, init_file, submodule_search_locations=[str(package_dir)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"{package_dir} yüklenemedi.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module
