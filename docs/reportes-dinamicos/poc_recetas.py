"""PoC: trocea el corpus por (documento, numero) y mide el coste de cada receta.

No es codigo de produccion: es la prueba de que la arquitectura propuesta en
PROPUESTA.md se sostiene con numeros reales. La version definitiva vive en
scripts/build_kb.py + app/ai/recipes.py.

    py -3 docs/reportes-dinamicos/poc_recetas.py
"""
import re, pathlib, json, hashlib, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[1] / "new-reports"

def slug(p):
    return str(p.relative_to(ROOT)).replace("\\", "/").rsplit(".md", 1)[0]

KB = {}      # slug -> {"intro": str, "nums": {n: str}, "whole": str}
for f in sorted(ROOT.rglob("*.md")):
    if f.name == "README.md":
        continue
    txt = f.read_text(encoding="utf-8")
    parts = re.split(r"^## Significados por n[uú]mero\s*$", txt, flags=re.M)
    intro, body = parts[0], (parts[1] if len(parts) > 1 else "")
    chunks = re.split(r"^### N[uú]mero\s+([0-9]{1,2})\s*$", body, flags=re.M)
    nums = {chunks[i]: chunks[i + 1] for i in range(1, len(chunks), 2)}
    KB[slug(f)] = {"intro": intro, "nums": nums, "whole": txt}

# --- dedupe: parrafos repetidos entre "Fuente:" distintas -------------------
def dedupe(text):
    out, seen = [], set()
    for para in re.split(r"\n\s*\n", text):
        key = hashlib.md5(re.sub(r"\W+", "", para.lower()).encode()).hexdigest()
        if len(para) > 120 and key in seen:
            continue
        seen.add(key)
        out.append(para)
    return "\n\n".join(out)

