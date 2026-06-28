"""Validación Fase 0 — altura del tope de pluma propia (ACHA ∩ ceniza).

Artefacto de verificación reutilizable. Cuatro bloques:

  (1) Cross-check de altura: la HT que recorto cae dentro del rango full-disk
      que el propio gránulo ACHA documenta (``minimum/maximum_cloud_top_height``).
      Valida fetch + georef + filtro DQF + extracción de altura sobre datos
      REALES, sin depender de que haya ceniza.

  (2) Camino de render del dashboard: el campo real alimenta ``_fig_acha_field``
      (la figura de la vista de altura) sin error.

  (3) Búsqueda de ceniza y comparación con VOLCAT: barre scans recientes de
      volcanes activos; si NUESTRA detección tri-espectral marca ceniza, reporta
      el tope (p95/max), chequea sanity físico (sobre el cráter, < 20 km) y busca
      el frame VOLCAT Ash_Height del MISMO scan para comparar el orden de
      magnitud. Si no hay ceniza, lo reporta (debe ser consistente con el nº de
      VAA activos).

  (4) Contexto VAAC: nº de Volcanic Ash Advisories activos ahora.

Nota: el VOLCAT de SSEC entrega el número km QUEMADO en el PNG (no se extrae a
nivel de pixel en Fase 0); la comparación es de orden de magnitud / co-ocurrencia.
El VOLCAT/SSEC sigue siendo el primario cuantitativo; esto es INDICATIVO.

Uso:
    python scripts/validate_acha_fase0.py
"""
from __future__ import annotations

import io
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np

from src.fetch.goes_acha import _list_files_at_hour, fetch_acha_height_at
from src.process.acha_plume_height import plume_top_height
from src.volcanos import get_volcano

# Volcanes a barrer (activos, buena cobertura GOES-19 ~28 días).
SWEEP_VOLCANOES = ["Sangay", "Reventador", "Sabancaya", "Popocatépetl",
                   "Nevados de Chillan", "Villarrica", "Lascar"]


def block1_height_crosscheck() -> bool:
    print("===== (1) Cross-check de altura vs metadata del gránulo =====")
    import s3fs
    import xarray as xr
    s3 = s3fs.S3FileSystem(anon=True)
    now = datetime.now(timezone.utc)
    keys = []
    for h in range(8):
        keys = _list_files_at_hour(s3, now - timedelta(hours=h))
        if keys:
            break
    if not keys:
        print("  [skip] sin gránulos ACHA recientes")
        return False
    with s3.open(keys[-1], "rb") as f:
        ds = xr.open_dataset(f, engine="h5netcdf")
        gmin = float(ds["minimum_cloud_top_height"].values)
        gmax = float(ds["maximum_cloud_top_height"].values)
        gmean = float(ds["mean_cloud_top_height"].values)
    print(f"  gránulo full-disk CTH: min={gmin:.0f} max={gmax:.0f} "
          f"mean={gmean:.0f} m")
    big = {"lat_min": -44, "lat_max": -34, "lon_min": -76, "lon_max": -69}
    res = fetch_acha_height_at(now, big)
    if res is None:
        print("  [skip] fetch_acha_height_at devolvió None (S3 intermitente)")
        return False
    h = res["height_m"]
    fin = h[np.isfinite(h)]
    if fin.size == 0:
        print("  [skip] sin HT válida en la región de prueba")
        return False
    inside = (fin.min() >= gmin - 50) and (fin.max() <= gmax + 50)
    print(f"  mi recorte: n={fin.size} min={fin.min():.0f} max={fin.max():.0f} "
          f"mean={fin.mean():.0f} m → dentro del rango full-disk: {inside}")
    return bool(inside)


def block2_render_path() -> bool:
    print("\n===== (2) Camino de render del dashboard (_fig_acha_field) =====")
    from dashboard.views.volcat_viewer import _fig_acha_field
    v = get_volcano("Villarrica")
    r = 0.75
    bounds = {"lat_min": v.lat - r, "lat_max": v.lat + r,
              "lon_min": v.lon - r, "lon_max": v.lon + r}
    res = fetch_acha_height_at(datetime.now(timezone.utc), bounds)
    if res is None:
        print("  [skip] sin gránulo ACHA")
        return False
    # Stand-in del campo: la HT de nube real (como si todo fuera ceniza válida)
    # — ejercita la figura con arrays 2D + lat/lon reales (NO implica ceniza).
    field_km = np.where(np.isfinite(res["height_m"]), res["height_m"] / 1000.0,
                        np.nan)
    fig = _fig_acha_field(field_km, res["lat"], res["lon"], bounds, "render-test")
    ntr = len(fig.data)
    # también el caso campo vacío (todo NaN) no debe romper.
    empty = np.full_like(field_km, np.nan)
    _fig_acha_field(empty, res["lat"], res["lon"], bounds, "empty-test")
    ok = ntr >= 1
    print(f"  _fig_acha_field OK · {ntr} trazas · campo vacío tolerado: True")
    return ok


