r"""S20b, preparacion (no lee temperaturas de GOES ni termico de ningun sensor): mascara de la pluma en la imagen
fina, altura por la sombra, correccion de paralaje y fraccion de pluma en cada pixel ABI.

Escenas objetivo (catalogadas por el revisor E de S19i):
  - 25-10-2026 14:34:31 UTC, Landsat 8 C2 L2 (LC08_L2SP_233085_20261025_02_T1), Planetary Computer.
  - 08-11-2026 14:53:02 UTC, Sentinel-2C L2A (S2C_19HBV_20261108_0_L2A), Element 84.

Regla de mascara (se repite en el criterio):
  referencia compuesta, celda a celda: entre las escenas Sentinel-2 L2A y Landsat C2 L2 a +-10 dias (no el mismo
    dia, nubosidad de catalogo <= 60 %), cada celda toma la escena mas cercana en fecha en que esa celda tiene dato
    valido y no esta marcada como nube por la mascara de la propia escena dilatada 3 celdas. Primero las escenas
    ANTERIORES (de la mas cercana a la mas lejana) y solo para las celdas que quedan sin dato, las posteriores: la
    ceniza que cae de la propia pluma ensucia la nieve de los dias siguientes (TER-13), y una referencia posterior
    deja de ser nieve justo bajo la pluma.
  nieve de referencia: NDSI = (verde - SWIR1)/(verde + SWIR1) > 0,6, verde > 0,4 y SWIR1 < 0,15.
  pluma: sobre nieve de referencia, SWIR1(objetivo) - SWIR1(referencia) > 0,04, rojo(objetivo) > 0,30 y
    NDSI(objetivo) < 0,80.
    Por que: sobre nieve, nube y ceniza suben el 1,6 um (la nieve lo absorbe) y bajan el NDSI; la roca que
    aparece por derretimiento sube el 1,6 um pero es oscura en el rojo; un cambio de iluminacion entre fechas
    (laderas al sol a otra hora) cambia el brillo pero casi no el NDSI, que es un cociente. Se pierde la pluma que
    no esta sobre nieve: la fraccion medida es un minimo, y se informa la fraccion observable.
  componentes de menos de 5 celdas (0,0045 km2) fuera; solo componentes a <= 15 km del crater.
  AVISO: el termino NDSI(objetivo) < 0,80 y la referencia compuesta se agregaron despues de ver que las primeras
  versiones marcaban laderas iluminadas (referencia de otra hora) y cambios de nieve (referencia de 10 dias). Se
  ajusto mirando solo reflectancia, antes de leer GOES o termico de cualquier fecha.
Altura por la sombra: para cada corrimiento d (0 a 6 km, paso 150 m) de la mascara hacia el azimut opuesto al sol,
mediana de rojo(objetivo)/rojo(referencia) en las celdas corridas que caen sobre nieve de referencia y fuera de la
pluma dilatada 3 celdas (minimo 200 celdas). d* = el corrimiento con la mediana mas baja; h = d* * tan(elevacion
solar) sobre el terreno, H = cota mediana del terreno bajo la sombra + h. Vale solo si la mediana en d* es <= 0,5
(sombra marcada) y el eje de la pluma forma >= 30 grados con la direccion de la sombra (si son casi paralelos, la
pluma se superpone consigo misma y d no queda definido). Si no vale, H = la del aviso del VAAC de esa hora (FL140
el 25-10, FL150 el 08-11).

Uso: python -I s20b_preparar.py
"""
import json
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s20b_comun as C  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
E84 = "https://earth-search.aws.element84.com/v1/search"
PC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"

NDSI_MIN, VERDE_MIN, SW1_REF_MAX = 0.6, 0.4, 0.15
DSW1_MIN, ROJO_MIN, NDSI_OBJ_MAX = 0.04, 0.30, 0.80
MIN_CELDAS, MAX_KM = 5, 15.0
SOMBRA_MAX, ANG_MIN, MIN_SOMBRA = 0.5, 30.0, 200
REF_DIAS, DIL_NUBE = 10, 3
F_MIN = 0.15
VAAC_H = {"2026-10-25": 14000 * 0.3048, "2026-11-08": 15000 * 0.3048}

