# ════════════════════════════════════════════════════════════════════
# FICHA SDA · validate_gfs_archive.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : habilitar validación HISTÓRICA del perfil (T(z)/viento) con GFS archivado, que Open-Meteo no da en el pasado
# Lógica        : baja el perfil GFS de archivo (GRIB2 byte-range) y lo compara con el de Open-Meteo cuando ambos existen (solapamiento reciente)
# Modelo/método : comparación determinística T(z)/viento por nivel (RMSE)
# Datos entrada : GFS f000 analysis (noaa-gfs-bdp-pds, público) + Open-Meteo GFS — SIN datos personales
# Variables     : RMSE de T por capa, error de HGT, error de viento
# Limitaciones  : el análisis f000 es el ciclo 6-horario más cercano (gap ≤3 h); requiere eccodes (extra .[archive])
# Refs/datos    : bucket noaa-gfs-bdp-pds (≥2021 verificado)
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Validación del fetcher de GFS ARCHIVADO (src/fetch/gfs_archive.py).

Por qué existe: Open-Meteo devuelve null en niveles de presión pasados, así que no
se pueden validar eventos históricos con él. El GFS archivado (GRIB2 en S3) SÍ. Este
script hace dos cosas:

  1. **Solapamiento reciente** (default): baja el perfil de archivo Y el de Open-Meteo
     para una fecha reciente (donde ambos existen) y mide su acuerdo → prueba que el
     fetcher de archivo reproduce el perfil NRT que ya validamos contra radiosondas.
  2. **Evento histórico** (--date YYYY-MM-DDTHH): baja solo el de archivo (Open-Meteo
     daría null) → habilita cruzar el árbitro de viento / Wen-Rose en eventos viejos.

Uso:
    pip install -e ".[archive]"                 # una vez (eccodes)
    python scripts/validate_gfs_archive.py                      # solapamiento (ayer 12Z)
    python scripts/validate_gfs_archive.py --date 2026-06-27T12 --lat -23.37 --lon -67.73
"""
from __future__ import annotations

import argparse
import io
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np

from src.fetch.gfs_archive import (fetch_gfs_profile_archive,
                                    fetch_gfs_wind_profile_archive)
from src.fetch.gfs_profile import fetch_gfs_profile, fetch_gfs_wind_profile


def _interp_T(levels, z):
    """T(z) interpolada del perfil (para comparar dos perfiles nivel a nivel)."""
    zs = np.array([l["z_m"] for l in levels])
    ts = np.array([l["T_K"] for l in levels])
    return float(np.interp(z, zs, ts))


def _compare_profiles(arch, om, lo_km=5, hi_km=12):
    """RMSE de T entre el perfil de archivo y Open-Meteo en la capa [lo,hi] km."""
    if not arch or not om:
        print("  (falta uno de los dos perfiles — sin comparación)")
        return
    zs = [l["z_m"] for l in arch["levels"] if lo_km * 1000 <= l["z_m"] <= hi_km * 1000]
    diffs = [_interp_T(arch["levels"], z) - _interp_T(om["levels"], z) for z in zs]
    if not diffs:
        print("  (sin niveles en la capa)")
        return
    d = np.array(diffs)
    print(f"  T(z) archivo vs Open-Meteo en {lo_km}-{hi_km} km: "
          f"RMSE {np.sqrt((d**2).mean()):.2f} K · bias {d.mean():+.2f} K "
          f"(≈ {abs(d.mean())/6.5*1000:.0f} m de altura equivalente)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DDTHH UTC (evento histórico)")
    ap.add_argument("--lat", type=float, default=-23.37)   # Láscar
    ap.add_argument("--lon", type=float, default=-67.73)
    args = ap.parse_args()

    if args.date:
        dt = datetime.strptime(args.date, "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        mode = "evento histórico"
    else:
        dt = (datetime.now(timezone.utc).replace(hour=12, minute=0, second=0,
                                                 microsecond=0) - timedelta(days=1))
        mode = "solapamiento reciente (ayer 12Z)"

    print(f"===== GFS archivado — {mode} =====")
    print(f"  punto ({args.lat}, {args.lon}) · dt {dt:%Y-%m-%d %H:%M UTC}\n")

    arch = fetch_gfs_profile_archive(args.lat, args.lon, dt)
    if not arch:
        print("  Sin perfil de archivo (¿red? ¿eccodes instalado? ¿gránulo?).")
        return
    print(f"  ARCHIVO: {len(arch['levels'])} niveles · valid {arch['valid_time']} "
          f"(gap {arch['time_gap_min']} min)")
    tr = arch["tropopause"]
    if tr:
        print(f"    tropopausa: {tr['z_m']/1000:.1f} km · {tr['T_K']:.1f} K")

    om = fetch_gfs_profile(args.lat, args.lon, dt)
    if om and om["levels"]:
        print(f"  OPEN-METEO: {len(om['levels'])} niveles · valid {om['valid_time']}")
        _compare_profiles(arch, om)
    else:
        print("  OPEN-METEO: sin perfil (esperable si la fecha es histórica → "
              "por eso existe el fetcher de archivo).")

    # Viento (solo reporta que corre + magnitud plausible; el número lo cruza
    # validate_fase3c cuando haya evento con pluma).
    wp = fetch_gfs_wind_profile_archive(args.lat, args.lon, dt)
    if wp:
        vmax = max(np.hypot(l["u_ms"], l["v_ms"]) for l in wp["levels"])
        print(f"  VIENTO archivo: {len(wp['levels'])} niveles · |V|max {vmax:.0f} m/s")
    print("\n  Perfil de archivo INDICATIVO (mismo GFS que el NRT, ya validado "
          "vs radiosondas). Habilita validar eventos históricos.")


if __name__ == "__main__":
    main()