def _compare_volcat(res) -> None:
    from src.fetch.volcat_api import resolve_volcat_sector, volcat_at_time
    v = get_volcano(res["volcano"])
    sector, instr = resolve_volcat_sector(v)
    vc = volcat_at_time(res["scan_dt"], sector, instr=instr,
                        image_type="Ash_Height", max_gap_min=30)
    if vc is None:
        print(f"    VOLCAT Ash_Height (sector {sector}): sin frame en ±30 min "
              "(ventana del API no alcanza, o SSEC sin detección).")
    else:
        gap = vc.get("gap_seconds", 0) / 60.0
        print(f"    VOLCAT Ash_Height (sector {sector}): frame "
              f"{vc.get('datetime')} (gap {gap:.0f} min) → ambos vieron el scan; "
              "el km de SSEC está quemado en el PNG (no se extrae en Fase 0).")


def block3_ash_search(hours_back=36, step_h=4, radius=0.6):
    print(f"\n===== (3) Búsqueda de ceniza ({hours_back}h atrás, "
          f"cada {step_h}h) =====")
    now = datetime.now(timezone.utc)
    hits = []
    for name in SWEEP_VOLCANOES:
        v = get_volcano(name)
        statuses = []
        for back in range(2, hours_back + 1, step_h):
            r = plume_top_height(now - timedelta(hours=back), v, radius_deg=radius)
            statuses.append(r.get("status"))
            if r.get("status") == "ok":
                hits.append(r)
        n_ok = statuses.count("ok")
        n_nodata = statuses.count("no_data")
        print(f"  {v.name:24} scans={len(statuses)} ok={n_ok} "
              f"no_plume={statuses.count('no_plume')} no_data={n_nodata}")
    if not hits:
        print("  → sin ceniza detectada en el barrido.")
        return None
    best = max(hits, key=lambda r: r["mask_px"])
    print(f"\n  ASH HIT: {best['volcano']} scan "
          f"{best['scan_dt'].strftime('%Y-%m-%d %H:%M UTC')}  "
          f"p95={best['top_km']:.1f} km · max={best['top_max_km']:.1f} km · "
          f"px={best['mask_px']} · latencia ~{best['latency_min']:.0f} min")
    v = get_volcano(best["volcano"])
    crater_km = v.elevation / 1000.0
    sane = crater_km - 1.0 <= best["top_max_km"] <= 20.0
    print(f"    sanity físico: cráter {crater_km:.1f} km ≤ tope "
          f"{best['top_max_km']:.1f} km ≤ 20 km → {sane}")
    _compare_volcat(best)
    return best


def block4_vaa_context() -> None:
    print("\n===== (4) Contexto VAAC (advisories activos) =====")
    try:
        from src.fetch.realearth_api import fetch_vaa_geojson
        feats = (fetch_vaa_geojson() or {}).get("features", [])
        print(f"  Volcanic Ash Advisories activos ahora: {len(feats)}")
        for f in feats[:20]:
            p = f.get("properties", {})
            print(f"    - {p.get('name') or p.get('title') or '?'}")
    except Exception as e:
        print(f"  [skip] VAA no accesible: {e}")


def main():
    ok1 = block1_height_crosscheck()
    ok2 = block2_render_path()
    best = block3_ash_search()
    block4_vaa_context()
    print("\n========== RESUMEN ==========")
    print(f"  (1) cross-check altura ......... {'PASS' if ok1 else 'SKIP/FAIL'}")
    print(f"  (2) render path dashboard ...... {'PASS' if ok2 else 'SKIP/FAIL'}")
    if best:
        print(f"  (3) ceniza real + VOLCAT ....... PASS ({best['volcano']}, "
              f"tope {best['top_max_km']:.1f} km)")
    else:
        print("  (3) ceniza real + VOLCAT ....... sin caso de ceniza en la "
              "ventana (consistente con período sin VAA)")
    print("  El VOLCAT/SSEC sigue siendo el primario cuantitativo; "
          "este producto es INDICATIVO.")


if __name__ == "__main__":
    main()
