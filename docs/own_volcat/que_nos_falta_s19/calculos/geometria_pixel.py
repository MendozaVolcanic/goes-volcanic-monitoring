"""Geometria del pixel de ABI (GOES-19) sobre Nevados de Chillan. S19i, 23-11-2026.

Que calcula y por que:
- Tamano en el suelo de un pixel IR (muestreo de 56 urad) y de un pixel de C02 (14 urad):
  para saber que fraccion de pixel llena una pluma de ~1 km de ancho.
- Corrimiento por paralaje de un punto con altura (la cumbre, la pluma): la grilla fija
  de ABI se navega sobre el elipsoide GRS80, asi que todo lo que tiene altura aparece
  corrido alejandose del satelite.

Formulas: GOES-R Product User Guide (PUG) L1b, seccion de navegacion de la grilla fija
(lat/lon <-> angulos de barrido x, y). No usa datos: solo geometria.
Uso: python geometria_pixel.py
"""
from __future__ import annotations

import math

# Parametros de la proyeccion de la grilla fija de GOES-East (mismos de src/config.py y
# src/fetch/goes_acha.py:30: lon_origin = -75.0, H = 35786023 m sobre el elipsoide).
REQ = 6378137.0          # semieje mayor GRS80, m
RPOL = 6356752.31414     # semieje menor GRS80, m
H = 35786023.0 + REQ     # distancia del satelite al centro de la Tierra, m
LON0 = math.radians(-75.0)
E2 = 1.0 - (RPOL / REQ) ** 2

# Nevados de Chillan (src/volcanos.py:48)
LAT, LON, ALT = -36.86, -71.38, 3212.0

IFOV_IR = 56e-6    # rad, muestreo de las bandas de 2 km
IFOV_C02 = 14e-6   # rad, muestreo de la banda de 0,5 km


def ecef(lat_deg: float, lon_deg: float, h: float) -> tuple[float, float, float]:
    """Geodesicas -> cartesianas, con el eje x apuntando a la longitud del satelite."""
    lat, lon = math.radians(lat_deg), math.radians(lon_deg) - LON0
    n = REQ / math.sqrt(1.0 - E2 * math.sin(lat) ** 2)
    return ((n + h) * math.cos(lat) * math.cos(lon),
            (n + h) * math.cos(lat) * math.sin(lon),
            (n * (1.0 - E2) + h) * math.sin(lat))


def scan_angles(p: tuple[float, float, float]) -> tuple[float, float]:
    """Punto cartesiano -> angulos de barrido (x, y) de la grilla fija, en rad."""
    sx, sy, sz = H - p[0], -p[1], p[2]
    y = math.atan2(sz, sx)
    x = math.asin(-sy / math.sqrt(sx * sx + sy * sy + sz * sz))
    return x, y


def ground(x: float, y: float) -> tuple[float, float]:
    """Angulos de barrido -> lat, lon sobre el elipsoide (formula del PUG L1b)."""
    a = math.sin(x) ** 2 + math.cos(x) ** 2 * (math.cos(y) ** 2 + (REQ / RPOL) ** 2 * math.sin(y) ** 2)
    b = -2.0 * H * math.cos(x) * math.cos(y)
    c = H * H - REQ * REQ
    rs = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
    sx, sy, sz = rs * math.cos(x) * math.cos(y), -rs * math.sin(x), rs * math.cos(x) * math.sin(y)
    lat = math.atan((REQ / RPOL) ** 2 * sz / math.sqrt((H - sx) ** 2 + sy * sy))
    lon = LON0 - math.atan2(sy, H - sx)
    return math.degrees(lat), math.degrees(lon)


def dist_km(lat1, lon1, lat2, lon2) -> tuple[float, float]:
    """Distancia (km) y rumbo (grados desde el norte) entre dos puntos cercanos."""
    latm = math.radians((lat1 + lat2) / 2)
    m = REQ * (1 - E2) / (1 - E2 * math.sin(latm) ** 2) ** 1.5   # radio meridiano
    n = REQ / math.sqrt(1 - E2 * math.sin(latm) ** 2)            # radio del primer vertical
    dn = math.radians(lat2 - lat1) * m
    de = math.radians(lon2 - lon1) * n * math.cos(latm)
    return math.hypot(dn, de) / 1000.0, (math.degrees(math.atan2(de, dn)) + 360) % 360


def main() -> None:
    p0 = ecef(LAT, LON, 0.0)
    sat = (H, 0.0, 0.0)
    los = [sat[i] - p0[i] for i in range(3)]
    rng = math.sqrt(sum(v * v for v in los))
    lat, lon = math.radians(LAT), math.radians(LON) - LON0
    up = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))
    vza = math.degrees(math.acos(sum(los[i] * up[i] for i in range(3)) / rng))
    print(f"Distancia satelite-Chillan: {rng / 1000:.0f} km; angulo cenital de vista: {vza:.1f} grados")

    x, y = scan_angles(p0)
    for nombre, ifov in (("IR 2 km (56 urad)", IFOV_IR), ("C02 0,5 km (14 urad)", IFOV_C02)):
        a = ground(x - ifov / 2, y); b = ground(x + ifov / 2, y)
        c = ground(x, y - ifov / 2); d = ground(x, y + ifov / 2)
        ew, _ = dist_km(*a, *b)
        ns, _ = dist_km(*c, *d)
        print(f"Pixel {nombre}: {ew:.2f} km E-O x {ns:.2f} km N-S; area {ew * ns:.2f} km2")

    print("\nParalaje (la grilla fija se navega sobre el elipsoide):")
    for etiqueta, h in (("cumbre 3,2 km", 3212.0), ("pluma 1 km sobre el crater (4,2 km)", 4212.0),
                        ("pluma 2,5 km sobre el crater (5,7 km)", 5712.0), ("por cada km de altura", 1000.0)):
        xa, ya = scan_angles(ecef(LAT, LON, h))
        la, lo = ground(xa, ya)
        d, rumbo = dist_km(LAT, LON, la, lo)
        print(f"  {etiqueta}: aparece {d:.2f} km corrido, rumbo {rumbo:.0f} grados "
              f"({(ya - y) / IFOV_IR:+.2f} filas IR, {(xa - x) / IFOV_IR:+.2f} columnas IR; "
              f"signo: y crece al norte, x crece al este)")

    print("\nFraccion de un pixel IR que llena una pluma recta que lo cruza entero:")
    a = ground(x - IFOV_IR / 2, y); b = ground(x + IFOV_IR / 2, y)
    c = ground(x, y - IFOV_IR / 2); d = ground(x, y + IFOV_IR / 2)
    ew, _ = dist_km(*a, *b); ns, _ = dist_km(*c, *d)
    for w in (0.3, 0.5, 1.0, 2.0):
        print(f"  ancho {w:.1f} km: {min(1, w / ns):.2f} si corre E-O, {min(1, w / ew):.2f} si corre N-S")
    print("  (cota superior: supone el pixel como caja; la respuesta espacial real del detector "
          "reparte ademas parte de la senal en los vecinos)")


if __name__ == "__main__":
    main()
