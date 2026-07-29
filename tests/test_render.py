"""Pruebas de la fase 5 (maquetación) que NO necesitan WeasyPrint.

Cubren la generación de gráficos SVG y del HTML del reporte. El paso final a PDF
(`html_renderer.to_pdf`) sólo corre en un sistema con las libs nativas y no se
ejercita aquí.

    py -3 tests/test_render.py
"""

import io
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import generate as gen        # noqa: E402
from app.ai import numbers as num         # noqa: E402
from app.pdf import charts                # noqa: E402
from app.pdf import html_renderer as hr   # noqa: E402
from app.domain.pinnacle import Pinnacle  # noqa: E402
from app.domain.dates import format_long_date  # noqa: E402

TODAY = date(2026, 7, 29)
NAME = "Juan Pedro Martinez"
BIRTH = date(1991, 11, 20)
NUMBERS = num.resolve(NAME, BIRTH, today=TODAY)
PIN = NUMBERS.pinnacle


def _svg_ok(svg: str) -> None:
    assert svg.startswith("<svg"), "no empieza por <svg"
    ET.fromstring(svg)          # bien formado


# --------------------------------------------------------------------------- #
# Gráficos
# --------------------------------------------------------------------------- #
def test_pinaculo_svg_bien_formado_y_con_valores():
    svg = charts.pinnacle_svg(PIN)
    _svg_ok(svg)
    assert ">11<" in svg          # A = karma 11
    assert "AUSENCIAS" in svg
    assert "SER SUPERIOR" in svg


def test_tira_del_nombre():
    svg = charts.name_strip_svg("juan-pedro-martinez", "3", "9")
    _svg_ok(svg)
    assert "ALMA 3" in svg and "EXPRESIÓN 9" in svg
    # "juanpedromartinez" = 17 letras -> 17 glifos con class="lt"
    assert svg.count('class="lt"') == 17


def test_ausencias_svg():
    svg = charts.absences_svg(PIN)
    _svg_ok(svg)
    # 9 celdas
    assert svg.count("<rect") == 9


def test_etapas_svg():
    svg = charts.stages_svg(PIN, PIN.age_at(TODAY))
    _svg_ok(svg)
    assert "ESTÁS AQUÍ" in svg


def test_rueda_ano_personal():
    svg = charts.personal_year_svg("5")
    _svg_ok(svg)
    assert "AÑO PERSONAL" in svg


def test_rueda_maneja_ano_11():
    # el 11 no está en el anillo 1-9; debe resaltar el sector 2 sin romperse
    svg = charts.personal_year_svg("11")
    _svg_ok(svg)


# --------------------------------------------------------------------------- #
# HTML del reporte
# --------------------------------------------------------------------------- #
def _render(report_key="quien-soy", partner=False):
    data, *_ = gen._load_mock("quien-soy") if report_key == "quien-soy" else (_stub(), )
    numbers = num.resolve(NAME, BIRTH, today=TODAY,
                          partner_birth_date=date(1988, 3, 5) if partner else None)
    from app.ai.recipes import REPORTS
    r = REPORTS[report_key]
    return hr.render_html(
        report_key, data, numbers,
        report_title=r.title, area_token=r.area,
        person_name=NAME, birth_long=format_long_date(BIRTH),
        today_long=format_long_date(TODAY),
        today_age=numbers.pinnacle.age_at(TODAY),
    )


def _stub():
    """Contenido mínimo válido para reportes sin mock (probar la maqueta)."""
    return {
        "titulo": "x", "subtitulo": "x", "frase_clave": "x", "resumen_portada": "x",
        "retrato": {"titulo": "x", "cuerpo": ["x"]},
        "secciones": [{"id": "s1", "titulo": "S1", "entradilla": "e",
                       "cuerpo": ["c"], "numeros": ["B"], "destacado": None,
                       "cierre_accionable": "a"}],
        "tension_central": {"titulo": "t", "numeros": ["B", "A"],
                            "cuerpo": ["c"], "como_resolverla": "r"},
        "plan": [{"titulo": "p", "texto": "t"}],
        "cierre": "fin",
    }


def test_html_quien_soy_estructura():
    html = _render("quien-soy")
    assert html.count('class="page"') >= 14
    assert "PassionOne" not in html or "Open Sans" in html   # css cargó
    ET.fromstring(_only_body_svgs(html)[0])                  # primer svg válido
    # color de área violeta inyectado
    assert "--area:#4C1D95" in html


def test_html_inyecta_color_de_area_por_reporte():
    html_bienestar = _render_stub("bienestar")
    assert "--area:#059669" in html_bienestar               # verde bienestar
    html_amor = _render_stub("amor")
    assert "--area:#EC4899" in html_amor                    # rosa amor


def _render_stub(report_key):
    numbers = num.resolve(NAME, BIRTH, today=TODAY)
    from app.ai.recipes import REPORTS
    r = REPORTS[report_key]
    return hr.render_html(
        report_key, _stub(), numbers,
        report_title=r.title, area_token=r.area,
        person_name=NAME, birth_long="x", today_long="y",
        today_age=numbers.pinnacle.age_at(TODAY),
    )


def test_bienestar_lleva_aviso_sanitario():
    html = _render_stub("bienestar")
    assert "no constituye diagnóstico" in html


def test_todos_los_reportes_maquetan_con_stub():
    from app.ai.recipes import REPORTS
    for key in REPORTS:
        html = _render_stub(key)
        assert html.count('class="page"') >= 5
        # todos los svg de charts, bien formados
        for svg in _only_body_svgs(html):
            ET.fromstring(svg)


def _only_body_svgs(html: str) -> list[str]:
    return re.findall(r"<svg.*?</svg>", html, re.S)


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    failures = 0
    print("Pruebas de maquetación (sin WeasyPrint)\n")
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
