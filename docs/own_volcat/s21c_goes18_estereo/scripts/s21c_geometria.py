"""S21c: geometria antes de bajar nada. Salida en resultados/geometria.txt.

Calcula, para GOES-18 y GOES-19 sobre el centro de emision: angulo cenital, azimut, pixel C02, corrimiento en el
disco por km de altura, franja y hora estimada de barrido, error del estereo por pixel y elevacion del sol en los
cuadros de cada pulso.
"""
import math
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402

out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


la, lo = K.VENT
for s in (18, 19):
    vza, az, dist = K.vista(s)
    r0, c0 = K.a_pixel(s, la, lo, K.CRATER_KM * 1000)
    r1, c1 = K.a_pixel(s, la, lo, (K.CRATER_KM + 1) * 1000)
    dr, dc = r1 - r0, c1 - c0
    k, t = K.t_obs(s)
    ifov = 14e-6 * dist                     # km por pixel perpendicular a la linea de vista
    p(f"GOES-{s}: angulo cenital {vza:.2f} grados, azimut hacia el satelite {az:.1f}, distancia {dist:.0f} km")
    p(f"  pixel C02 del centro de emision a {K.CRATER_KM} km: fila {r0:.2f}, columna {c0:.2f}")
    p(f"  por km de altura sobre el crater (columna vertical): {dr:+.3f} filas, {dc:+.3f} columnas, "
      f"{math.hypot(dr, dc):.2f} px; direccion en la imagen atan2(dc, -dr) = "
      f"{math.degrees(math.atan2(dc, -dr)):.0f} grados (0 = arriba en la imagen, 90 = derecha)")
    p(f"  C02 perpendicular a la linea de vista: {ifov:.3f} km; en el suelo: {ifov:.3f} x {ifov / math.cos(math.radians(vza)):.2f} km (aprox.)")
    p(f"  corrimiento en el suelo por km de altura: {math.tan(math.radians(vza)):.2f} km hacia el azimut {(az + 180) % 360:.0f}")
    p(f"  franja del disco (desde 0 al norte): {k}; hora estimada de barrido: {t:.0f} s tras el minuto redondo "
      f"({int(t // 60)} min {t % 60:.0f} s)")

k18, t18 = K.t_obs(18)
k19, t19 = K.t_obs(19)
p(f"Desfase estimado GOES-19 menos GOES-18 sobre Chillan: {t19 - t18:+.0f} s (incertidumbre declarada +-30 s)")

# error del estereo: Jacobiano en un tope a 2 km sobre el crater, sigma 0,5 px por coordenada
for hsc in (1.0, 2.0, 2.4):
    lat2, lon2 = la, lo
    obs = {s: K.a_pixel(s, lat2, lon2, (K.CRATER_KM + hsc) * 1000) for s in (18, 19)}
    de, dn, h, rms, J = K.triangular(obs)
    cov = np.linalg.inv(J.T @ J) * 0.5 ** 2
    sd = np.sqrt(np.diag(cov))
    p(f"Estereo, tope {hsc} km sobre el crater: recupera de {de:+.3f} km, dn {dn:+.3f} km, h {h:.3f} km (rms {rms:.1e} px); "
      f"error 1 sigma con 0,5 px por coordenada en los dos: E {sd[0]:.2f} km, N {sd[1]:.2f} km, h {sd[2]:.2f} km")
    # solo GOES-18 con la hipotesis de columna vertical sobre el centro: altura = largo / (px por km)
r0, c0 = K.a_pixel(18, la, lo, K.CRATER_KM * 1000)
r1, c1 = K.a_pixel(18, la, lo, (K.CRATER_KM + 1) * 1000)
p(f"Solo GOES-18, columna vertical sobre el centro: {math.hypot(r1 - r0, c1 - c0):.2f} px por km -> 0,5 px = "
  f"{0.5 / math.hypot(r1 - r0, c1 - c0):.2f} km de altura")

# deriva de la pluma entre los dos barridos
for v in (5, 10, 20):
    p(f"Viento {v} m/s: la pluma se mueve {v * abs(t19 - t18) / 1000:.2f} km entre los dos barridos "
      f"(+-30 s: hasta {v * (abs(t19 - t18) + 30) / 1000:.2f} km)")

# sol en los cuadros de cada pulso (hora real de barrido de GOES-19 y GOES-18)
pulsos = [("E6", datetime(2026, 10, 27, 9, 26)), ("E9", datetime(2026, 10, 28, 15, 34)),
          ("E10", datetime(2026, 10, 28, 17, 38)), ("E11", datetime(2026, 10, 28, 20, 32)),
          ("E12", datetime(2026, 10, 28, 21, 49)), ("L8", datetime(2026, 10, 25, 14, 34))]
for nom, t0 in pulsos:
    lab = t0.replace(minute=t0.minute // 10 * 10) - timedelta(minutes=10)
    for i in range(5):
        lb = lab + timedelta(minutes=10 * i)
        o19 = lb + timedelta(seconds=t19)
        o18 = lb + timedelta(seconds=t18)
        el, az = K.sol(o19)
        p(f"  {nom} rotulo {lb:%d-%m %H:%M}: GOES-19 mira {o19:%H:%M:%S}, GOES-18 {o18:%H:%M:%S} "
          f"({(o19 - t0).total_seconds() / 60:+.1f} min del inicio); sol {el:.1f} grados de elevacion, azimut {az:.0f}")

with open(os.path.join(os.path.dirname(__file__), "..", "resultados", "geometria.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
