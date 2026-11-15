"""Los textos del dashboard van en español de Chile: tú, nunca voseo.

Por qué: el dashboard lo leen y lo proyectan geólogos de OVDAS; "presioná",
"probá" o "podés" delatan texto escrito desde otro país (o generado) y
desentonan en una herramienta institucional de SERNAGEOMIN. La regla vive
en el CLAUDE.md del usuario; esta prueba la hace cumplir en todos los
strings de `dashboard/` y `src/` (lo que ve el operador y los docstrings).

Lista explícita y no una regla por terminación: "está", "acá", "podrá" o
"aquí" terminan en vocal acentuada y son correctos.
"""

import ast
import re
from pathlib import Path

RAIZ = Path(__file__).parent.parent

VOSEO = {
    "tenés", "podés", "querés", "sabés", "elegí", "presioná", "apretá",
    "mirá", "fijate", "andá", "probá", "poné", "tocá", "usá", "hacé",
    "generá", "encadenalos", "cambiá", "bajá", "subí", "abrí", "esperá",
    "revisá", "dejá", "activá", "desactivá", "tildá", "destildá",
    "seleccioná", "deslizá", "arrastrá", "volvé", "escribí", "consultá",
    "verificá", "podes", "tenes", "queres", "pedís", "pedis", "elegís",
    "elegis", "elegi", "perdés", "perdes", "vos", "eleginado",
}
_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúÑñü]+")


def _strings(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def test_ningun_texto_usa_voseo():
    hallazgos = []
    for carpeta in ("dashboard", "src"):
        for path in sorted((RAIZ / carpeta).rglob("*.py")):
            for linea, texto in _strings(path):
                malas = {p for p in _PALABRA.findall(texto)
                         if p.lower() in VOSEO}
                if malas:
                    hallazgos.append(
                        f"{path.relative_to(RAIZ)}:{linea} {sorted(malas)}")
    assert not hallazgos, "voseo en textos:\n" + "\n".join(hallazgos)
