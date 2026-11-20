"""Pruebas de que STORAGE_DIR nunca queda fuera del Volume en Railway.

    py -3 tests/test_storage_dir.py
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402

_VOLUME_VAR = "RAILWAY_VOLUME_MOUNT_PATH"


def _settings(storage_dir: str, volume: str | None) -> Settings:
    """Settings con un STORAGE_DIR dado y el Volume simulado (o sin Volume)."""
    original = os.environ.get(_VOLUME_VAR)
    try:
        if volume is None:
            os.environ.pop(_VOLUME_VAR, None)
        else:
            os.environ[_VOLUME_VAR] = volume
        return Settings(_env_file=None, storage_dir=storage_dir)
    finally:
        if original is None:
            os.environ.pop(_VOLUME_VAR, None)
        else:
            os.environ[_VOLUME_VAR] = original


def _posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def test_ruta_relativa_se_corrige_al_volume():
    # El caso real del incidente: STORAGE_DIR=data con el Volume en /data.
    assert _posix(_settings("data", "/data").storage_dir) == "/data"


def test_ruta_absoluta_fuera_del_volume_se_corrige():
    assert _posix(_settings("/app/data", "/data").storage_dir) == "/data"


def test_prefijo_parecido_no_cuenta_como_dentro():
    assert _posix(_settings("/data2", "/data").storage_dir) == "/data"


def test_ruta_igual_al_volume_se_respeta():
    assert _posix(_settings("/data", "/data").storage_dir) == "/data"


def test_subcarpeta_del_volume_se_respeta():
    assert _posix(_settings("/data/pdfs", "/data").storage_dir) == "/data/pdfs"


def test_sin_volume_no_se_toca():
    # Desarrollo local: no hay Volume y la ruta relativa es válida.
    assert _posix(_settings("data", None).storage_dir) == "data"


def test_volume_vacio_no_se_toca():
    assert _posix(_settings("data", "").storage_dir) == "data"


if __name__ == "__main__":
    failures = 0
    print("Pruebas de STORAGE_DIR dentro del Volume\n")
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print()
    print(f"{failures} fallaron" if failures else "Todas las pruebas pasaron OK")
    sys.exit(1 if failures else 0)
