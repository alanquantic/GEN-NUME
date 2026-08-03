"""Comprime PDFs existentes (p. ej. los estáticos de assets/static).

    # sólo recompresión estructural (sin pérdida):
    py -3 scripts/compress_pdf.py archivo.pdf [mas.pdf ...]

    # además re-encoda los JPG de fondo (con pérdida, revisar resultado):
    py -3 scripts/compress_pdf.py --images archivo.pdf
    py -3 scripts/compress_pdf.py --images --max-px 1400 --quality 75 archivo.pdf

Escribe `<nombre>.min.pdf` junto al original; nunca lo sobreescribe.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.pdf.compress import slim, slim_images  # noqa: E402


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 1

    with_images = "--images" in args
    max_px, quality = 1600, 80
    if "--max-px" in args:
        max_px = int(args[args.index("--max-px") + 1])
    if "--quality" in args:
        quality = int(args[args.index("--quality") + 1])

    files = [Path(a) for a in args
             if not a.startswith("--") and a not in (str(max_px), str(quality))]

    print(f"{'ARCHIVO':<44}{'ANTES':>10}{'DESPUÉS':>10}{'AHORRO':>8}")
    print("-" * 72)
    for path in files:
        data = path.read_bytes()
        out = (slim_images(data, max_px=max_px, jpeg_quality=quality)
               if with_images else slim(data))
        dst = path.with_suffix(".min.pdf")
        dst.write_bytes(out)
        saved = 100 * (1 - len(out) / len(data))
        print(f"{path.name:<44}{len(data) // 1024:>9}K{len(out) // 1024:>9}K{saved:>7.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