OBJ = {
    "2026-10-25": {"id": "LC08_L2SP_233085_20261025_02_T1", "fuente": "pc", "hora": "14:34:31"},
    "2026-11-08": {"id": "S2C_19HBV_20261108_0_L2A", "fuente": "e84", "hora": "14:53:02"},
}
TOK = None


def item_e84(iid):
    return C.stac_post(E84, {"collections": ["sentinel-2-l2a"], "ids": [iid]})["features"][0]


def item_pc(iid):
    return C.stac_post(PC, {"collections": ["landsat-c2-l2"], "ids": [iid]})["features"][0]


def bandas(it):
    """Reflectancias verde, rojo, SWIR1, SWIR2 y mascara de nube en la grilla local (cache en D:)."""
    global TOK
    cache = os.path.join(C.TRABAJO, it["id"] + ".npz")
    if os.path.exists(cache):
        return dict(np.load(cache))
    if it["collection"] == "landsat-c2-l2":
        if TOK is None:
            TOK = C.pc_token()
        h = {k: it["assets"][k]["href"] + "?" + TOK for k in ("green", "red", "swir16", "swir22", "qa_pixel")}
        b = {k: C.leer(h[k], 2.75e-5, -0.2) for k in ("green", "red", "swir16", "swir22")}
        qa = C.leer(h["qa_pixel"], rs=C.Resampling.nearest, nodata=1)
        q = np.nan_to_num(qa, nan=1).astype(np.uint32)
        b["nube"] = ((q >> 3) & 1).astype(bool) | ((q >> 1) & 1).astype(bool)      # cloud o dilated cloud
        b["valido"] = np.isfinite(qa) & ((q & 1) == 0)
    else:
        p = it["properties"]
        suma = 0.0 if p.get("earthsearch:boa_offset_applied", False) else -0.1
        b = {k: C.leer(it["assets"][k]["href"], 1e-4, suma) for k in ("green", "red", "swir16", "swir22")}
        scl = C.leer(it["assets"]["scl"]["href"], rs=C.Resampling.nearest, nodata=0)
        b["nube"] = np.isin(scl, [8, 9, 10])
        b["valido"] = np.isfinite(scl) & (scl > 0)
    np.savez_compressed(cache, **b)
    return b


def ndsi(b):
    with np.errstate(invalid="ignore", divide="ignore"):
        return (b["green"] - b["swir16"]) / (b["green"] + b["swir16"])


def nieve_de(b):
    with np.errstate(invalid="ignore"):
        return (ndsi(b) > NDSI_MIN) & (b["green"] > VERDE_MIN) & (b["swir16"] < SW1_REF_MAX)


def referencia_compuesta(dia, objetivo_id):
    d0 = datetime.strptime(dia, "%Y-%m-%d")
    rng = f"{d0 - timedelta(days=REF_DIAS):%Y-%m-%d}T00:00:00Z/{d0 + timedelta(days=REF_DIAS + 1):%Y-%m-%d}T00:00:00Z"
    pt = {"type": "Point", "coordinates": [C.CRATER[1], C.CRATER[0]]}
    cands = C.stac_post(E84, {"collections": ["sentinel-2-l2a"], "intersects": pt, "datetime": rng, "limit": 50})["features"]
    cands += C.stac_post(PC, {"collections": ["landsat-c2-l2"], "intersects": pt, "datetime": rng, "limit": 50,
                              "query": {"platform": {"in": ["landsat-8", "landsat-9"]}}})["features"]
    cands = [c for c in cands if c["properties"]["datetime"][:10] != dia and c["id"] != objetivo_id
             and (c["properties"].get("eo:cloud_cover") or 0) <= 60]

    def clave(c):
        t = datetime.strptime(c["properties"]["datetime"][:19], "%Y-%m-%dT%H:%M:%S")
        return (0 if t < d0 else 1, abs((t.date() - d0.date()).days), c["id"])
    cands.sort(key=clave)
    ref = {k: np.full((C.N, C.N), np.nan, "float32") for k in ("green", "red", "swir16", "swir22")}
    quien = np.full((C.N, C.N), -1, "int16")
    usadas = []
    for i, c in enumerate(cands):
        b = bandas(c)
        claro = (b["valido"] & np.isfinite(b["green"]) & np.isfinite(b["swir16"])
                 & ~ndimage.binary_dilation(b["nube"], iterations=DIL_NUBE))
        nuevo = claro & (quien < 0)
        for k in ref:
            ref[k][nuevo] = b[k][nuevo]
        quien[nuevo] = i
        usadas.append({"id": c["id"], "fecha": c["properties"]["datetime"], "celdas_aportadas": int(nuevo.sum())})
        print("  referencia", usadas[-1], flush=True)
    return ref, quien, usadas


