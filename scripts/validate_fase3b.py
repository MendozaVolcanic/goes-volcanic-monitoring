"""Validación Fase 3b — altura Wen-Rose (corrección emisividad) vs BT-matching
(Fase 3a) vs ACHA NOAA (Fase 0) vs VOLCAT SSEC, TODOS sobre el MISMO scan.

Qué demuestra:
  (1) El pipeline Wen-Rose corre end-to-end sobre datos REALES (bandas L1b +
      coeficientes Planck + Ts de cielo claro + perfil GFS + despeje Tc).
  (2) En plumas semi-transparentes la corrección Wen-Rose **sube** la altura
      respecto del BT-matching (Δ ≥ 0), y queda en el mismo orden que ACHA.
  (3) **Triangulación de ground truth**: prioriza un caso donde los TRES métodos
      independientes (ACHA OE de NOAA, BT-matching, Wen-Rose) disparen → si
      coinciden, sube la confianza en el NÚMERO (no solo en el comportamiento).
      Además cruza con VOLCAT Ash_Height de SSEC (co-ocurrencia del mismo scan).
  (4) Reporta la **banda de incertidumbre β** y la **confianza INDICATIVA** —
      para que el número no se lea como exacto.

Honestidad: Wen-Rose y BT-matching son cotas/correcciones INDICATIVAS; el
cuantitativo validado sigue siendo VOLCAT. Una pluma de gas/SO₂ (sin ceniza
silicatada) da `no_plume` en los tres métodos — es correcto, no un bug.

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

# Volcanes con chance de ceniza reciente. Los ecuatoriales/México suelen tener
# plumas más densas → mejor chance de que ACHA (OE de NOAA) también dispare.
SWEEP = ["Sangay", "Reventador", "Popocatépetl", "Sabancaya", "Lascar",
         "Nevados de Chillan", "Villarrica"]


def _acha_top(scan_dt, v):
    """Tope ACHA del mismo scan (None si no dispara)."""
    try:
        from src.process.acha_plume_height import plume_top_height
        a = plume_top_height(scan_dt, v, radius_deg=0.6)
        return a["top_km"] if a.get("status") == "ok" else None
    except Exception:
        return None


def _volcat_cooccur(scan_dt, v) -> str:
    """¿VOLCAT SSEC tiene un frame Ash_Height del mismo scan? (co-ocurrencia; el
    km de SSEC está quemado en el PNG, no se extrae a nivel de píxel)."""
    try:
        from src.fetch.volcat_api import resolve_volcat_sector, volcat_at_time
        sector, instr = resolve_volcat_sector(v)
        vc = volcat_at_time(scan_dt, sector, instr=instr,
                            image_type="Ash_Height", max_gap_min=30)
        if vc is None:
            return "VOLCAT: sin frame en ±30 min"
        gap = vc.get("gap_seconds", 0) / 60.0
        return f"VOLCAT: frame {vc.get('datetime')} (gap {gap:.0f} min) — co-ocurre"
    except Exception as e:
        return f"VOLCAT: no accesible ({e})"


def _report(res) -> None:
    v = get_volcano(res["volcano"])
    crater_km = v.elevation / 1000.0
    acha_top = res.get("_acha_top")
    print(f"\n  CASO: {res['volcano']} · scan "
          f"{res['scan_dt'].strftime('%Y-%m-%d %H:%M UTC')} · "
          f"px ceniza={res['mask_px']} (corregidos={res['n_corrected']}, "
          f"claros={res['n_clear']}) · latencia ~{res['latency_min']:.0f} min")
    print(f"    Ts (fondo) = {res['ts_k']:.1f} K [{res['ts_source']}] · "
          f"β={res['beta']} · tropopausa = {res['tropopause_km']:.1f} km")
    print(f"    BT-matching (cota opaca) ...... p95 = {res['top_bt_matching_km']:.1f} km")
    print(f"    Wen-Rose (emis. corregida) .... p95 = {res['top_km']:.1f} km  "
          f"[banda β {res['top_km_lo']:.1f}–{res['top_km_hi']:.1f} km, "
          f"máx {res['top_max_km']:.1f}]")
    d = res["delta_km"]
    sign = "✓ sube (esperado)" if d >= -0.1 else "⚠ baja (revisar)"
    print(f"    Δ(Wen-Rose − BT-matching) = {d:+.1f} km   {sign}")
    co2 = res.get("co2_semitransp_btd")
    if co2 is not None:
        verdict = ("✓ confirma semi-transparencia (corrección real)" if co2 >= 0.5
                   else "⚠ sugiere pluma ~opaca (corrección sospechosa)")
        print(f"    CO₂ 13.3µm (árbitro indep.): BTD(11−13.3) = {co2:+.1f} K → {verdict}")
    if acha_top is not None:
        da = res["top_km"] - acha_top
        print(f"    ACHA NOAA (OE genérica) ....... p95 = {acha_top:.1f} km  "
              f"→ TRIANGULACIÓN 3 métodos: Δ(WenRose−ACHA) = {da:+.1f} km "
              f"({'✓ coinciden' if abs(da) <= 2.5 else '⚠ discrepan >2.5'})")
    else:
        print("    ACHA NOAA ..................... no_plume (sin retrieval; "
              "Wen-Rose/BT rescatan el caso, pero sin 3ª fuente para triangular)")
    print(f"    {_volcat_cooccur(res['scan_dt'], v)}")
    print(f"    CONFIANZA (indicativa): {res['confidence'].upper()}"
          + (f"  ⚠ {' · '.join(res['flags'])}" if res.get("flags") else ""))
    sane = crater_km - 1.0 <= res["top_max_km"] <= 20.0
    print(f"    sanity físico: cráter {crater_km:.1f} ≤ tope "
          f"{res['top_max_km']:.1f} ≤ 20 km → {sane}")


def main(hours_back=48, step_h=6, radius=0.6):
    now = datetime.now(timezone.utc)
    print(f"===== Fase 3b — barrido de ceniza ({hours_back}h, cada {step_h}h) =====")
    hits = []
    for name in SWEEP:
        v = get_volcano(name)
        if v is None:
            print(f"  {name:24} [no en catálogo]")
            continue
        statuses = []
        got = False
        for back in range(2, hours_back + 1, step_h):
            r = wen_rose_top_height(now - timedelta(hours=back), v, radius_deg=radius)
            statuses.append(r.get("status"))
            if r.get("status") == "ok" and (r.get("mask_px") or 0) >= 5 and not got:
                r["_acha_top"] = _acha_top(r["scan_dt"], v)  # ¿3ª fuente?
                hits.append(r)
                got = True   # un hit por volcán basta para el barrido
        print(f"  {v.name:24} scans={len(statuses)} "
              f"ok={statuses.count('ok')} no_plume={statuses.count('no_plume')} "
              f"no_data={statuses.count('no_data')}")

    print("\n========== RESULTADO ==========")
    if not hits:
        print("  Sin ceniza detectada (consistente con período sin VAA). El pipeline "
              "Wen-Rose corrió end-to-end sobre datos reales; sin pluma de ceniza "
              "no hay tope que reportar. Una pluma de gas/SO₂ NO cuenta (transparente "
              "en 11 µm → no_plume correcto).")
        return
    # Ranking: priorizar un caso con ACHA (triangulación 3-vías), luego mask_px.
    hits.sort(key=lambda r: (r.get("_acha_top") is not None, r["mask_px"]),
              reverse=True)
    best = hits[0]
    n_3way = sum(1 for h in hits if h.get("_acha_top") is not None)
    print(f"  {len(hits)} caso(s) con ceniza · {n_3way} con ACHA disparando "
          f"(triangulación 3-vías posible)")
    _report(best)
    if best.get("_acha_top") is None and n_3way == 0:
        print("\n  NOTA: ningún caso del barrido tuvo ACHA con retrieval → se valida "
              "el COMPORTAMIENTO (Wen-Rose sube sobre BT-matching), no el número "
              "absoluto. Para validar magnitud hace falta un caso con 3ª fuente "
              "(ACHA/VOLCAT numérico/VAAC) — pendiente de pluma más densa.")
    print("\n  Wen-Rose es INDICATIVO; el VOLCAT/SSEC sigue siendo el primario "
          "cuantitativo.")


if __name__ == "__main__":
    main()
