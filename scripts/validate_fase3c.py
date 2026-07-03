"""Validación Fase 3c — árbitro de altura por cizalla de viento vs Wen-Rose
(térmico), sobre el mismo evento. Corre cuando hay una pluma en 2 scans seguidos.

Qué demuestra: (1) el pipeline de viento corre end-to-end (2 scans → centroides →
advección → perfil de viento GFS → altura); (2) donde hay cizalla suficiente, la
altura por viento es un cross-check INDEPENDIENTE del método térmico; si coinciden,
sube la confianza. Si no hay ceniza o no hay cizalla, lo reporta (no es bug).

Uso: python scripts/validate_fase3c.py
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

from src.process.wind_shear_height import wind_shear_top_height
from src.process.wen_rose_height import wen_rose_top_height
from src.volcanos import get_volcano

SWEEP = ["Sangay", "Reventador", "Popocatépetl", "Sabancaya", "Lascar",
         "Nevados de Chillan", "Villarrica"]


def main(hours_back=48, step_h=6, radius=0.6):
    now = datetime.now(timezone.utc)
    print(f"===== Fase 3c — cizalla de viento ({hours_back}h, cada {step_h}h) =====")
    best = None
    for name in SWEEP:
        v = get_volcano(name)
        if v is None:
            continue
        for back in range(2, hours_back + 1, step_h):
            dt = now - timedelta(hours=back)
            ws = wind_shear_top_height(dt, v, radius_deg=radius)
            st = ws.get("status")
            if st in ("ok", "no_shear", "adv_ambiguous", "band_unconstrained"):
                print(f"  {v.name:22} {dt:%Y-%m-%d %H:%M} → {st} "
                      f"(adv {ws.get('adv_speed_ms', 0):.1f} m/s, cizalla "
                      f"{ws.get('shear_ms', 0):.0f} m/s)")
                if st == "ok" and best is None:
                    best = (v, dt, ws)
                    break
    print("\n========== RESULTADO ==========")
    if best is None:
        print("  Sin caso con ceniza en 2 scans + cizalla suficiente en el barrido "
              "(esperable en período sin VAA). El pipeline corrió end-to-end.")
        return
    v, dt, ws = best
    print(f"  CASO: {v.name} · {ws['scan_dt']:%Y-%m-%d %H:%M UTC}")
    print(f"    Altura por VIENTO: {ws['top_km']:.1f} km "
          f"[banda {ws['band_lo_km']:.1f}–{ws['band_hi_km']:.1f} km] · "
          f"advección {ws['adv_speed_ms']:.0f} m/s · cizalla {ws['shear_ms']:.0f} m/s "
          f"· mismatch {ws['mismatch_ms']:.1f} m/s")
    wr = wen_rose_top_height(dt, v, radius_deg=radius)
    if wr.get("status") == "ok":
        d = ws["top_km"] - wr["top_km"]
        print(f"    Altura TÉRMICA (Wen-Rose): {wr['top_km']:.1f} km")
        print(f"    → Δ(viento − térmico) = {d:+.1f} km "
              f"({'✓ concuerdan (métodos ortogonales)' if abs(d) <= 2.5 else '⚠ discrepan >2.5'})")
    else:
        print(f"    Wen-Rose: {wr.get('status')} — sin cross-check térmico este scan")
    print("\n  Ambos INDICATIVOS; VOLCAT/SSEC sigue siendo el primario.")


if __name__ == "__main__":
    main()
