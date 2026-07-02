"""Cross-check en vivo: perfil T(z) del PROPIO GOES-19 (LVTPF) vs GFS (Open-Meteo).

Por qué (geología → pipeline): el mapeo Teff→altura de la pluma depende de un
perfil vertical T(z). GFS (Open-Meteo) ya está validado contra radiosondas (RMSE
0.3–1.1 K en 5–12 km; `scripts/validate_gfs_vs_radiosonde.py`). LVTPF es la MISMA
cantidad física medida por el propio sondeador infrarrojo del ABI. Este script
compara ambos perfiles en varios volcanes chilenos: si concuerdan al nivel al que
GFS concuerda con la radiosonda, la altura queda doblemente respaldada; donde
divergen, es incertidumbre honesta (típicamente ≥12 km, ya marcado no fiable).

Compara: tropopausa (punto frío), T(z) en la banda fiable 5–12 km (RMSE/bias), y
el mapeo Tc→altura para BTs representativas del tope de pluma.

Uso:
    python scripts/compare_lvtp_vs_gfs.py
    python scripts/compare_lvtp_vs_gfs.py --volcan Villarrica
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np

# Unicode seguro en consola Windows (cp1252 rompe con Δ/°).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fetch.goes_lvtp import fetch_lvtp_profile           # noqa: E402
from src.fetch.gfs_profile import (                          # noqa: E402
    fetch_gfs_profile, altitudes_from_bt, _monotone_tropo_branch)

# (nombre, lat, lon) — un muestreo N→S de la zona volcánica chilena.
VOLCANOS = [
    ("Lascar",              -23.37, -67.73),
    ("Nevados de Chillan",  -36.86, -71.38),
    ("Villarrica",          -39.42, -71.93),
    ("Calbuco",             -41.33, -72.61),
]

BAND_Z = np.arange(5000.0, 12001.0, 1000.0)   # banda fiable 5–12 km
BTS = [230.0, 220.0, 215.0]                     # BTs típicas de tope de pluma


def _z_t(profile: dict) -> tuple[np.ndarray, np.ndarray]:
    """Rama monótona (z asc, T dec) del perfil, para interpolar."""
    kept = _monotone_tropo_branch(profile)
    return (np.array([l["z_m"] for l in kept]),
            np.array([l["T_K"] for l in kept]))


def compare_one(name: str, lat: float, lon: float) -> dict | None:
    print(f"\n===== {name} ({lat}, {lon}) =====")
    lv = fetch_lvtp_profile(lat, lon)
    gf = fetch_gfs_profile(lat, lon)
    if lv is None:
        print("  LVTPF: None (sin gránulo o sin cielo claro suficiente)")
        return None
    if gf is None:
        print("  GFS: None")
        return None
    print(f"  LVTPF  n_clear={lv['n_clear_px']}  niveles={len(lv['levels'])}  "
          f"valid={lv['valid_time']}")
    print(f"  GFS    niveles={len(gf['levels'])}  valid={gf['valid_time']}  "
          f"gap={gf.get('time_gap_min')} min")

    tl, tg = lv["tropopause"], gf["tropopause"]
    print(f"  Tropopausa   LVTPF {tl['z_m']/1000:5.2f} km / {tl['T_K']:.1f} K"
          f"    GFS {tg['z_m']/1000:5.2f} km / {tg['T_K']:.1f} K")

    Zl, Tl = _z_t(lv)
    Zg, Tg = _z_t(gf)
    dT = np.interp(BAND_Z, Zl, Tl) - np.interp(BAND_Z, Zg, Tg)
    rmse = float(np.sqrt(np.mean(dT ** 2)))
    bias = float(np.mean(dT))
    print(f"  ΔT(LVTPF−GFS) 5–12 km (K): {np.round(dT, 1)}")
    print(f"  RMSE T = {rmse:.2f} K   bias = {bias:+.2f} K")

    for bt in BTS:
        zl = float(altitudes_from_bt(np.array([bt]), lv)[0]) / 1000.0
        zg = float(altitudes_from_bt(np.array([bt]), gf)[0]) / 1000.0
        print(f"    BT={bt:.0f} K → LVTPF {zl:5.2f} km | GFS {zg:5.2f} km | "
              f"Δ={zl - zg:+.2f} km")
    return {"name": name, "rmse": rmse, "bias": bias}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--volcan", help="nombre exacto de un volcán de la lista")
    args = ap.parse_args()

    targets = VOLCANOS
    if args.volcan:
        targets = [v for v in VOLCANOS if v[0].lower() == args.volcan.lower()]
        if not targets:
            raise SystemExit(f"volcán no en la lista: {args.volcan}")

    results = [r for v in targets if (r := compare_one(*v))]
    if len(results) > 1:
        rmse = np.mean([r["rmse"] for r in results])
        bias = np.mean([r["bias"] for r in results])
        print(f"\n=== Resumen ({len(results)} volcanes) ===")
        print(f"  RMSE T 5–12 km medio = {rmse:.2f} K   bias medio = {bias:+.2f} K")
        print("  (comparar contra GFS-vs-radiosonda: RMSE 0.3–1.1 K)")


if __name__ == "__main__":
    main()