# --- recetas ---------------------------------------------------------------
# ("documento", "clave-del-numero")  |  ("documento", "@intro") | ("documento","@whole")
RECETAS = {
    "quien-soy": [
        ("01-metodo/significado-espiritual-de-los-numeros", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-personal", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-del-karma", "A"),
        ("02-calculos-de-fecha-de-nacimiento/numero-de-vida-pasada", "C"),
        ("02-calculos-de-fecha-de-nacimiento/numero-de-la-personalidad", "D"),
        ("02-calculos-de-fecha-de-nacimiento/tu-destino", "H"),
        ("02-calculos-de-fecha-de-nacimiento/numero-del-subconsciente", "I"),
        ("02-calculos-de-fecha-de-nacimiento/numero-espejo", "J"),
        ("02-calculos-de-fecha-de-nacimiento/mi-sombra-numero-oculto", "P"),
        ("02-calculos-de-fecha-de-nacimiento/armonico-y-desarmonico", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-del-alma", "ALMA"),
        ("03-calculos-del-nombre/numero-del-nombre", "NOMBRE"),
        ("03-calculos-del-nombre/expresion-del-alma-y-personalidad", "EXPRESION"),
        ("03-calculos-del-nombre/nombre-activo", "ACTIVO"),
    ],
    "amor": [
        ("02-calculos-de-fecha-de-nacimiento/numero-espejo", "J"),
        ("02-calculos-de-fecha-de-nacimiento/numero-personal", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-del-alma", "ALMA"),
        ("05-calculos-de-pareja/relacion-entre-numeros", "B"),
        ("05-calculos-de-pareja/relacion-entre-numeros", "J"),
        ("05-calculos-de-pareja/numero-de-pareja", "PAREJA"),
        ("05-calculos-de-pareja/el-amor-segun-tu-ano-personal", "AP"),
        ("05-calculos-de-pareja/ciclo-de-vida-de-la-pareja", "APREL"),
        ("05-calculos-de-pareja/almas-gemelas-karmicas-y-dharmicas", "@whole"),
        ("05-calculos-de-pareja/sinastria-numerologica", "@intro"),
    ],
    "trabajo": [
        ("02-calculos-de-fecha-de-nacimiento/talentos-personales-y-profesionales", "B"),
        ("02-calculos-de-fecha-de-nacimiento/talentos-personales-y-profesionales", "H"),
        ("02-calculos-de-fecha-de-nacimiento/tu-destino", "H"),
        ("02-calculos-de-fecha-de-nacimiento/numero-personal", "B"),
        ("03-calculos-del-nombre/expresion-del-alma-y-personalidad", "EXPRESION"),
        ("03-calculos-del-nombre/numero-del-nombre", "NOMBRE"),
        ("04-calculos-de-tiempo/ano-personal", "AP"),
        ("04-calculos-de-tiempo/binomios-energeticos", "AP"),
        ("04-calculos-de-tiempo/realizaciones-y-metas-del-ciclo-de-vida", "REAL"),
    ],
    "bienestar": [
        ("01-metodo/significado-espiritual-de-los-numeros", "B"),
        ("02-calculos-de-fecha-de-nacimiento/armonico-y-desarmonico", "B"),
        ("02-calculos-de-fecha-de-nacimiento/armonico-y-desarmonico", "D"),
        ("02-calculos-de-fecha-de-nacimiento/mi-sombra-numero-oculto", "P"),
        ("02-calculos-de-fecha-de-nacimiento/tarea-no-aprendida-y-ausencias", "AUS"),
        ("02-calculos-de-fecha-de-nacimiento/como-potencializar-mi-energia", "@whole"),
        ("06-otros-calculos/deudas-karmicas", "@whole"),
        ("04-calculos-de-tiempo/ano-personal", "AP"),
    ],
    "proposito": [
        ("01-metodo/significado-espiritual-de-los-numeros", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-del-alma", "ALMA"),
        ("02-calculos-de-fecha-de-nacimiento/tu-destino", "H"),
        ("02-calculos-de-fecha-de-nacimiento/mision-del-numero-personal", "B"),
        ("02-calculos-de-fecha-de-nacimiento/numero-de-la-madurez", "MAD"),
        ("02-calculos-de-fecha-de-nacimiento/reidentificacion-con-tu-yo", "B"),
        ("02-calculos-de-fecha-de-nacimiento/encuentro-con-tu-maestro", "MAESTRO"),
        ("02-calculos-de-fecha-de-nacimiento/mi-proyecto-sentido", "PROY"),
        ("04-calculos-de-tiempo/etapas-y-ciclos-de-vida", "E1"),
        ("04-calculos-de-tiempo/etapas-y-ciclos-de-vida", "E2"),
        ("04-calculos-de-tiempo/etapas-y-ciclos-de-vida", "E3"),
        ("04-calculos-de-tiempo/etapas-y-ciclos-de-vida", "E4"),
        ("04-calculos-de-tiempo/realizaciones-y-metas-del-ciclo-de-vida", "REAL"),
    ],
}

# numeros de una persona de ejemplo (Juan Pedro Martinez, 20/11/1991)
NUM = {"A": "11", "B": "2", "C": "2", "D": "6", "H": "4", "I": "1", "J": "7",
       "P": "6", "ALMA": "9", "EXPRESION": "5", "NOMBRE": "5", "ACTIVO": "3",
       "AP": "3", "APREL": "6", "PAREJA": "8", "AUS": "7", "MAD": "6",
       "MAESTRO": "4", "PROY": "2", "REAL": "8", "E1": "4", "E2": "2",
       "E3": "6", "E4": "22"}

print(f"{'receta':<12} {'bruto':>10} {'dedup':>10} {'~tokens':>9}  piezas")
print("-" * 60)
for name, receta in RECETAS.items():
    piezas, faltan = [], []
    for doc, key in receta:
        d = KB.get(doc)
        if d is None:
            faltan.append(doc); continue
        if key == "@whole":
            piezas.append(d["whole"])
        elif key == "@intro":
            piezas.append(d["intro"])
        else:
            n = NUM[key]
            if n in d["nums"]:
                piezas.append(d["nums"][n])
            else:
                faltan.append(f"{doc}#{n}")
    raw = "\n\n".join(piezas)
    ded = dedupe(raw)
    print(f"{name:<12} {len(raw):>10,} {len(ded):>10,} {len(ded)//4:>9,}  {len(piezas)}/{len(receta)}"
          + (f"  FALTAN: {faltan}" if faltan else ""))
