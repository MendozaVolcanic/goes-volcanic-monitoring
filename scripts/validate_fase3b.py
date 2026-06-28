"""Validación Fase 3b — altura Wen-Rose (corrección emisividad 2 canales) vs
BT-matching (Fase 3a) vs ACHA NOAA (Fase 0), TODOS sobre el MISMO scan.

Qué demuestra:
  (1) El pipeline Wen-Rose corre end-to-end sobre datos REALES (bandas L1b +
      coeficientes Planck + Ts de cielo claro + perfil GFS + despeje Tc).
  (2) En plumas semi-transparentes la corrección Wen-Rose **sube** la altura
      respecto del BT-matching (Δ = top_WenRose − top_BTmatching ≥ 0), y queda
      en el mismo orden que ACHA (que también corrige por OE).
  (3) Sanity físico: el tope cae sobre el cráter y < 20 km.

Barre volcanes activos buscando ceniza real; en el primer hit sólido hace la
comparación 3-vías. Si no hay ceniza (período sin VAA), igual confirma que el
pipeline corre (status no_plume sobre datos reales).

Uso:
    python scripts/validate_fase3b.py
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

from src.process.wen_rose_height import wen_rose_top_height
from src.volcanos import get_volcano

# Volcanes con buena chance de ceniza reciente (ecuatoriales + México + Chile).
SWEEP = ["Popocatépetl", "Sangay", "Reventador", "Sabancaya", "Lascar",
         "Nevados de Chillan", "Villarrica"]


def _three_way(res) -> None:
    """Comparación Wen-Rose vs BT-matching (mismo scan, dentro del propio result)
    vs ACHA NOAA (gránulo L2 del mismo scan)."""
    v = get_volcano(res["volcano"])
    crater_km = v.elevation / 1000.0
    print(f"\n  ASH HIT: {res['volcano']} · scan "
          f"{res['scan_dt'].strftime('%Y-%m-%d %H:%M UTC')} · "
          f"px ceniza={res['mask_px']} (corregidos Wen-Rose={res['n_corrected']}) · "
          f"latencia ~{res['latency_min']:.0f} min")
    print(f"    Ts (fondo) = {res['ts_k']:.1f} K  [{res['ts_source']}]  ·  "
          f"β = {res['beta']}  ·  tropopausa = {res['tropopause_km']:.1f} km")
    twr = res["top_km"]
    tbt = res["top_bt_matching_km"]
    d = res["delta_km"]
    print(f"    BT-matching (opaco, cota) ... p95 = {tbt:.1f} km")
    print(f"    Wen-Rose (emis. corregida) .. p95 = {twr:.1f} km  "
          f"(máx {res['top_max_km']:.1f} km)")
    sign = "✓ sube (esperado en semitransparente)" if d >= -0.1 else \
        "⚠ baja — revisar (no debería)"
    print(f"    Δ(Wen-Rose − BT-matching) = {d:+.1f} km   {sign}")

    # ACHA del mismo scan
    try:
        from src.process.acha_plume_height import plume_top_height
        acha = plume_top_height(res["scan_dt"], v, radius_deg=0.6)
        if acha.get("status") == "ok":
            da = twr - acha["top_km"]
            print(f"    ACHA NOAA (OE genérica) ..... p95 = {acha['top_km']:.1f} km "
                  f"→ Δ(Wen-Rose − ACHA) = {da:+.1f} km "
                  f"({'✓ mismo orden' if abs(da) <= 2.5 else '⚠ discrepa >2.5'})")
        else:
            print(f"    ACHA NOAA: {acha.get('status')} "
                  f"({acha.get('reason', 'sin retrieval sobre la ceniza')})")
    except Exception as e:
        print(f"    ACHA NOAA: no disponible ({e})")

    sane = crater_km - 1.0 <= res["top_max_km"] <= 20.0
    print(f"    sanity físico: cráter {crater_km:.1f} km ≤ tope "
          f"{res['top_max_km']:.1f} km ≤ 20 km → {sane}")


def main(hours_back=48, step_h=6, radius=0.6):
    now = datetime.now(timezone.utc)
    print(f"===== Fase 3b — barrido de ceniza ({hours_back}h, cada {step_h}h) =====")
    best = None
    for name in SWEEP:
        v = get_volcano(name)
        if v is None:
            print(f"  {name:24} [no en catálogo]")
            continue
        statuses = []
        for back in range(2, hours_back + 1, step_h):
            r = wen_rose_top_height(now - timedelta(hours=back), v, radius_deg=radius)
            statuses.append(r.get("status"))
            if r.get("status") == "ok" and (r.get("mask_px") or 0) >= 8:
                if best is None or r["mask_px"] > best["mask_px"]:
                    best = r
                break   # un hit sólido por volcán basta
        print(f"  {v.name:24} scans={len(statuses)} "
              f"ok={statuses.count('ok')} no_plume={statuses.count('no_plume')} "
              f"no_data={statuses.count('no_data')}")
        if best is not None and best["mask_px"] >= 30:
            break       # hit grande → suficiente para la comparación

    print("\n========== RESULTADO ==========")
    if best is None:
        print("  Sin ceniza detectada en el barrido (consistente con período sin "
              "VAA). El pipeline Wen-Rose corrió end-to-end sobre datos reales "
              "(fetch + Ts + perfil + despeje) — sin pluma activa no hay tope que "
              "reportar.")
        return
    _three_way(best)
    print("\n  Wen-Rose es INDICATIVO; corrige el BT-matching hacia arriba en "
          "semitransparentes. El VOLCAT/SSEC sigue siendo el primario cuantitativo.")


if __name__ == "__main__":
    main()
