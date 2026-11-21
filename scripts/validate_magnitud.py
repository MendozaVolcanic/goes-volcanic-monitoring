"""Validación de MAGNITUD de la altura propia contra VOLCAT (pasos 3 a 6 del plan).

Por qué: la altura propia (BT-matching, Wen-Rose, ACHA ∩ ceniza) sólo estaba
validada en comportamiento. Aquí se compara el NÚMERO contra VOLCAT (SSEC/CIMSS)
en plumas que VOLCAT sí mide, scan por scan, con el criterio que Nicolás fijó el
16-11-2026 antes de ver números (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md):
un scan es consistente si el intervalo del tope VOLCAT (bloque de la barra) se
cruza con nuestro intervalo, sin margen; por método; se cuenta cuántos cumplen.

Etapas (cada una deja un JSON en docs/own_volcat/validacion_magnitud/):

  volcat    lee los PNG Ash_Height cosechados en el paso 0 (sin red) y fija, por
            cuadro, el tope del objeto VOLCAT anclado al volcán, entero y
            recortado a la misma caja que usan nuestros métodos.
  recortes  arma mosaicos de los cuadros VOLCAT alrededor del volcán para la
            revisión a ojo del manto sinóptico (plan §3.4, opción c). Sólo mira
            VOLCAT; la lista de exclusión se escribe a mano en exclusiones.json.
  propios   corre los tres métodos en el mismo scan de cada cuadro con tope y no
            excluido, con el GFS archivado inyectado. Reanudable; borra los L1b
            de disco tras cada scan.
  comparar  aplica el criterio y escribe la tabla (markdown) por método y evento.

Uso:
    python scripts/validate_magnitud.py volcat
    python scripts/validate_magnitud.py recortes --out <carpeta>
    python scripts/validate_magnitud.py propios [--solo EVENTO] [--max N]
    python scripts/validate_magnitud.py comparar

Datos de entrada: data/raw/volcat_validacion/ (gitignored, ver manifiesto.json
con URL y sha256 de cada PNG). Salidas versionadas: docs/own_volcat/validacion_magnitud/.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np  # noqa: E402

# Cuadros VOLCAT de entrada. Defecto: data/raw/volcat_validacion del checkout. En un worktree esa carpeta no
# existe (gitignored); se apunta a otra copia con --raw o con la variable VOLCAT_VALIDACION_RAW (--raw manda).
RAW = Path(os.environ.get("VOLCAT_VALIDACION_RAW") or ROOT / "data" / "raw" / "volcat_validacion")
OUT = ROOT / "docs" / "own_volcat" / "validacion_magnitud"
F_VOLCAT = OUT / "volcat_lecturas.json"
F_EXCL = OUT / "exclusiones.json"
F_PROPIOS = OUT / "propios.json"
F_TABLA = OUT / "tabla.md"

# Caja de comparación: la misma que usan nuestros métodos por defecto en la app
# (radius_deg=0.75, ±83 km). Se valida el número que el operador vería.
RADIO_DEG = 0.75

# Eventos con pluma y volcán con coordenada citada. Los "trampa" (mantos del
# 16-11) y Ruiz (un solo píxel, descartado en el paso 2) no entran.
EVENTOS_VOLCAN = {
    "reventador_20261107": "Reventador",
    "reventador_20261103": "Reventador",
    "reventador_20261026": "Reventador",
    "sabancaya_20261101": "Sabancaya",
    "sabancaya_20261026": "Sabancaya",
    "sabancaya_20261028": "Sabancaya",
    "sabancaya_20261017": "Sabancaya",
    "cotopaxi_20261025": "Cotopaxi",
    "chillan_20261108": "Nevados de Chillan",
}


def _volcan(nombre: str):
    from src.volcanos import get_volcano
    from src.volcanos_validacion import VALIDACION
    if nombre in VALIDACION:
        return VALIDACION[nombre].volcano
    return get_volcano(nombre)


def _georef(sector: str):
    """(lat0, lon0, dp_grados, px_km) de la grilla CE del sector, igual que
    src.fetch.volcat_api.volcat_height_at."""
    from src.fetch.volcat_api import R_TIERRA_MEDIO_KM
    listados = sorted((RAW / sector).glob("listado_*.json"))
    c = json.loads(listados[-1].read_text(encoding="utf-8"))["coordinates"]
    assert str(c.get("PROJECTION", "")).upper() == "CE", sector
    dp = math.degrees(c["SCALE_FACTOR"] / c["EQ_RADIUS"])
    olon = c["ORIGIN_LON"] - 360.0 if c["ORIGIN_LON"] > 180.0 else c["ORIGIN_LON"]
    lon0 = olon + c.get("OFFSET_X", 0) * dp
    lat0 = c["ORIGIN_LAT"] + c.get("OFFSET_Y", 0) * dp
    return lat0, lon0, dp, math.radians(dp) * R_TIERRA_MEDIO_KM


def _pix(v, lat0, lon0, dp):
    return int(round((lat0 - v.lat) / dp)), int(round((v.lon - lon0) / dp))


def _recortar_a_caja(a, row, col, dp, radio_deg):
    """Copia del PNG con el MAPA fuera de la caja ±radio pintado de negro
    (saturación 0: deja de ser candidato). La leyenda de abajo no se toca."""
    from src.process.volcat_colorbar import MAP_FRAC
    b = a.copy()
    hmap = int(MAP_FRAC * a.shape[0])
    r = int(round(radio_deg / dp))
    m = np.ones((hmap, a.shape[1]), bool)
    m[max(0, row - r):row + r + 1, max(0, col - r):col + r + 1] = False
    b[:hmap][m] = 0.0
    return b


def _lee_png(p: Path):
    from PIL import Image
    return np.asarray(Image.open(p).convert("RGB")).astype("float64")


def etapa_volcat(_args):
    """Lectura VOLCAT de cada cuadro de los eventos con pluma (sin red)."""
    from src.process.volcat_colorbar import volcat_object_heights
    eventos = json.loads((RAW / "eventos.json").read_text(encoding="utf-8"))
    out = {}
    for ev, nombre in EVENTOS_VOLCAN.items():
        e = eventos[ev]
        v = _volcan(nombre)
        lat0, lon0, dp, px_km = _georef(e["sector"])
        px_ew = px_km * math.cos(math.radians(v.lat))
        row, col = _pix(v, lat0, lon0, dp)
        filas = []
        for cu in e["cuadros"]:
            p = RAW / e["sector"] / "frames" / f"{cu}.png"
            if not p.exists():
                filas.append({"cuadro": cu, "nota": "PNG no cosechado"})
                continue
            a = _lee_png(p)
            entero = volcat_object_heights(a, row, col, px_km=px_km, px_km_ew=px_ew)
            caja = volcat_object_heights(_recortar_a_caja(a, row, col, dp, RADIO_DEG),
                                         row, col, px_km=px_km, px_km_ew=px_ew)
            filas.append({"cuadro": cu, "entero": entero, "caja": caja})
        out[ev] = {"sector": e["sector"], "volcan": v.name,
                   "lat": v.lat, "lon": v.lon, "cumbre_km": v.elevation / 1000.0,
                   "px_volcan": [row, col], "px_km": px_km, "cuadros": filas}
        n_top = sum(1 for f in filas if "top_lo_km" in f.get("caja", {}))
        print(f"{ev:22} {len(filas):3} cuadros · {n_top:3} con tope en la caja")
    OUT.mkdir(parents=True, exist_ok=True)
    F_VOLCAT.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float),
                        encoding="utf-8")
    print(f"→ {F_VOLCAT}")


def etapa_recortes(args):
    """Mosaicos por evento: recorte ±radio_px alrededor del volcán, disco de
    10 km dibujado, hora y tope VOLCAT rotulados. Sólo cuadros con objeto
    anclado o con nota de manto (lo que hay que revisar a ojo)."""
    from PIL import Image, ImageDraw
    lect = json.loads(F_VOLCAT.read_text(encoding="utf-8"))
    dst = Path(args.out)
    dst.mkdir(parents=True, exist_ok=True)
    lado = args.lado_km
    for ev, d in lect.items():
        row, col = d["px_volcan"]
        r = int(round(lado / d["px_km"]))
        r10 = 10.0 / d["px_km"]
        tiles = []
        for f in d["cuadros"]:
            ent = f.get("entero", {})
            if "top_lo_km" not in ent and not ent.get("sector_wide") and "n" not in ent:
                continue
            im = Image.open(RAW / d["sector"] / "frames" / f"{f['cuadro']}.png").convert("RGB")
            cr = im.crop((col - r, row - r, col + r, row + r)).resize((240, 240))
            dr = ImageDraw.Draw(cr)
            s = 240 / (2 * r)
            dr.ellipse((120 - r10 * s, 120 - r10 * s, 120 + r10 * s, 120 + r10 * s),
                       outline=(255, 255, 255))
            tope = (f"{ent['top_lo_km']}-{ent['top_hi_km']}" if "top_lo_km" in ent
                    else ("MANTO" if ent.get("sector_wide") else "sin tope"))
            dr.rectangle((0, 0, 240, 14), fill=(0, 0, 0))
            dr.text((2, 1), f"{f['cuadro'][5:16]} {tope}", fill=(255, 255, 0))
            tiles.append(cr)
        if not tiles:
            continue
        nc = 8
        nr = math.ceil(len(tiles) / nc)
        mos = Image.new("RGB", (nc * 240, nr * 240), (40, 40, 40))
        for i, t in enumerate(tiles):
            mos.paste(t, ((i % nc) * 240, (i // nc) * 240))
        mos.save(dst / f"{ev}.jpg", quality=80)
        print(f"{ev}: {len(tiles)} cuadros → {dst / (ev + '.jpg')}")


def _cuadros_a_correr(lect, excl):
    for ev, d in lect.items():
        ex = excl.get(ev, {})
        todo = ex.get("todo")
        for f in d["cuadros"]:
            caja = f.get("caja", {})
            if "top_lo_km" not in caja:
                continue
            if f.get("entero", {}).get("sector_wide"):
                continue
            if todo or f["cuadro"] in ex.get("cuadros", {}):
                continue
            yield ev, d, f


def _dt_cuadro(cu: str) -> datetime:
    return datetime.strptime(cu, "%Y-%m-%d_%H-%M-%S").replace(tzinfo=timezone.utc)


def _resumen(r: dict, metodo: str) -> dict:
    keep = ("status", "reason", "top_km", "top_max_km", "top_km_lo", "top_km_hi",
            "mask_px", "n_capped", "all_capped", "confidence", "flags",
            "tropopause_km", "profile_time", "top_bt_matching_km", "ts_k",
            "ts_source", "n_clear", "below_summit", "co2_semitransp_btd")
    o = {k: r.get(k) for k in keep if k in r}
    sd = r.get("scan_dt")
    o["scan_dt"] = sd.strftime("%Y-%m-%dT%H:%M:%SZ") if sd else None
    o["metodo"] = metodo
    return o


def _limpiar_l1b(dt):
    """Borra los full-disk L1b de ESE scan bajados a data/raw/ (caché, se re-baja
    si hace falta). Sólo los del scan: otros procesos del lote corren en paralelo.
    No toca data/raw/volcat_validacion/."""
    from src.config import RAW_DIR
    n = 0
    for p in RAW_DIR.glob(f"OR_ABI-L1b-RadF-*_s{dt:%Y%j%H%M}*.nc"):
        try:
            n += p.stat().st_size
            p.unlink()
        except OSError:
            pass
    return n


def etapa_propios(args):
    from src.fetch.gfs_archive import fetch_gfs_profile_archive
    from src.process.acha_plume_height import plume_top_height
    from src.process.bt_matching_height import bt_matching_top_height
    from src.process.wen_rose_height import wen_rose_top_height

    lect = json.loads(F_VOLCAT.read_text(encoding="utf-8"))
    excl = json.loads(F_EXCL.read_text(encoding="utf-8"))
    hechos = _propios()
    salida = (OUT / f"propios_parte{args.parte}.json" if args.partes > 1
              else F_PROPIOS)
    mios = (json.loads(salida.read_text(encoding="utf-8"))
            if salida.exists() else {})
    perfiles = {}

    def perfil(lat, lon, dt):
        # Un GFS por ciclo y volcán: los scans del mismo ciclo comparten perfil.
        c = dt + timedelta(hours=3)          # ciclo de 6 h más cercano
        k = (round(lat, 3), round(lon, 3), c.strftime("%Y%m%d"), c.hour // 6)
        if k not in perfiles:
            perfiles[k] = fetch_gfs_profile_archive(lat, lon, dt)
        return perfiles[k]

    n = 0
    for i, (ev, d, f) in enumerate(_cuadros_a_correr(lect, excl)):
        if args.solo and ev != args.solo:
            continue
        if i % args.partes != args.parte:
            continue
        clave = f"{ev}/{f['cuadro']}"
        if clave in hechos and "error" not in hechos[clave]:
            continue                       # hecho; un error de red se reintenta
        if args.max and n >= args.max:
            break
        libre = shutil.disk_usage(ROOT).free / 1e9
        if libre < args.min_libre_gb:
            print(f"PARO: quedan {libre:.1f} GB libres (< {args.min_libre_gb})")
            break
        v = _volcan(d["volcan"])
        dt = _dt_cuadro(f["cuadro"])
        t0 = time.time()
        res = {}
        try:
            res["bt_matching"] = _resumen(bt_matching_top_height(
                dt, v, radius_deg=RADIO_DEG, profile_fn=perfil), "bt_matching")
            res["wen_rose"] = _resumen(wen_rose_top_height(
                dt, v, radius_deg=RADIO_DEG, summit_km=v.elevation / 1000.0,
                profile_fn=perfil), "wen_rose")
            res["acha"] = _resumen(plume_top_height(dt, v, radius_deg=RADIO_DEG),
                                   "acha")
        except Exception as e:  # se registra y se sigue: un scan no tumba el lote
            res["error"] = f"{type(e).__name__}: {e}"
        bytes_l1b = _limpiar_l1b(dt)
        res["l1b_mb"] = round(bytes_l1b / 1e6, 1)
        res["seg"] = round(time.time() - t0, 1)
        mios[clave] = res
        salida.write_text(json.dumps(mios, indent=1, ensure_ascii=False,
                                     default=str), encoding="utf-8")
        n += 1
        st = {m: (res.get(m) or {}).get("status") for m in ("bt_matching", "wen_rose", "acha")}
        print(f"{clave}: {st} · {res['l1b_mb']} MB L1b · {res['seg']} s · "
              f"libre {shutil.disk_usage(ROOT).free / 1e9:.1f} GB", flush=True)
    print(f"{n} scans nuevos → {salida}")


def _propios() -> dict:
    """Resultados propios de todas las corridas (archivo único o por partes)."""
    out = {}
    for p in sorted(OUT.glob("propios*.json")):
        out.update(json.loads(p.read_text(encoding="utf-8")))
    return out


# ── Criterio (decidido por Nicolás el 16-11-2026, antes de ver números) ──────
def intervalo_propio(r: dict, metodo: str):
    """Nuestro intervalo del tope, o None si el método no da tope.

    Wen-Rose declara su banda β (top_km_lo a top_km_hi). BT-matching y ACHA no
    declaran banda: su intervalo es el punto p95 (intervalo degenerado), así que
    cruzar = el p95 cae dentro del bloque VOLCAT. Declarado antes de correr
    (docs/own_volcat/validacion_magnitud/CRITERIO.md)."""
    if not r or r.get("status") != "ok" or r.get("top_km") is None:
        return None
    if metodo == "wen_rose":
        lo, hi = r.get("top_km_lo"), r.get("top_km_hi")
        if lo is None or hi is None:
            return None
        return min(lo, hi), max(lo, hi)
    return r["top_km"], r["top_km"]


def se_cruzan(a, b) -> bool:
    """Dos intervalos cerrados se cruzan, sin margen."""
    return a[0] <= b[1] and b[0] <= a[1]


def etapa_comparar(_args):
    lect = json.loads(F_VOLCAT.read_text(encoding="utf-8"))
    excl = json.loads(F_EXCL.read_text(encoding="utf-8"))
    hechos = _propios()
    metodos = ("bt_matching", "wen_rose", "acha")
    tabla = {}
    detalle = []
    for ev, d, f in _cuadros_a_correr(lect, excl):
        clave = f"{ev}/{f['cuadro']}"
        if clave not in hechos:
            continue
        caja = f["caja"]
        iv = (caja["top_lo_km"], caja["top_hi_km"])
        fila = {"cuadro": clave, "volcat": iv}
        t = tabla.setdefault(ev, {"scans": 0, **{m: {"tope": 0, "cruza": 0,
                                                    "sobre": 0, "bajo": 0,
                                                    "sin_tope": {}} for m in metodos}})
        t["scans"] += 1
        for m in metodos:
            r = hechos[clave].get(m) or {}
            ip = intervalo_propio(r, m)
            if ip is None:
                motivo = r.get("status") or hechos[clave].get("error", "error")
                t[m]["sin_tope"][motivo] = t[m]["sin_tope"].get(motivo, 0) + 1
                fila[m] = None
                continue
            t[m]["tope"] += 1
            if se_cruzan(iv, ip):
                t[m]["cruza"] += 1
            elif ip[0] > iv[1]:
                t[m]["sobre"] += 1
            else:
                t[m]["bajo"] += 1
            fila[m] = [round(ip[0], 2), round(ip[1], 2)]
        detalle.append(fila)

    nombres = {"bt_matching": "BT-matching", "wen_rose": "Wen-Rose (banda β)",
               "acha": "ACHA ∩ ceniza"}
    lineas = ["| Evento | Scans VOLCAT con tope | Método | Con tope propio | "
              "Se cruzan | Propio sobre | Propio bajo | Sin tope (motivo) |",
              "|---|---|---|---|---|---|---|---|"]
    tot = {m: {"scans": 0, "tope": 0, "cruza": 0} for m in metodos}
    for ev, t in tabla.items():
        for m in metodos:
            x = t[m]
            sin = ", ".join(f"{k}: {v}" for k, v in sorted(x["sin_tope"].items())) or "0"
            lineas.append(f"| {ev} | {t['scans']} | {nombres[m]} | {x['tope']} | "
                          f"{x['cruza']} | {x['sobre']} | {x['bajo']} | {sin} |")
            tot[m]["scans"] += t["scans"]
            tot[m]["tope"] += x["tope"]
            tot[m]["cruza"] += x["cruza"]
    lineas.append("")
    for m in metodos:
        lineas.append(f"- **{nombres[m]}**: {tot[m]['cruza']} de {tot[m]['tope']} scans "
                      f"con tope propio se cruzan con VOLCAT ({tot[m]['scans']} scans "
                      "VOLCAT con tope en total).")
    F_TABLA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (OUT / "detalle.json").write_text(json.dumps(detalle, indent=1), encoding="utf-8")
    print("\n".join(lineas))


def main():
    global RAW
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", type=Path, default=None,
                    help=f"carpeta de cuadros VOLCAT (defecto: {RAW}; también VOLCAT_VALIDACION_RAW)")
    sub = ap.add_subparsers(dest="etapa", required=True)
    sub.add_parser("volcat")
    r = sub.add_parser("recortes")
    r.add_argument("--out", required=True)
    r.add_argument("--lado-km", type=float, default=40.0)
    p = sub.add_parser("propios")
    p.add_argument("--solo")
    p.add_argument("--max", type=int, default=0)
    p.add_argument("--min-libre-gb", type=float, default=8.0)
    p.add_argument("--partes", type=int, default=1,
                   help="procesos en paralelo; cada uno corre un scan de cada N")
    p.add_argument("--parte", type=int, default=0)
    sub.add_parser("comparar")
    a = ap.parse_args()
    if a.raw is not None:
        RAW = a.raw
    {"volcat": etapa_volcat, "recortes": etapa_recortes,
     "propios": etapa_propios, "comparar": etapa_comparar}[a.etapa](a)


if __name__ == "__main__":
    main()
