"""Snapshots VIIRS (True Color + anomalías térmicas 375 m) de volcanes patagónicos.

Por qué: varios volcanes australes (Hudson, Chaitén, Melimoyu, Corcovado, Yanteles,
Mentolat…) no tienen sector VOLCAT ni monitoreo dedicado; GOES los ve a 2 km. VIIRS
(polar, 375 m, ~2 pasadas/día) es el complemento natural, y GIBS lo sirve ya
georreferenciado. Este script baja un True Color y el overlay térmico de cada volcán
al sur de una latitud dada, para una fecha, y reporta cobertura de la pasada.

Es una vista COMPLEMENTARIA, separada de la cadena ABI NRT (no se mezcla).

Uso:
    python scripts/viirs_patagonia_snapshots.py                 # ayer, lat < -42
    python scripts/viirs_patagonia_snapshots.py --date 2026-06-15 --lat-max -40
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from PIL import Image

from src.fetch.viirs_gibs import _default_date, fetch_viirs_image
from src.volcanos import CATALOG


def _slug(name: str) -> str:
    out = name.lower().replace(" ", "-")
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ñ", "n"), ("(", ""), (")", "")):
        out = out.replace(a, b)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD UTC (default ayer)")
    ap.add_argument("--lat-max", type=float, default=-42.0,
                    help="incluir volcanes con lat < esto (default -42 = Patagonia)")
    ap.add_argument("--pad", type=float, default=0.6, help="medio ancho de caja (°)")
    ap.add_argument("--out", default=r"C:\Users\nmend\Downloads\viirs_patagonia",
                    help="carpeta de salida")
    args = ap.parse_args()

    when = args.date or _default_date()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sur = sorted([v for v in CATALOG if v.lat < args.lat_max], key=lambda v: v.lat)
    print(f"VIIRS {when} · {len(sur)} volcanes al sur de {args.lat_max}° · "
          f"salida: {out}")

    for v in sur:
        tc = fetch_viirs_image(v.lat, v.lon, when=when, layer="truecolor",
                               pad_deg=args.pad, size=512)
        th = fetch_viirs_image(v.lat, v.lon, when=when, layer="thermal",
                               pad_deg=args.pad, size=512)
        cov = tc["coverage_frac"] if tc else 0.0
        thc = th["coverage_frac"] if th else 0.0
        tag = "OK " if cov > 0.05 else "sin pasada"
        flag = "  🔥 ANOMALÍA TÉRMICA" if thc > 0.0 else ""
        print(f"  {v.name:22} cobertura {cov*100:3.0f}%  [{tag}]{flag}")
        if tc and cov > 0.05:
            base = out / f"viirs_{when}_{_slug(v.name)}"
            Image.fromarray(tc["image"]).save(base.with_name(base.name + "_truecolor.png"))
            if th and thc > 0.0:
                Image.fromarray(th["image"]).save(
                    base.with_name(base.name + "_thermal.png"))
    print("Listo.")


if __name__ == "__main__":
    main()
