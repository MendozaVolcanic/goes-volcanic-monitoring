"""El triángulo de volcán es UNO solo: hueco y con tamaño canónico por vista.

Por qué (pedido de operaciones, ago-2026): el triángulo marca la POSICIÓN del
cráter — es una referencia geográfica, no un dato. Plotly centra el símbolo en
la coordenada, así que el cráter cae bajo el centro de masa del glifo: si el
marcador es grande y relleno, tapa exactamente lo que se está mirando. Un
frente de lava o un hotspot sub-kilométrico cabe entero debajo (a ±0.75° y
~5 px/km un size=18 cubría ~3.5 km ≈ dos píxeles GOES).

Dos decisiones, y este test las pinea:
1. **Tamaño** por tipo de encuadre, con techo — antes eran literales entre 4 y
   18 repartidos en 14 sitios de 12 vistas, sin criterio común.
2. **Hueco** (`-open`) — achicar reduce el área tapada pero no la elimina: el
   centro del glifo siempre está sobre el cráter. Sólo el contorno abierto deja
   ver el dato a través del marcador.

Si alguien agrega una vista con su propio `symbol="triangle-up"` relleno, o
sube la escala por encima del techo acordado, falla acá.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEWS = Path(__file__).parent.parent / "dashboard" / "views"

# Techo por nivel: el triángulo no debe crecer más allá de ~1 píxel GOES en su
# encuadre típico. Si un cambio futuro los sube, que sea una decisión explícita.
MAX_SIZE = {"wide": 5, "region": 7, "zone": 9, "focus": 12}


def test_volcano_marker_scale_is_sane():
    """La escala canónica existe, es creciente y respeta el techo por nivel."""
    from dashboard.style import VOLCANO_MARKER

    assert set(VOLCANO_MARKER) == set(MAX_SIZE), VOLCANO_MARKER
    for level, top in MAX_SIZE.items():
        assert 2 <= VOLCANO_MARKER[level] <= top, (level, VOLCANO_MARKER[level])
    assert (VOLCANO_MARKER["wide"] < VOLCANO_MARKER["region"]
            < VOLCANO_MARKER["zone"] < VOLCANO_MARKER["focus"])


def test_volcano_marker_is_hollow():
    """El marcador NO debe rellenar: el hotspot bajo el cráter tiene que verse.

    En Plotly los símbolos `-open` dibujan sólo el trazo, con `marker.color`
    como color de línea — por eso el contorno necesita ancho propio.
    """
    from dashboard.style import VOLCANO_MARKER_LINE, volcano_marker

    for level in VOLCANO_MARKER_LINE:
        m = volcano_marker(level)
        assert m["symbol"].endswith("-open"), (level, m["symbol"])
        # Ventana estrecha a propósito: por debajo de 0.5 px el trazo se diluye
        # en el antialiasing y el marcador desaparece sobre fondo claro; por
        # encima de ~1.4 el contorno vuelve a tapar terreno (el borde ocupa
        # área igual que un relleno, que es lo que el hueco vino a evitar).
        assert 0.5 <= m["line"]["width"] <= 1.4, (level, m["line"])
        # el trazo hereda el color del marcador (si no, se dibuja invisible)
        assert m["line"]["color"] == m["color"], (level, m)

    # el trazo acompaña al tamaño: nunca un contorno grueso en un glifo chico
    widths = [VOLCANO_MARKER_LINE[k]
              for k in ("wide", "region", "zone", "focus")]
    assert widths == sorted(widths), widths

    assert volcano_marker("focus", color="#ff4444")["color"] == "#ff4444"
    assert volcano_marker("zone", width=3.0)["line"]["width"] == 3.0


def test_no_view_builds_its_own_volcano_marker():
    """Ninguna vista arma el triángulo a mano: todas pasan por el helper."""
    offenders = []
    for path in sorted(VIEWS.glob("*.py")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "triangle-up" in line:
                offenders.append(f"{path.name}:{n} {line.strip()[:60]}")

    assert not offenders, (
        "usar dashboard.style.volcano_marker() en vez de armar el símbolo:\n  "
        + "\n  ".join(offenders))


def test_no_view_draws_a_solid_triangle_in_pil():
    """Tampoco a mano en los renders PNG del lado servidor.

    Este hueco es real y costó una segunda pasada (ago-2026): el Modo Sala de
    las 4 zonas, el zoom del volcán en alerta, el GIF de los loops y el
    thumbnail de Series NO usan Plotly — componen la imagen con PIL. Cuando el
    marcador de Plotly pasó a hueco, esos cuatro se quedaron RELLENOS, y son
    justamente los que se proyectan en la sala.

    Un `draw.polygon` de TRES vértices es un triángulo dibujado a mano: tiene
    que ir por `map_helpers.draw_volcano_marker_pil`. Los diamantes de hot spot
    (cuatro vértices) sí se dibujan localmente — son el dato, no una
    referencia, y van rellenos a propósito.
    """
    # `d.polygon([...])` con exactamente 3 tuplas en el literal
    tri_call = re.compile(
        r"\.polygon\(\s*\[\s*(\([^)]*\)\s*,\s*){2}\([^)]*\)\s*,?\s*\]", re.S)
    offenders = []
    for path in sorted(VIEWS.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        for m in tri_call.finditer(src):
            offenders.append(f"{path.name}:{src[:m.start()].count(chr(10)) + 1}")
        # y la variante con la lista en una variable llamada `tri`
        for m in re.finditer(r"\.polygon\(\s*tri\b", src):
            offenders.append(f"{path.name}:{src[:m.start()].count(chr(10)) + 1}")

    assert not offenders, (
        "triángulo dibujado a mano en PIL — usar "
        "map_helpers.draw_volcano_marker_pil():\n  " + "\n  ".join(offenders))


def test_no_solid_triangle_marker_in_matplotlib():
    """Y tampoco en los PDF/PNG de matplotlib (reportes de `scripts/`).

    En matplotlib el triángulo se rellena por default: `"r^"` pinta el glifo
    entero. Hueco = `markerfacecolor="none"`.
    """
    scripts = Path(__file__).parent.parent / "scripts"
    offenders = []
    for path in sorted(scripts.glob("*.py")):
        # Sin comentarios: si no, el propio comentario que explica el fix
        # ("usar markerfacecolor=none") hace pasar el test — falso verde
        # verificado por mutación.
        lines = [re.sub(r"#.*$", "", ln)
                 for ln in path.read_text(encoding="utf-8").splitlines()]
        src = "\n".join(lines)
        for m in re.finditer(r'"[a-z]?\^"|marker\s*=\s*[\'"]\^[\'"]', src):
            # la llamada completa (hasta el paréntesis de cierre de la línea
            # lógica) es donde tiene que estar el facecolor
            window = src[m.start():m.start() + 400].split(")\n")[0]
            if "markerfacecolor" not in window and "mfc" not in window:
                line = src[:m.start()].count("\n") + 1
                offenders.append(f"{path.name}:{line}")

    assert not offenders, (
        'triángulo relleno en matplotlib — usar markerfacecolor="none":\n  '
        + "\n  ".join(offenders))


def test_pil_volcano_marker_is_hollow():
    """El helper PIL no rellena y deja halo de contraste (sobre nube blanca un
    trazo cian fino desaparece)."""
    from PIL import Image, ImageDraw

    from dashboard.map_helpers import draw_volcano_marker_pil

    img = Image.new("RGB", (41, 41), (255, 255, 255))
    draw_volcano_marker_pil(ImageDraw.Draw(img), 20, 20, size=12)
    # el centro (donde cae el cráter) sigue siendo el fondo, no el marcador
    assert img.getpixel((20, 20)) == (255, 255, 255), img.getpixel((20, 20))
    # y el trazo existe: hay píxeles cian en el borde inferior del triángulo
    row = [img.getpixel((x, 28)) for x in range(41)]
    assert (0, 255, 255) in row, "no se dibujó el contorno cian"


def test_every_view_uses_a_known_level():
    """Los niveles que pasan las vistas existen en la escala (un typo como
    `volcano_marker("zoom")` reventaría recién al renderizar esa vista)."""
    from dashboard.style import VOLCANO_MARKER

    used, bad = set(), []
    for path in sorted(VIEWS.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        for m in re.finditer(r'volcano_marker\(\s*"([^"]+)"', src):
            used.add(m.group(1))
            if m.group(1) not in VOLCANO_MARKER:
                bad.append(f"{path.name}: nivel '{m.group(1)}'")
        # el overlay de volcat propaga el nivel en vez de un tamaño en px
        for m in re.finditer(r'_overlay_volcanoes_border\([^)]*level(?::\s*str)?'
                             r'\s*=\s*"([^"]+)"', src):
            used.add(m.group(1))
            if m.group(1) not in VOLCANO_MARKER:
                bad.append(f"{path.name}: level '{m.group(1)}'")

    assert not bad, bad
    # sanity: el refactor tocó las 12 vistas, así que deben aparecer los 4 niveles
    assert used == set(VOLCANO_MARKER), used
