"""Funciones numerológicas base.

Port fiel de `reports-pdf/src/helpers.php` (reduceNumber / reduceNumberForSub).
Estas funciones son el corazón de todos los cálculos y su comportamiento debe
ser IDÉNTICO al proyecto original en PHP.

Regla: se reduce la suma de dígitos hasta obtener un solo dígito, salvo los
"números maestros" 11 y 22, que no se reducen.
"""

from __future__ import annotations

_MASTER_NUMBERS = (11, 22)


def _digit_sum(n: int) -> int:
    return sum(int(d) for d in str(n))


def reduce_number(value: int) -> int:
    """Reduce a un dígito, respetando los maestros 11 y 22.

    Equivalente a `reduceNumber()` en helpers.php.
    """
    n = int(value)
    while n > 9 and n not in _MASTER_NUMBERS:
        n = _digit_sum(n)
    return n


def reduce_number_for_sub(value: int) -> int:
    """Reduce siempre a un dígito (sin excepción de maestros).

    Equivalente a `reduceNumberForSub()` en helpers.php. Se usa en la sinastría
    de pareja donde después se calculan diferencias.
    """
    n = int(value)
    while n > 9:
        n = _digit_sum(n)
    return n
