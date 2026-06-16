"""Regenera el array 'coast' de dashboard/chile_geometry.json desde
Natural Earth 10m coastline (dominio publico), cubriendo TODA la costa
chilena: Arica (lat ~-17.5) -> Cabo de Hornos (lat ~-56), no solo el sur.

Por que: la costa del JSON solo iba lat -55 a -42 (bug de extraccion previa)
-> faltaba toda la costa central/norte del Pacifico (Puerto Montt -> Arica:
Valparaiso, Coquimbo, Antofagasta...) en TODAS las vistas que usan
dashboard.map_helpers.add_chile_border. La frontera Andina ('border') ya
estaba completa y NO se toca (viene de otra fuente, IGM Chile). (jun 2026)

Requiere geopandas (solo dev/build, NO runtime de la app). El dashboard solo
LEE el JSON resultante.

Uso: python scripts/build_chile_coast.py
"""
from __future__ import annotations

import json
import os
import tempfile
import urllib.request
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
GEO_JSON = ROOT / "dashboard" / "chile_geometry.json"

# Natural Earth 10m physical coastline (public domain).
NE_URL = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_coastline.zip"
# bbox Pacifico chileno (minx, miny, maxx, maxy) = (lon_w, lat_s, lon_e, lat_n).
# lon_e=-68.5 deja afuera la costa atlantica argentina; lat -56.5..-17 cubre
# de Cabo de Hornos al limite con Peru.
BBOX = (-76.5, -56.5, -68.5, -17.0)
SIMPLIFY_TOL = 0.003  # Douglas-Peucker ~330 m (mismo criterio que el original)


# Frontera Chile-Peru (norte): el dato IGM ('border') concatena ZEE austral +
# Argentina + Bolivia pero NO incluye Peru -> faltaba el limite norte. Se
# extrae aparte de Natural Earth admin_0 boundary lines y se ANEXA al border
# (sin tocar el resto). (jun 2026, pedido OVDAS)
NE_BORDER_URL = ("https://naturalearth.s3.amazonaws.com/10m_cultural/"
                 "ne_10m_admin_0_boundary_lines_land.zip")
PERU_BBOX = (-70.7, -18.7, -69.2, -17.1)  # lon_w, lat_s, lon_e, lat_n


def _chile_peru_border() -> list[list]:
    """Tramo del limite Chile-Peru (tripoint -> costa de Arica) desde NE."""
    tmp = os.path.join(tempfile.gettempdir(), "ne_10m_admin0_lines.zip")
    if not os.path.exists(tmp):
        req = urllib.request.Request(NE_BORDER_URL,
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            f.write(r.read())
    gdf = gpd.read_file("zip://" + tmp)
    clip = gdf.clip(PERU_BBOX)
    seg: list[list] = []
    for geom in clip.geometry:
        if geom is None or geom.is_empty:
            continue
        parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for ls in parts:
            ls = ls.simplify(SIMPLIFY_TOL)
            if ls.is_empty:
                continue
            xs, ys = ls.xy
            for lon, lat in zip(xs, ys):
                seg.append([round(float(lat), 4), round(float(lon), 4)])
            seg.append([None, None])
    return seg


def main() -> int:
    tmp = os.path.join(tempfile.gettempdir(), "ne_10m_coastline.zip")
    if not os.path.exists(tmp):
        req = urllib.request.Request(NE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            f.write(r.read())

    gdf = gpd.read_file("zip://" + tmp)
    clip = gdf.clip(BBOX)

    coast: list[list] = []
    for geom in clip.geometry:
        if geom is None or geom.is_empty:
            continue
        parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for ls in parts:
            ls = ls.simplify(SIMPLIFY_TOL)
            if ls.is_empty:
                continue
            xs, ys = ls.xy  # lon, lat
            for lon, lat in zip(xs, ys):
                coast.append([round(float(lat), 4), round(float(lon), 4)])
            coast.append([None, None])  # "lift pen" entre segmentos (Plotly)

    data = json.loads(GEO_JSON.read_text(encoding="utf-8"))
    data["coast"] = coast

    # Anexar el tramo Chile-Peru al border si falta (idempotente: si ya hay
    # puntos en lat -18.7..-17.1 con lon <= -69.9, no re-anexar).
    border = data.get("border", [])
    has_peru = any(c and c[0] is not None and c[1] is not None
                   and -18.7 <= c[0] <= -17.1 and c[1] <= -69.9 for c in border)
    if not has_peru:
        peru = _chile_peru_border()
        if peru:
            if border and border[-1] != [None, None]:
                border = border + [[None, None]]
            data["border"] = border + peru
            print(f"border: +{sum(1 for p in peru if p[0] is not None)} "
                  f"pts Chile-Peru anexados")
    else:
        print("border: tramo Chile-Peru ya presente")

    GEO_JSON.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")

    valid = [c for c in coast if c[0] is not None]
    lats = [c[0] for c in valid]
    lons = [c[1] for c in valid]
    print(f"coast: {len(coast)} pts ({len(valid)} val, "
          f"{len(coast) - len(valid)} separadores)")
    print(f"   lat [{min(lats):.2f}, {max(lats):.2f}]  "
          f"lon [{min(lons):.2f}, {max(lons):.2f}]")
    print(f"json: {GEO_JSON.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
