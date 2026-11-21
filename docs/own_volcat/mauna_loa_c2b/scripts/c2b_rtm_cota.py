"""C2b, analisis POSTERIOR (no estaba en el criterio; se escribio despues de ver que la prueba del criterio no tiene
cielo despejado): el cielo despejado de VOLCAT (geocatRTM) sigue la cota fina del terreno o la del GFS?

Por que se puede responder sin cielo despejado: geocatRTM es una salida del modelo, no de la observacion. El GFS
de VOLCAT viene en celdas de 0,5 grados (~55 km), y cada pixel ABI dice en que celda cae (nwp_x_index,
nwp_y_index). Si dentro de UNA celda el cielo despejado baja con la cota del pixel a la tasa de enfriamiento del
aire (unos 5 a 7 K por km), el modelo lleva la superficie a la cota de un modelo de elevacion fino (lo que hace
CLAVR-x). Si es plano dentro de la celda, o solo cambia suave como una interpolacion, usa la cota del GFS.

Mide:
1. Cota del GFS de cada celda (surface height del archivo GFS del paquete) contra la cota del modelo de elevacion
   (Terrarium) en las cumbres.
2. Pendiente del cielo despejado de C14 contra la cota, dentro de cada celda con tierra (minimos cuadrados con
   plano en fila y columna, para no confundir el gradiente de una interpolacion con la cota), y agrupada.
3. Variacion del cielo despejado dentro de celdas de oceano (como interpola el GFS).
4. Temperatura del GFS a la cota de la cumbre y en su superficie, para leer el valor de la cumbre.

Uso (venv_hdf4, -I): python -I c2b_rtm_cota.py <npz de c2b_extraer> <c2b_mapas.npz> <gfs.hdf> <salida.json>
"""
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np  # noqa: E402
from pyhdf.SD import SD, SDC  # noqa: E402

SITIOS = {"Mauna Loa": (19.475, -155.608, 4169), "Mauna Kea": (19.821, -155.468, 4207)}


def r(v, n=2):
    return None if v is None or not np.isfinite(v) else round(float(v), n)


