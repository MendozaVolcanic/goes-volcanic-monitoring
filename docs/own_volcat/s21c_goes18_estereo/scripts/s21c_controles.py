r"""S21c: eleccion de los dias de control SOLO con la mascara de nubes (ACMF), antes de bajar o mirar el C02.

Regla E1 de H23/H24 (`h24_medir.despejada("chillan")`): un cuadro esta despejado si 80 % o mas del terreno bajo
(10 a 30 km del sitio con paralaje, cota < 1.300 m) tiene ACMF 0 o 1. Cubo ACMF de H23 (21-09 al 23-10) en
D:\goes_notas\s17\h23\acm_oct.npz y de H24 (24 al 31-10) en D:\goes_notas\s18\h24\acm_oct.npz.

Salida: resultados/controles.json y controles.txt.
"""
import json
import os
from datetime import datetime, timedelta

import numpy as np

LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEMV = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
CUBOS = [(r"D:\goes_notas\s17\h23\acm_oct.npz", r"D:\goes_notas\s17\h23\cubo_oct.npz"),
         (r"D:\goes_notas\s18\h24\acm_oct.npz", r"D:\goes_notas\s18\h24\cubo_oct.npz")]
LAT, LON = (np.load(LATLON)[k] for k in ("lat", "lon"))
ZDEM = np.load(DEMV)["zdem"]
la, lo, h = -36.86, -71.38, 3212


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


d = hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo).ravel()
bajo = np.where((d >= 10.0) & (d <= 30.0) & (ZDEM.ravel() < 1300.0))[0]

frac = {}
for fa, fc in CUBOS:
    acm = np.load(fa)["acm"]
    t0 = datetime.strptime(str(np.load(fc)["t0"]), "%Y-%m-%d")
    clara = (acm[:, bajo] <= 1).mean(1)
    falta = (acm[:, bajo] > 3).all(1)          # sin archivo ACMF (relleno)
    for i in range(acm.shape[0]):
        t = t0 + timedelta(minutes=10 * i)
        frac[t] = None if falta[i] else float(clara[i])

# Ventana de la tarde que cubre los pulsos E9 a E12 (rotulos 15:20 a 22:10) y la manana de Landsat (14:20 a 15:00)
TARDE = [(15, 20), (22, 10)]
MANANA = [(14, 0), (15, 20)]
ACTIVOS = {"2026-10-22", "2026-10-23"}         # 22-10 marca VCB (excluido en H23); 23-10 vispera del inicio (H24 §7)


def tramo(dia, h0, h1):
    t = datetime(dia.year, dia.month, dia.day, *h0)
    fin = datetime(dia.year, dia.month, dia.day, *h1)
    out = []
    while t <= fin:
        out.append(frac.get(t))
        t += timedelta(minutes=10)
    return out


res = {}
lineas = []
dia = datetime(2026, 9, 21)
while dia <= datetime(2026, 10, 31):
    tt, mm = tramo(dia, *TARDE), tramo(dia, *MANANA)
    def resumen(v):
        ok = [x for x in v if x is not None]
        return {"n": len(v), "con_acmf": len(ok), "despejados": int(sum(x >= 0.8 for x in ok)),
                "frac_min": round(min(ok), 3) if ok else None}
    res[f"{dia:%Y-%m-%d}"] = {"tarde": resumen(tt), "manana": resumen(mm)}
    dia += timedelta(days=1)

# Regla de seleccion (escrita antes de mirar el C02): dia anterior al 22-10, todos los cuadros del tramo con ACMF
# y E1 despejado en el 100 % de ellos. De los que cumplen, los 6 mas cercanos al 22-10 (temporada mas parecida).
def elegir(tramo_nom):
    ok = [k for k, v in res.items() if k < "2026-10-22" and k not in ACTIVOS
          and v[tramo_nom]["con_acmf"] == v[tramo_nom]["n"] and v[tramo_nom]["despejados"] == v[tramo_nom]["n"]]
    return sorted(ok)[-6:], ok


ct, todos_t = elegir("tarde")
cm, todos_m = elegir("manana")
for k, v in res.items():
    lineas.append(f"{k}: tarde {v['tarde']['despejados']}/{v['tarde']['n']} despejados (ACMF en {v['tarde']['con_acmf']}, "
                  f"min {v['tarde']['frac_min']}); manana {v['manana']['despejados']}/{v['manana']['n']} "
                  f"(ACMF en {v['manana']['con_acmf']}, min {v['manana']['frac_min']})")
lineas.append(f"Dias de tarde que cumplen (antes del 22-10): {todos_t}")
lineas.append(f"Controles de tarde elegidos: {ct}")
lineas.append(f"Dias de manana que cumplen (antes del 22-10): {todos_m}")
lineas.append(f"Controles de manana elegidos: {cm}")
print("\n".join(lineas))
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
with open(os.path.join(base, "controles.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lineas) + "\n")
with open(os.path.join(base, "controles.json"), "w", encoding="utf-8") as f:
    json.dump({"por_dia": res, "control_tarde": ct, "control_manana": cm}, f, indent=1)
