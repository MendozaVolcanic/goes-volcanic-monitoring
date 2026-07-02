# ════════════════════════════════════════════════════════════════════
# FICHA SDA · validate_gfs_vs_radiosonde.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : validar el perfil GFS (el eslabón más débil de la altura propia) contra radiosondas REALES
# Lógica        : compara T(z) y viento del GFS que usamos vs el sondeo medido más cercano (U. Wyoming)
# Modelo/método : comparación determinística (interpolación + RMSE por capas)
# Datos entrada : radiosondas U. Wyoming (públicas) + perfil GFS Open-Meteo — SIN datos personales
# Variables     : RMSE de T por capa, error de altura equivalente, error de viento
# Limitaciones  : sondeos 12Z (1-2/día); estaciones a decenas-cientos de km del volcán
# Refs/datos    : weather.uwyo.edu (endpoint NUEVO /wsgi/; el /cgi-bin/ viejo da 404)
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Validación del perfil GFS contra radiosondas (Ola 6 del audit jul-2026).

Por qué (geología → pipeline): toda la cadena de altura propia convierte una
temperatura de tope a kilómetros BUSCÁNDOLA en el perfil GFS T(z). Si el GFS
está corrido 2 K en la troposfera media, la altura se corre ~300-400 m. Este
script mide ese error contra la única verdad MEDIDA disponible: las radiosondas
operativas (12Z) de las estaciones chilenas/argentinas cercanas a los volcanes.

Uso:
    python scripts/validate_gfs_vs_radiosonde.py [YYYY-MM-DD]
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
import requests

# Estaciones WMO con sondeo operativo cerca de volcanes monitoreados.
STATIONS = {
    "85799": ("Puerto Montt (SCTE)", -41.43, -73.10, "Calbuco/Osorno/Villarrica"),
    "85442": ("Antofagasta (SCFA)", -23.45, -70.44, "Láscar/Lastarria"),
    "85586": ("Sto Domingo (SCSN)", -33.65, -71.61, "Tupungatito/San José"),
    "85934": ("Punta Arenas (SCCI)", -53.00, -70.85, "zona austral"),
}
WYO = "https://weather.uwyo.edu/wsgi/sounding"


def fetch_sounding(station: str, dt: datetime):
    """Sondeo Wyoming (endpoint /wsgi/, formato TEXT:LIST) → lista de niveles
    {p_hPa, z_m, T_K, wind_dir, wind_kt}. None si no hay sondeo."""
    params = {"datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
              "id": station, "type": "TEXT:LIST"}
    try:
        r = requests.get(WYO, params=params, timeout=30)
        r.raise_for_status()
        text = r.text
    except Exception as e:
        print(f"    [!] Wyoming {station}: {e}")
        return None
    levels = []
    for line in text.splitlines():
        parts = line.split()
        # filas de datos: PRES HGHT TEMP DWPT RELH MIXR DRCT SKNT ...
        if len(parts) >= 8:
            try:
                p, z, t = float(parts[0]), float(parts[1]), float(parts[2])
                drct, sknt = float(parts[6]), float(parts[7])
            except ValueError:
                continue
            if 20.0 <= p <= 1050.0 and -120.0 < t < 60.0:
                levels.append({"p_hPa": p, "z_m": z, "T_K": t + 273.15,
                               "wind_dir": drct, "wind_ms": sknt * 0.514444})
    return levels or None


def compare_station(station: str, dt: datetime) -> None:
    name, lat, lon, volcs = STATIONS[station]
    print(f"\n── {name} · {volcs} · sondeo {dt:%Y-%m-%d %HZ} ──")
    snd = fetch_sounding(station, dt)
    if snd is None:
        print("    sin sondeo disponible (la estación no siempre lanza)")
        return
    from src.fetch.gfs_profile import fetch_gfs_profile, fetch_gfs_wind_profile
    gfs = fetch_gfs_profile(lat, lon, dt)
    if gfs is None:
        print("    sin perfil GFS (Open-Meteo)")
        return
    gz = np.array([l["z_m"] for l in gfs["levels"]])
    gt = np.array([l["T_K"] for l in gfs["levels"]])
    # comparar en las alturas del SONDEO dentro del rango GFS, por capas
    layers = [(0, 5000, "0-5 km"), (5000, 12000, "5-12 km (banda de alturas)"),
              (12000, 20000, "12-20 km")]
    print(f"    niveles sondeo: {len(snd)} · niveles GFS: {len(gz)}")
    for z0, z1, lbl in layers:
        pts = [l for l in snd if z0 <= l["z_m"] <= z1
               and gz.min() <= l["z_m"] <= gz.max()]
        if len(pts) < 3:
            continue
        sz = np.array([l["z_m"] for l in pts])
        st = np.array([l["T_K"] for l in pts])
        gt_i = np.interp(sz, gz, gt)
        rmse = float(np.sqrt(np.mean((gt_i - st) ** 2)))
        bias = float(np.mean(gt_i - st))
        # error de altura equivalente con lapse ~6.5 K/km
        dz_m = abs(bias) / 6.5 * 1000.0
        print(f"    T(z) {lbl:28} RMSE={rmse:4.1f} K · bias={bias:+4.1f} K "
              f"(≈ {dz_m:3.0f} m de error de altura)")
    # viento (si el perfil de viento GFS responde)
    wp = fetch_gfs_wind_profile(lat, lon, dt)
    if wp:
        wz = np.array([l["z_m"] for l in wp["levels"]])
        wu = np.array([l["u_ms"] for l in wp["levels"]])
        wv = np.array([l["v_ms"] for l in wp["levels"]])
        pts = [l for l in snd if 1000 <= l["z_m"] <= 15000
               and wz.min() <= l["z_m"] <= wz.max() and l["wind_ms"] > 0]
        if len(pts) >= 3:
            sz = np.array([l["z_m"] for l in pts])
            su = -np.array([l["wind_ms"] for l in pts]) * \
                np.sin(np.radians([l["wind_dir"] for l in pts]))
            sv = -np.array([l["wind_ms"] for l in pts]) * \
                np.cos(np.radians([l["wind_dir"] for l in pts]))
            du = np.interp(sz, wz, wu) - su
            dv = np.interp(sz, wz, wv) - sv
            rmse_w = float(np.sqrt(np.mean(du ** 2 + dv ** 2)))
            print(f"    viento 1-15 km ({len(pts)} niveles)    RMSE vect={rmse_w:4.1f} m/s "
                  f"(relevante para el árbitro de cizalla)")


def main():
    if len(sys.argv) > 1:
        day = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # el 12Z de ayer siempre existe; el de hoy puede no estar aún
        day = datetime.now(timezone.utc) - timedelta(days=1)
    dt = day.replace(hour=12, minute=0, second=0, microsecond=0)
    print(f"===== GFS (Open-Meteo) vs radiosondas — {dt:%Y-%m-%d 12Z} =====")
    print("(el GFS es el eslabón que convierte Tc→altura en TODA la cadena propia)")
    for st in STATIONS:
        compare_station(st, dt)
    print("\nInterpretación: bias de T de ±1 K ≈ ±150 m de altura; RMSE ≤ 2 K en "
          "5-12 km valida el mapeo Tc→altura para un producto INDICATIVO.")


if __name__ == "__main__":
    main()