def main(npz, mapas, gfs, salida):
    z = np.load(npz); m = np.load(mapas)
    clr = z["geocatRTM__channel_14_brightness_temperature_clear"].astype(float)
    emi = z["geocatRTM__channel_14_surface_emissivity"].astype(float)
    nx = z["geocatRTM__nwp_x_index"].astype(int); ny = z["geocatRTM__nwp_y_index"].astype(int)
    elev, ft, cnt, lat, lon = m["elev"], m["ftierra"], m["cnt"], m["lat"], m["lon"]
    s = SD(gfs, SDC.READ)
    zs = s.select("surface height")[:].astype(float) * 1000.0  # el archivo dice UNITS = km
    tsf = s.select("surface temperature")[:].astype(float)
    T3 = s.select("temperature")[:].astype(float); H3 = s.select("height")[:].astype(float) * 1000.0  # km -> m
    plev = s.select("pressure levels")[:].astype(float); lm = s.select("land mask")[:].astype(float)
    s.end()
    res = {"gfs": os.path.basename(gfs), "notas": []}

    # base de los indices nwp: se elige la que deja la celda mas cerca del pixel (lat = -90 + 0,5 i; lon = 0,5 j)
    mejor = None
    for b in (0, 1):
        la_c = -90 + 0.5 * (ny - b); lo_c = (0.5 * (nx - b) + 180) % 360 - 180
        d = np.nanmax(np.abs(la_c - z["geocatL1__pixel_latitude"])) + np.nanmax(np.abs(lo_c - z["geocatL1__pixel_longitude"]))
        if mejor is None or d < mejor[1]:
            mejor = (b, d)
    b = mejor[0]
    res["base_indices_nwp"] = {"base": b, "max_dif_lat_mas_lon_grados": r(mejor[1], 3)}
    iy, ix = ny - b, nx - b

    # 1. cumbres
    cum = {}
    for nom, (la, lo, h) in SITIOS.items():
        d = (lat - la) ** 2 + ((lon - lo) * np.cos(np.radians(la))) ** 2
        d = np.where(np.isfinite(d) & (cnt >= 20), d, np.inf)
        i, j = np.unravel_index(np.argmin(np.where(elev > 0, d, np.inf)), d.shape)
        # pixel de mayor cota a <= 6 km de la cumbre
        cerca = (d <= (6 / 111.0) ** 2) & (ft == 1)
        k = np.unravel_index(np.argmax(np.where(cerca, elev, -1)), elev.shape)
        cy, cx = iy[k], ix[k]
        alt = H3[cy, cx, :]; tem = T3[cy, cx, :]
        o = np.argsort(alt)
        t_cumbre = float(np.interp(elev[k], alt[o], tem[o]))
        cum[nom] = {"cota_GVP_m": h, "pixel": [int(k[0]), int(k[1])], "cota_vista_pixel_m": r(elev[k], 0),
                    "celda_gfs": [int(cy), int(cx)], "cota_gfs_celda_m": r(zs[cy, cx], 0),
                    "mascara_tierra_gfs": r(lm[cy, cx], 2),
                    "t_superficie_gfs_K": r(tsf[cy, cx]), "t_aire_gfs_a_cota_pixel_K": r(t_cumbre),
                    "clr14_pixel_K": r(clr[k]), "emisividad14_pixel": r(emi[k], 3)}
    res["cumbres"] = cum

    # 2. pendiente dentro de celda (tierra pura, >= 12 pixeles, rango de cota >= 1 km)
    puro = (cnt >= 20) & (ft == 1) & np.isfinite(clr)
    rr, cc = np.meshgrid(np.arange(clr.shape[0]), np.arange(clr.shape[1]), indexing="ij")
    celdas = []
    Xs, ys = [], []
    for key in sorted(set(zip(iy[puro].tolist(), ix[puro].tolist()))):
        sel = puro & (iy == key[0]) & (ix == key[1])
        n = int(sel.sum())
        if n < 12:
            continue
        e = elev[sel] / 1000.0
        if e.max() - e.min() < 1.0:
            continue
        A = np.column_stack([np.ones(n), rr[sel] - rr[sel].mean(), cc[sel] - cc[sel].mean(), e - e.mean()])
        coef, *_ = np.linalg.lstsq(A, clr[sel], rcond=None)
        A2 = np.column_stack([np.ones(n), e - e.mean()])
        c2, *_ = np.linalg.lstsq(A2, clr[sel], rcond=None)
        resid = clr[sel] - A @ coef
        celdas.append({"celda": list(key), "n": n, "cota_min_m": r(elev[sel].min(), 0), "cota_max_m": r(elev[sel].max(), 0),
                       "cota_gfs_m": r(zs[key], 0), "pendiente_K_km_con_plano": r(coef[3]), "pendiente_K_km_sola": r(c2[1]),
                       "resid_sd_K": r(resid.std()), "clr14_rango_K": [r(clr[sel].min()), r(clr[sel].max())]})
        Xs.append(np.column_stack([e - e.mean(), rr[sel] - rr[sel].mean(), cc[sel] - cc[sel].mean()]))
        ys.append(clr[sel] - clr[sel].mean())
    res["celdas_tierra"] = celdas
    if Xs:
        X = np.vstack(Xs); Y = np.concatenate(ys)
        cf, *_ = np.linalg.lstsq(X, Y, rcond=None)
        res["pendiente_agrupada_K_km"] = r(cf[0])
        res["pendientes_por_celda_mediana_K_km"] = r(np.median([c["pendiente_K_km_con_plano"] for c in celdas]))

    # 3. oceano: variacion dentro de la celda
    oc = (cnt >= 20) & (ft == 0) & np.isfinite(clr)
    sds = []
    for key in sorted(set(zip(iy[oc].tolist(), ix[oc].tolist()))):
        sel = oc & (iy == key[0]) & (ix == key[1])
        if sel.sum() >= 50:
            sds.append(clr[sel].std())
    res["oceano_sd_dentro_de_celda_K"] = {"celdas": len(sds), "mediana": r(np.median(sds)) if sds else None,
                                           "max": r(np.max(sds)) if sds else None}
    # todo el dominio, por si la caja del modelo de elevacion es chica
    sd_all = []
    for key in sorted(set(zip(iy.ravel().tolist(), ix.ravel().tolist()))):
        sel = (iy == key[0]) & (ix == key[1]) & np.isfinite(clr) & (lm[key] < 0.5)
        if sel.sum() >= 50:
            sd_all.append(clr[sel].std())
    res["dominio_celdas_mar_gfs_sd_dentro_K"] = {"celdas": len(sd_all), "mediana": r(np.median(sd_all)) if sd_all else None}
    json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "celdas_tierra"}, ensure_ascii=False, indent=1))
    print("celdas de tierra:", len(celdas))
    for c in celdas:
        print(" ", c)


if __name__ == "__main__":
    main(*sys.argv[1:5])
