"""Copia y OPTIMIZA los assets de imagen que usa el catálogo activo.

Del proyecto original (reports-pdf/assets/report) toma solo las carpetas que
necesitan los 16 reportes activos, recomprime cada JPEG (limita el borde largo
a ~150 DPI para A4 y baja la calidad) y las escribe en assets/report/,
preservando la estructura de carpetas.

Ejecutar:  .venv/Scripts/python.exe scripts/optimize_assets.py
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / ".." / "reports-pdf" / "assets" / "report").resolve()
DST = ROOT / "assets" / "report"

# Carpetas usadas por el catálogo activo (16 reportes).
NEEDED = [
    "quien-soy-g",            # reporte-quien-soy
    "quien-soy-e",            # reporte-quien-soy-extended
    "etapa-vida-g",           # reporte-etapa-de-vida-*
    "horoscopo",              # horoscopo
    "amor",                   # amor-pareja-ano-personal
    "pareja-g",               # reporte-pareja / -2025 / -2023
    "pareja",                 # bonus-pareja (no genérico)
    "maestro-g",              # reporte-maestro
    "herida-g",               # reporte-herida
    "antidoto-g",             # reporte-antidoto
    "personalidad-pareja-g",  # reporte-personalidad-pareja
    "lectura-pareja-g",       # reporte-lectura-pareja
]

MAX_LONG_EDGE = 1600   # ~135-150 DPI para A4; suficiente para fondo de página
QUALITY = 72
EXTS = {".jpg", ".jpeg", ".png"}


def optimize_one(src_file: Path, dst_file: Path) -> tuple[int, int]:
    before = src_file.stat().st_size
    with Image.open(src_file) as im:
        im = im.convert("RGB")
        long_edge = max(im.size)
        if long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / long_edge
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        buf = BytesIO()
        im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    data = buf.getvalue()
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    # Nunca inflar: si el original ya era más pequeño, se conserva tal cual.
    if len(data) < before:
        dst_file.write_bytes(data)
    else:
        dst_file.write_bytes(src_file.read_bytes())
    return before, dst_file.stat().st_size


def main() -> int:
    if not SRC.exists():
        print(f"No existe la carpeta origen: {SRC}")
        return 1

    grand_before = grand_after = count = 0
    print(f"{'CARPETA':<26}{'IMGS':>6}{'ANTES(MB)':>11}{'DESPUES(MB)':>13}")
    print("-" * 56)
    for folder in NEEDED:
        src_dir = SRC / folder
        if not src_dir.exists():
            print(f"{folder:<26}{'--- no existe en origen ---':>30}")
            continue
        fb = fa = fc = 0
        for src_file in sorted(src_dir.rglob("*")):
            if src_file.is_file() and src_file.suffix.lower() in EXTS:
                rel = src_file.relative_to(src_dir)
                dst_file = (DST / folder / rel).with_suffix(".jpg")
                b, a = optimize_one(src_file, dst_file)
                fb += b; fa += a; fc += 1
        grand_before += fb; grand_after += fa; count += fc
        print(f"{folder:<26}{fc:>6}{fb/1e6:>11.1f}{fa/1e6:>13.1f}")

    print("-" * 56)
    pct = (1 - grand_after / grand_before) * 100 if grand_before else 0
    print(f"{'TOTAL':<26}{count:>6}{grand_before/1e6:>11.1f}{grand_after/1e6:>13.1f}")
    print(f"\nReduccion: {grand_before/1e6:.0f} MB -> {grand_after/1e6:.0f} MB  ({pct:.0f}% menos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
