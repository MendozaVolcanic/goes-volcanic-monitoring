r"""S21c: geometria comun de GOES-18 y GOES-19 sobre Nevados de Chillan, para el C02 (0,64 um, 0,5 km).

Formulas de navegacion del PUG L1b vol. 3, sec. 4.2.8 (grilla fija al elipsoide GRS80). Cada satelite con su
longitud de proyeccion leida del encabezado L1b (GOES-18: -137,0; GOES-19: -75,0). Paso de la grilla C02 y origen
leidos del encabezado (x: 1,4e-5 rad, -0,151865; y: -1,4e-5 rad, 0,151865).

Datos pesados en D:\goes_notas\s21\c\ (fuera del repo).
"""
import math
import os
from datetime import datetime, timedelta

import numpy as np

TRABAJO = r"D:\goes_notas\s21\c"
VENT = (-36.8677, -71.3793)      # centro de emision (RAV 06-11), el de H24
CRATER_KM = 3.2                  # cota del crater, como H10 y H24
H_SAT = 35786023.0
RE, RP = 6378137.0, 6356752.31414
E2 = 1 - (RP / RE) ** 2
SAT_LON = {18: -137.0, 19: -75.0}
DX, X0 = 1.4e-05, -0.151865      # C02: x = X0 + DX * columna
DY, Y0 = -1.4e-05, 0.151865      # C02: y = Y0 + DY * fila
NFD = 21696
VEL_BARRIDO = 0.024434           # rad/s E-O (Kalluri 2018, p. 4)
FRANJA = 0.013807                # rad N-S por franja, 22 franjas iguales (S19i INS-01)
# Modo 6A (goes-r.gov, abiScanModeInfo, leido por S19i): franja 0 empieza a 19,5 s; franja 18 (indice desde 0)
# de 513,2 a 524,5 s; la ultima termina en 590,7 s. Las franjas intermedias se interpolan linealmente (ver criterio).
T_FRANJA0, T_FRANJA18 = 19.5, 513.2


def ecef(lat, lon, h):
    p, l = np.radians(lat), np.radians(lon)
    n = RE / np.sqrt(1 - E2 * np.sin(p) ** 2)
    return np.array([(n + h) * np.cos(p) * np.cos(l), (n + h) * np.cos(p) * np.sin(l), (n * (1 - E2) + h) * np.sin(p)])


def barrido(sat, lat, lon, h_m=0.0):
    """Angulos de barrido (x, y) en rad de un punto a h_m sobre el elipsoide visto por GOES-<sat>."""
    X, Y, Z = ecef(lat, np.asarray(lon) - SAT_LON[sat], h_m)
    sx, sy, sz = (H_SAT + RE) - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def a_pixel(sat, lat, lon, h_m=0.0):
    """Fila y columna (fraccionarias) del disco completo C02 donde GOES-<sat> ve el punto."""
    x, y = barrido(sat, lat, lon, h_m)
    return (y - Y0) / DY, (x - X0) / DX


def sat_ecef(sat):
    return np.array([(H_SAT + RE) * math.cos(math.radians(SAT_LON[sat])),
                     (H_SAT + RE) * math.sin(math.radians(SAT_LON[sat])), 0.0])


def enu(lat, lon):
    p, l = math.radians(lat), math.radians(lon)
    e = np.array([-math.sin(l), math.cos(l), 0.0])
    n = np.array([-math.sin(p) * math.cos(l), -math.sin(p) * math.sin(l), math.cos(p)])
    u = np.array([math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p)])
    return e, n, u


def vista(sat, lat=VENT[0], lon=VENT[1], h_m=CRATER_KM * 1000):
    """Angulo cenital de vista, azimut hacia el satelite (grados) y distancia (km)."""
    P = ecef(lat, lon, h_m)
    d = sat_ecef(sat) - P
    e, n, u = enu(lat, lon)
    dist = np.linalg.norm(d)
    vza = math.degrees(math.acos(d @ u / dist))
    az = math.degrees(math.atan2(d @ e, d @ n)) % 360
    return vza, az, dist / 1000


def desplazar(lat, lon, de_km, dn_km):
    return lat + dn_km / 111.2, lon + de_km / (111.2 * np.cos(np.radians(lat)))


def t_obs(sat, lat=VENT[0], lon=VENT[1], h_m=CRATER_KM * 1000):
    """Segundos desde el minuto redondo del rotulo en que el ABI de GOES-<sat> barre el punto (estimacion)."""
    x, y = barrido(sat, lat, lon, h_m)
    k = int((Y0 - y) // FRANJA)
    t0 = T_FRANJA0 + k * (T_FRANJA18 - T_FRANJA0) / 18.0
    # dentro de la franja, de oeste a este: borde oeste del disco en la latitud de barrido del punto
    ymid = Y0 - (k + 0.5) * FRANJA
    r = 0.151865
    xw = -math.sqrt(max(r * r - ymid * ymid, 0.0))
    return k, t0 + (x - xw) / VEL_BARRIDO


def sol(dt, lat=VENT[0], lon=VENT[1]):
    """Elevacion y azimut del sol (grados), formula de NOAA (precision de ~0,1 grado, basta para esto)."""
    doy = dt.timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (dt.hour - 12 + dt.minute / 60 + dt.second / 3600) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                    - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
           + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = dt.hour * 60 + dt.minute + dt.second / 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    p = math.radians(lat)
    cz = math.sin(p) * math.sin(dec) + math.cos(p) * math.cos(dec) * math.cos(ha)
    zen = math.acos(max(-1, min(1, cz)))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(p) - math.tan(dec) * math.cos(p))) + 180
    return 90 - math.degrees(zen), az % 360


def triangular(obs, lat0=VENT[0], lon0=VENT[1]):
    """Punto 3D (de_km, dn_km, h_km sobre el elipsoide) que mejor explica las posiciones observadas.

    obs: {sat: (fila, columna)} en el disco C02. Minimos cuadrados con Jacobiano numerico (Gauss-Newton).
    Devuelve (de, dn, h, residuo_rms_px, jacobiano)."""
    p = np.array([0.0, 0.0, CRATER_KM + 1.0])

    def modelo(q):
        la, lo = desplazar(lat0, lon0, q[0], q[1])
        out = []
        for s in sorted(obs):
            r, c = a_pixel(s, la, lo, q[2] * 1000)
            out += [r, c]
        return np.array(out)

    y = np.array([v for s in sorted(obs) for v in obs[s]])
    for _ in range(20):
        f0 = modelo(p)
        J = np.zeros((len(y), 3))
        for i in range(3):
            dq = np.zeros(3)
            dq[i] = 1e-3
            J[:, i] = (modelo(p + dq) - f0) / 1e-3
        step = np.linalg.lstsq(J, y - f0, rcond=None)[0]
        p = p + step
        if np.abs(step).max() < 1e-6:
            break
    res = y - modelo(p)
    return p[0], p[1], p[2], float(np.sqrt(np.mean(res ** 2))), J


def cuadros(dia, h0, h1):
    """Rotulos de 10 min entre h0 y h1 (datetime UTC) del dia."""
    t, out = datetime(dia.year, dia.month, dia.day, h0.hour, h0.minute), []
    fin = datetime(dia.year, dia.month, dia.day, h1.hour, h1.minute)
    while t <= fin:
        out.append(t)
        t += timedelta(minutes=10)
    return out


def ruta_cuadro(sat, dt):
    return os.path.join(TRABAJO, "l1b", f"g{sat}_{dt:%Y%m%d_%H%M}.npz")
