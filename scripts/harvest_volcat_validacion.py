"""Cosecha los cuadros VOLCAT Ash_Height de los eventos candidatos a validar la
MAGNITUD de la altura propia (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md, paso 0).

Por qué existe: el API de SSEC/RealEarth guarda solo 30 días rodantes (medido el
16-11-2026: `daterange:180` devuelve igual del 17-10 al 16-11). Un evento que no se
guarda antes de que venza queda sin referencia VOLCAT para siempre; los datos GOES
(L1b, ACHA) y el GFS archivado, en cambio, siguen en S3.

No clasifica ni decide nada: solo baja archivos y deja un manifiesto con la URL, el
tamaño y el sha256 de cada uno, para que la validación posterior sea reproducible y
se pueda probar que el dato crudo no se tocó. Los archivos van a
`data/raw/volcat_validacion/` (gitignored) y NUNCA se modifican después.

Es idempotente: un archivo que ya está en disco con el sha256 del manifiesto no se
vuelve a bajar, así que se puede correr de nuevo para completar huecos.

Uso:
    python scripts/harvest_volcat_validacion.py            # todos los eventos
    python scripts/harvest_volcat_validacion.py --dry-run  # solo cuenta cuadros
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fetch.volcat_api import _frame_meta, _query_frames_estado  # noqa: E402

# Destino de la cosecha. Defecto: data/raw/volcat_validacion del checkout; --raw o VOLCAT_VALIDACION_RAW lo
# cambian (--raw manda), por ejemplo para completar una copia fuera del repo.
OUT = Path(os.environ.get("VOLCAT_VALIDACION_RAW") or ROOT / "data" / "raw" / "volcat_validacion")
FMT = "%Y-%m-%d_%H-%M-%S"

# (etiqueta, sector, desde UTC, hasta UTC, rol)
# Las horas salen del sondeo del 16-11-2026 (1 cuadro cada 3 h por sector), ver
# el plan §2. Ventana de ±3 h alrededor de lo visto, para tener la evolución.
# rol "pluma": candidato a comparar. rol "trampa": falsa detección sinóptica del
# tamaño del sector, sirve de caso negativo para el filtro de objeto anclado.
EVENTOS = [
    ("reventador_20261107", "Reventador_250_m", "2026-11-07 17:50", "2026-11-07 23:50", "pluma"),
    ("reventador_20261103", "Reventador_250_m", "2026-11-03 17:50", "2026-11-03 23:50", "pluma"),
    ("reventador_20261026", "Reventador_250_m", "2026-10-26 08:50", "2026-10-26 14:50", "pluma"),
    ("sabancaya_20261101", "Sabancaya_250_m", "2026-10-31 21:30", "2026-11-01 09:30", "pluma"),
    ("sabancaya_20261026", "Sabancaya_250_m", "2026-10-26 06:30", "2026-10-26 15:30", "pluma"),
    ("sabancaya_20261028", "Sabancaya_250_m", "2026-10-28 06:30", "2026-10-28 12:30", "pluma"),
    ("sabancaya_20261017", "Sabancaya_250_m", "2026-10-17 11:50", "2026-10-17 17:50", "pluma"),
    ("cotopaxi_20261025", "Cotopaxi_150_m", "2026-10-25 14:40", "2026-10-25 23:50", "pluma"),
    ("ruiz_20261023", "Ruiz_250_m", "2026-10-23 11:50", "2026-10-23 17:50", "pluma"),
    # Único caso chileno. Chillán no tiene sector dedicado: cae en el regional
    # de 2 km. Sondeo cada 10 min del 08-11: VOLCAT dibuja sobre el volcán de
    # 13:20 a 21:40 UTC, en pulsos de ~2,4 a ~6,5 km (pedido de Nicolás, 16-11).
    ("chillan_20261108", "Chile_Central_2_km", "2026-11-08 12:00", "2026-11-08 23:00", "pluma"),
    ("trampa_sabancaya_20261116", "Sabancaya_250_m", "2026-11-16 08:50", "2026-11-16 10:50", "trampa"),
    ("trampa_ubinas_20261116", "Ubinas_250_m", "2026-11-16 08:50", "2026-11-16 10:50", "trampa"),
    ("trampa_copahue_20261116", "Copahue_250_m", "2026-11-16 08:50", "2026-11-16 10:50", "trampa"),
]

# Capas fijas del sector (mapa, grilla lat/lon, volcanes): una vez por sector.
CAPAS_SECTOR = ("legend_url", "latlon_url", "volcanoes_url")


def _utc(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _bajar(url: str, destino: Path, manifiesto: dict) -> dict:
    """Baja `url` a `destino` si no está ya con el mismo sha256. Devuelve la fila."""
    previo = manifiesto.get(str(destino.relative_to(OUT)).replace("\\", "/"))
    if previo and destino.exists() and _sha256(destino.read_bytes()) == previo.get("sha256"):
        return previo
    fila = {"url": url, "bajado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:  # red caída: se anota, no se inventa el archivo
        fila["error"] = f"{type(e).__name__}: {e}"
        return fila
    fila["http"] = r.status_code
    if r.status_code != 200 or not r.content:
        fila["error"] = f"HTTP {r.status_code}, {len(r.content)} bytes"
        return fila
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    fila["bytes"] = len(r.content)
    fila["sha256"] = _sha256(r.content)
    return fila


def main() -> int:
    global OUT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--raw", type=Path, default=None,
                    help=f"carpeta destino (defecto: {OUT}; también VOLCAT_VALIDACION_RAW)")
    args = ap.parse_args()
    if args.raw is not None:
        OUT = args.raw

    OUT.mkdir(parents=True, exist_ok=True)
    man_path = OUT / "manifiesto.json"
    manifiesto = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}

    listados: dict[str, tuple[list, dict | None]] = {}
    tareas: list[tuple[str, Path]] = []
    resumen = []
    for etiqueta, sector, desde, hasta, rol in EVENTOS:
        if sector not in listados:
            frames, coords, err = _query_frames_estado(sector, "ABI", "Ash_Height", "GOES-19")
            if err:
                print(f"{sector}: {err}", flush=True)
            listados[sector] = (frames, coords)
            # Listado completo y coordenadas tal cual las da SSEC: definen la
            # georreferencia del PNG y qué cuadros existían el día de la cosecha.
            hoy = datetime.now(timezone.utc).strftime("%Y%m%d")
            if not args.dry_run and frames:
                d = OUT / sector
                d.mkdir(parents=True, exist_ok=True)
                (d / f"listado_{hoy}.json").write_text(
                    json.dumps({"coordinates": coords, "endtime": frames}, indent=1),
                    encoding="utf-8")
                meta0 = _frame_meta(frames[-1], sector, "ABI", "Ash_Height", coords)
                for k in CAPAS_SECTOR:
                    nombre = meta0[k].rsplit("/", 1)[-1]
                    tareas.append((meta0[k], d / "capas" / nombre))
        frames, coords = listados[sector]
        t0, t1 = _utc(desde), _utc(hasta)
        sel = []
        for f in frames:
            try:
                t = datetime.strptime(f["datetime"], FMT).replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            if t0 <= t <= t1:
                sel.append(f)
        esperados = int((t1 - t0) / timedelta(minutes=10)) + 1
        resumen.append((etiqueta, sector, rol, len(sel), esperados))
        for f in sel:
            meta = _frame_meta(f, sector, "ABI", "Ash_Height", coords)
            d = OUT / sector / "frames"
            tareas.append((meta["image_url"], d / f"{f['datetime']}.png"))
            if meta["annot_url"]:
                tareas.append((meta["annot_url"], d / f"{f['datetime']}_annot.png"))
        if not args.dry_run:
            ev = OUT / "eventos.json"
            evs = json.loads(ev.read_text(encoding="utf-8")) if ev.exists() else {}
            evs[etiqueta] = {"sector": sector, "desde_utc": desde, "hasta_utc": hasta,
                             "rol": rol, "cuadros": [f["datetime"] for f in sel]}
            ev.write_text(json.dumps(evs, indent=1, ensure_ascii=False), encoding="utf-8")

    for etiqueta, sector, rol, n, esp in resumen:
        print(f"{etiqueta:28s} {sector:18s} {rol:7s} cuadros {n:3d} de {esp:3d} esperados", flush=True)
    # Un cuadro puede pertenecer a dos ventanas: se baja una sola vez.
    unicas = list(dict.fromkeys(tareas))
    print(f"archivos a bajar: {len(unicas)}", flush=True)
    if args.dry_run:
        return 0

    def _uno(t):
        url, destino = t
        return str(destino.relative_to(OUT)).replace("\\", "/"), _bajar(url, destino, manifiesto)

    with ThreadPoolExecutor(4) as ex:
        for i, (clave, fila) in enumerate(ex.map(_uno, unicas), 1):
            manifiesto[clave] = fila
            if i % 50 == 0:
                print(f"  {i}/{len(unicas)}", flush=True)
                man_path.write_text(json.dumps(manifiesto, indent=1), encoding="utf-8")
    man_path.write_text(json.dumps(manifiesto, indent=1), encoding="utf-8")

    errores = {k: v["error"] for k, v in manifiesto.items() if "error" in v}
    total = sum(v.get("bytes", 0) for v in manifiesto.values())
    print(f"listo: {len(manifiesto)} archivos, {total / 1e6:.1f} MB, {len(errores)} con error", flush=True)
    for k, e in list(errores.items())[:20]:
        print(f"  ERROR {k}: {e}", flush=True)
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