def limpiar(m):
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    if n == 0:
        return m
    tam = ndimage.sum(m, lab, range(1, n + 1))
    d = C.hav(C.GLAT, C.GLON, *C.CRATER)
    dmin = ndimage.minimum(d, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = (tam >= MIN_CELDAS) & (dmin <= MAX_KM)
    return keep[lab]


def angulos_vista(it):
    """(cenit, azimut hacia el sensor) en grados en el crater, aproximados. S2: media de la granula (banda 11).
    Landsat: cenit por la distancia a traves de la traza (orbita a 705 km), azimut perpendicular a la traza."""
    if it["collection"] == "landsat-c2-l2":
        poly = np.array(it["geometry"]["coordinates"][0])
        lados = [(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
        lados.sort(key=lambda ab: -C.hav(ab[0][1], ab[0][0], ab[1][1], ab[1][0]))
        (lo0, la0), (lo1, la1) = lados[0]
        tr = C.Transformer.from_crs(4326, C.CRS, always_xy=True)
        x0, y0 = tr.transform(lo0, la0)
        x1, y1 = tr.transform(lo1, la1)
        ux, uy = (x1 - x0), (y1 - y0)
        nrm = math.hypot(ux, uy)
        ux, uy = ux / nrm, uy / nrm
        cxs, cys = tr.transform(*poly[:-1].mean(0))
        dx, dy = cxs - C.CX, cys - C.CY
        ct = dx * (-uy) + dy * ux
        vx, vy = ct * (-uy), ct * ux
        return math.degrees(math.atan(abs(ct) / 705000.0)), math.degrees(math.atan2(vx, vy)) % 360
    x = urllib.request.urlopen(it["assets"]["granule_metadata"]["href"], timeout=60).read()
    root = ET.fromstring(x)
    for e in root.iter():
        if e.tag.endswith("Mean_Viewing_Incidence_Angle") and e.get("bandId") == "11":
            z = float([c for c in e if c.tag.endswith("ZENITH_ANGLE")][0].text)
            a = float([c for c in e if c.tag.endswith("AZIMUTH_ANGLE")][0].text)
            return z, a
    return float("nan"), float("nan")


def forma(m):
    """Area, largo y ancho (percentiles 2 y 98 sobre el eje principal y el perpendicular), azimuts."""
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return {}
    e, n = C.GX[ys, xs] - C.CX, C.GY[ys, xs] - C.CY
    w, v = np.linalg.eigh(np.cov(np.vstack([e, n])))
    eje = v[:, 1]
    pe, pn = e - e.mean(), n - n.mean()
    a1 = pe * eje[0] + pn * eje[1]
    a2 = pe * v[0, 0] + pn * v[1, 0]
    dist = np.hypot(e, n)
    return {"area_km2": round(len(xs) * C.RES_M ** 2 / 1e6, 3),
            "largo_km_p2_p98": round(float(np.percentile(a1, 98) - np.percentile(a1, 2)) / 1000, 2),
            "ancho_km_p2_p98": round(float(np.percentile(a2, 98) - np.percentile(a2, 2)) / 1000, 2),
            "azimut_eje_grados_0_180": round(math.degrees(math.atan2(eje[0], eje[1])) % 180, 1),
            "azimut_centroide_desde_crater": round(math.degrees(math.atan2(e.mean(), n.mean())) % 360, 1),
            "dist_centroide_km": round(math.hypot(e.mean(), n.mean()) / 1000, 2),
            "dist_max_km": round(float(dist.max()) / 1000, 2), "dist_min_km": round(float(dist.min()) / 1000, 2)}


def altura_por_sombra(pl, nieve, bo, br, sun_az, sun_el, dem, az_eje):
    az = (sun_az + 180) % 360
    a = math.radians(az)
    with np.errstate(invalid="ignore", divide="ignore"):
        rat = bo["red"] / br["red"]
    base = nieve & ~ndimage.binary_dilation(pl, iterations=3)
    curva = []
    for d in np.arange(0, 6001, 150):
        s = C.mover(pl, d * math.sin(a), d * math.cos(a)) & base
        curva.append((float(d), int(s.sum()), float(np.nanmedian(rat[s])) if s.sum() >= MIN_SOMBRA else np.nan))
    meds = np.array([c[2] for c in curva])
    if not np.isfinite(meds).any():
        return {"valida": False, "motivo": "sin celdas de sombra"}, curva
    k = int(np.nanargmin(meds))
    d = curva[k][0]
    s = C.mover(pl, d * math.sin(a), d * math.cos(a)) & base
    z = float(np.nanmedian(dem[s]))
    h = d * math.tan(math.radians(sun_el))
    ang = abs(((az_eje - az) + 90) % 180 - 90)
    return {"valida": bool(meds[k] <= SOMBRA_MAX and ang >= ANG_MIN), "d_m": d,
            "mediana_rojo_rel": round(float(meds[k]), 3), "angulo_eje_sombra": round(ang, 1),
            "h_sobre_terreno_m": round(h), "cota_sombra_m": round(z), "H_m": round(z + h),
            "azimut_sombra": round(az, 1)}, curva


def figura(bo, pl, dia):
    from PIL import Image

    def st(b, lo, hi):
        return (np.clip((np.nan_to_num(b) - lo) / (hi - lo), 0, 1) * 255).astype("uint8")
    rgb = np.dstack([st(bo["swir22"], 0, 0.4), st(bo["swir16"], 0, 0.4), st(bo["red"], 0, 1.2)])
    rgb[pl ^ ndimage.binary_erosion(pl)] = (255, 0, 255)
    c = C.N // 2
    rgb[c - 3:c + 4, c - 3:c + 4] = (255, 255, 0)
    Image.fromarray(rgb[c - 400:c + 400, c - 400:c + 400]).save(os.path.join(FIG, f"mascara_{dia}.png"))


def main():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    f_dem = os.path.join(C.TRABAJO, "dem_local.npy")
    dem = np.load(f_dem) if os.path.exists(f_dem) else C.dem_local()
    np.save(f_dem, dem)
    z_crater = float(dem[C.N // 2, C.N // 2])
    print("cota DEM en el crater", round(z_crater), "m; ajuste ABI residuo", C.RESID, flush=True)
    resumen = {"cota_crater_m": round(z_crater), "ajuste_abi_residuo_px": C.RESID,
               "regla": {"NDSI_MIN": NDSI_MIN, "VERDE_MIN": VERDE_MIN, "SW1_REF_MAX": SW1_REF_MAX,
                         "DSW1_MIN": DSW1_MIN, "ROJO_MIN": ROJO_MIN, "NDSI_OBJ_MAX": NDSI_OBJ_MAX,
                         "MIN_CELDAS": MIN_CELDAS, "MAX_KM": MAX_KM, "SOMBRA_MAX": SOMBRA_MAX, "ANG_MIN": ANG_MIN,
                         "REF_DIAS": REF_DIAS, "DIL_NUBE": DIL_NUBE, "F_MIN": F_MIN}}
    area = C.area_pixel_km2()
    for dia, o in OBJ.items():
        print("==", dia, o["id"], flush=True)
        it = item_pc(o["id"]) if o["fuente"] == "pc" else item_e84(o["id"])
        bo = bandas(it)
        br, quien, usadas = referencia_compuesta(dia, o["id"])
        nieve = nieve_de(br)
        ok = np.isfinite(bo["swir16"]) & np.isfinite(bo["red"])
        with np.errstate(invalid="ignore"):
            pl = (nieve & ok & ((bo["swir16"] - br["swir16"]) > DSW1_MIN) & (bo["red"] > ROJO_MIN)
                  & (ndsi(bo) < NDSI_OBJ_MAX))
        pl = limpiar(pl)
        p = it["properties"]
        sun_az, sun_el = p["view:sun_azimuth"], p["view:sun_elevation"]
        fo = forma(pl)
        alt, curva = altura_por_sombra(pl, nieve & ok, bo, br, sun_az, sun_el, dem,
                                       fo.get("azimut_eje_grados_0_180", 0.0))
        if alt.get("valida"):
            H, fuente_h = float(alt["H_m"]), "sombra"
        else:
            H, fuente_h = VAAC_H[dia], "VAAC"
        vza, vaa = angulos_vista(it)
        # la pluma aparece corrida (H - terreno) * tan(vza) hacia el lado opuesto al sensor: se la devuelve
        h_ag = max(H - float(np.nanmedian(dem[pl])), 0.0) if pl.any() else 0.0
        dpar = h_ag * math.tan(math.radians(vza)) if np.isfinite(vza) else 0.0
        de, dn = dpar * math.sin(math.radians(vaa)), dpar * math.cos(math.radians(vaa))
        plv = C.mover(pl, de, dn)
        nv = C.mover(nieve & ok, de, dn)
        fr = {}
        for etq, hh in (("H", H), ("H-1km", H - 1000), ("H+1km", H + 1000)):
            fr[etq] = (C.acumular(plv, hh) / area, C.acumular(nv, hh) / area)
        f, obs = fr["H"]
        rc, cc = C.a_ventana(C.CRATER[0], C.CRATER[1], z_crater)
        rc, cc = int(round(float(rc))), int(round(float(cc)))
        bloque = np.zeros((C.NY, C.NX), bool)
        bloque[rc - 1:rc + 2, cc - 1:cc + 2] = True
        pob = (f >= F_MIN) & ~bloque
        d15 = C.hav(C.GLAT, C.GLON, *C.CRATER) <= 15
        info = {"objetivo": o["id"], "hora_utc": o["hora"], "referencias": usadas,
                "frac_nieve_ref_15km": round(float(nieve[d15].mean()), 3),
                "frac_sin_referencia_15km": round(float((quien[d15] < 0).mean()), 3),
                "sol_azimut": round(sun_az, 1), "sol_elevacion": round(sun_el, 1),
                "vista_cenit": round(vza, 2), "vista_azimut_hacia_sensor": round(vaa, 1),
                "paralaje_sensor_fino_m": round(dpar), "celdas_pluma": int(pl.sum()),
                "forma": forma(plv), "altura_sombra": alt, "H_usada_m": round(H), "fuente_H": fuente_h,
                "pixel_abi_crater": [rc, cc],
                "pixeles_abi_con_pluma": int((f > 0).sum()), "pixeles_abi_f_ge_fmin": int((f >= F_MIN).sum()),
                "poblacion": [{"fila": int(r), "col": int(c), "f": round(float(f[r, c]), 3),
                               "f_observable": round(float(obs[r, c]), 3), "cota_m": round(float(C.ZDEM[r, c]))}
                              for r, c in zip(*np.nonzero(pob))],
                "f_bloque_crater": round(float(f[bloque].sum()), 3),
                "poblacion_H-1km": int(((fr["H-1km"][0] >= F_MIN) & ~bloque).sum()),
                "poblacion_H+1km": int(((fr["H+1km"][0] >= F_MIN) & ~bloque).sum()),
                "f_max": round(float(f.max()), 3), "pluma_km2_en_ventana": round(float((f * area).sum()), 3)}
        resumen[dia] = info
        print(json.dumps({k: v for k, v in info.items() if k != "referencias"}, ensure_ascii=False),
              flush=True)
        np.savez_compressed(os.path.join(C.TRABAJO, f"mascara_{dia}.npz"), pluma=pl, pluma_vista=plv,
                            nieve=nieve, f=f, obs=obs, f_menos=fr["H-1km"][0], f_mas=fr["H+1km"][0],
                            obs_menos=fr["H-1km"][1], obs_mas=fr["H+1km"][1], bloque=bloque, H=H, quien=quien,
                            curva=np.array(curva, dtype=float))
        figura(bo, pl, dia)
    with open(os.path.join(RES, "preparar_resumen.json"), "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
