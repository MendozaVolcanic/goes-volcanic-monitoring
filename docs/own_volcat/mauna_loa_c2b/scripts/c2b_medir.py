"""C2b, paso 2: cielo despejado de VOLCAT (geocatRTM) contra lo observado en cumbres de 4 km. Criterio:
docs/own_volcat/mauna_loa_c2b/criterio_C2b_2026-11-21.md (commit ac81069, subido antes de correr esto).

Por que: si el modelo radiativo de VOLCAT no lleva la superficie a la cota real, su cielo despejado en una cumbre
queda mas tibio que lo observado, como el nuestro en Chillan. D = BT11 despejado (geocatRTM, canal 14) menos BT11
observado (geocatL1, canal 14), en pixeles despejados segun pruebas que solo usan la observacion.

Pasos:
1. Modelo de elevacion (teselas Terrarium z9). Cada celda se proyecta CON su altura sobre la grilla fija del ABI
   (paralaje) y se asigna al pixel donde cae: elevacion media vista, fraccion de tierra y lat/lon verdaderas
   medias por pixel. Se comprueba antes la proyeccion: las lat/lon de geocatL1 a altura 0 deben volver a su
   fila y columna.
2. Pruebas de despejado por pixel y cuadro (criterio, seccion "Pixel despejado").
3. Sitios, estadistica de D, regla, y lo descriptivo (tramos de cota, Haleakala, oceano, emisividad que publica
   VOLCAT, probabilidad IR).

Uso: python -I c2b_medir.py <carpeta npz> <carpeta dem> <L1b C14 NetCDF de input> <carpeta salida>
"""
import os, sys, glob, json, math
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

DECIDEN = ("091600", "092100", "092600")
SITIOS = {"Mauna Loa": (19.475, -155.608), "Mauna Kea": (19.821, -155.468)}
KILAUEA = (19.408, -155.283)
HALEAKALA = (20.709, -156.253)


# ------------------------------------------------------------------ geometria
def proyeccion(nc_path):
    import netCDF4
    d = netCDF4.Dataset(nc_path); p = d["goes_imager_projection"]
    g = dict(a=float(p.semi_major_axis), b=float(p.semi_minor_axis), h=float(p.perspective_point_height),
             lon0=float(p.longitude_of_projection_origin))
    x = d["x"]; y = d["y"]
    g.update(x_sc=float(x.scale_factor), x_of=float(x.add_offset), y_sc=float(y.scale_factor), y_of=float(y.add_offset),
             nx=len(d.dimensions["x"]), ny=len(d.dimensions["y"]))
    d.close()
    return g


def escaneo(lat, lon, h, g):
    """Angulos de escaneo (x, y) en rad del ABI para un punto geodetico con altura h (m). ECEF exacto, sin aproximar."""
    a, b = g["a"], g["b"]; e2 = 1 - (b / a) ** 2
    la = np.radians(lat); dl = np.radians(lon - g["lon0"])
    N = a / np.sqrt(1 - e2 * np.sin(la) ** 2)
    X = (N + h) * np.cos(la) * np.cos(dl); Y = (N + h) * np.cos(la) * np.sin(dl); Z = (N * (1 - e2) + h) * np.sin(la)
    H = g["h"] + a
    sx, sy, sz = H - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def fila_col(x, y, g, meta):
    """Indices (0) dentro del subconjunto geocat. Columna completa = (x - offset)/escala; el subconjunto empieza en
    First_Line_Processed y First_Element_Processed (base 1)."""
    c = (x - g["x_of"]) / g["x_sc"] - (meta["First_Element_Processed"] - 1)
    r = (y - g["y_of"]) / g["y_sc"] - (meta["First_Line_Processed"] - 1)
    return r, c


def dist_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2); dp = p2 - p1; dl = np.radians(lon2 - lon1)
    s = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(s))


def dem(carpeta):
    lat, lon, el = [], [], []
    for f in sorted(glob.glob(os.path.join(carpeta, "t9_*.png"))):
        _, x, y = os.path.basename(f)[:-4].split("_"); x, y = int(x), int(y)
        a = np.asarray(Image.open(f).convert("RGB"), "float64")
        e = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        j, i = np.meshgrid(np.arange(256), np.arange(256))
        n = 2 ** 9
        lo = (x + (j + 0.5) / 256) / n * 360 - 180
        la = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (y + (i + 0.5) / 256) / n))))
        lat.append(la.ravel()); lon.append(lo.ravel()); el.append(e.ravel())
    return np.concatenate(lat), np.concatenate(lon), np.concatenate(el)


# ------------------------------------------------------------------ medicion
def planck_inv(R, co):
    fk1, fk2, bc1, bc2 = co
    return (fk2 / np.log(fk1 / R + 1) - bc1) / bc2


def planck(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * T))


def resumen(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if v.size == 0:
        return {"n": 0}
    return {"n": int(v.size), "mediana": round(float(np.median(v)), 2), "p10": round(float(np.percentile(v, 10)), 2),
            "p90": round(float(np.percentile(v, 90)), 2), "min": round(float(v.min()), 2), "max": round(float(v.max()), 2)}


def main(npzdir, demdir, l1b, out):
    os.makedirs(out, exist_ok=True)
    horas = sorted(os.path.basename(f)[4:-4] for f in glob.glob(os.path.join(npzdir, "c2b_*.npz")))
    Z = {h: np.load(os.path.join(npzdir, f"c2b_{h}.npz")) for h in horas}
    meta = json.loads(str(Z[horas[0]]["meta"]))
    g = proyeccion(l1b)
    L1 = lambda h, v: Z[h]["geocatL1__" + v]  # noqa: E731
    lat0, lon0 = L1(horas[0], "pixel_latitude"), L1(horas[0], "pixel_longitude")
    NY, NX = lat0.shape
    res = {"proyeccion": g, "meta_nav": meta, "horas": horas, "deciden": DECIDEN}

    # 1a. comprobacion de la proyeccion con los propios pixeles
    xs, ys = escaneo(lat0.astype(float), lon0.astype(float), 0.0, g)
    r, c = fila_col(xs, ys, g, meta)
    rr, cc = np.meshgrid(np.arange(NY), np.arange(NX), indexing="ij")
    dr, dc = r - rr, c - cc
    res["chequeo_proyeccion"] = {"dfila_mediana": float(np.median(dr)), "dfila_maxabs": float(np.abs(dr).max()),
                                 "dcol_mediana": float(np.median(dc)), "dcol_maxabs": float(np.abs(dc).max())}
    off_r, off_c = round(float(np.median(dr))), round(float(np.median(dc)))
    print("chequeo proyeccion", res["chequeo_proyeccion"], "desfase entero aplicado", off_r, off_c, flush=True)
    assert abs(np.median(dr) - off_r) < 0.05 and abs(np.median(dc) - off_c) < 0.05 and np.abs(dr - off_r).max() < 0.05

    # 1b. elevacion vista por pixel
    dla, dlo, de = dem(demdir)
    hs = np.maximum(de, 0.0)
    xs, ys = escaneo(dla, dlo, hs, g)
    r, c = fila_col(xs, ys, g, meta)
    r = np.rint(r - off_r).astype(int); c = np.rint(c - off_c).astype(int)
    ok = (r >= 0) & (r < NY) & (c >= 0) & (c < NX)
    idx = r[ok] * NX + c[ok]
    cnt = np.bincount(idx, minlength=NY * NX).reshape(NY, NX)
    tierra = np.bincount(idx, (de[ok] > 0).astype(float), minlength=NY * NX).reshape(NY, NX)
    elev = np.bincount(idx, hs[ok], minlength=NY * NX).reshape(NY, NX)
    elmax = np.full(NY * NX, -1e9); np.maximum.at(elmax, idx, hs[ok]); elmax = elmax.reshape(NY, NX)
    tla = np.bincount(idx, dla[ok], minlength=NY * NX).reshape(NY, NX)
    tlo = np.bincount(idx, dlo[ok], minlength=NY * NX).reshape(NY, NX)
    with np.errstate(invalid="ignore", divide="ignore"):
        ftierra = tierra / cnt; elev = elev / cnt; tla = tla / cnt; tlo = tlo / cnt
    cubierto = cnt >= 20
    puro = cubierto & (ftierra == 1)
    res["dem"] = {"celdas": int(de.size), "pixeles_cubiertos": int(cubierto.sum()), "pixeles_tierra_pura": int(puro.sum()),
                  "celdas_por_pixel_mediana": float(np.median(cnt[cubierto])), "elev_max_vista_m": float(np.nanmax(elev[puro]))}
    print("dem", res["dem"], flush=True)

    # 2. pruebas de despejado (solo observacion)
    bt14 = np.stack([L1(h, "channel_14_brightness_temperature") for h in horas])
    bt15 = np.stack([L1(h, "channel_15_brightness_temperature") for h in horas])
    bt7 = np.stack([L1(h, "channel_7_brightness_temperature") for h in horas])
    clr14 = np.stack([Z[h]["geocatRTM__channel_14_brightness_temperature_clear"] for h in horas])
    t1 = (bt14 - bt15 >= -1.0) & (bt14 - bt15 <= 3.0)
    t2 = (bt7 - bt14 >= -2.0) & (bt7 - bt14 <= 4.0)
    dif = np.full(bt14.shape, np.nan)
    for k in range(len(horas)):
        v = [np.abs(bt14[k] - bt14[j]) for j in (k - 1, k + 1) if 0 <= j < len(horas)]
        dif[k] = np.mean(v, axis=0)
    t3 = dif <= 1.0
    t4 = bt14 >= 250.0
    desp = t1 & t2 & t3 & t4
    D = clr14 - bt14
    dec = np.array([h in DECIDEN for h in horas])

    # emisividad que publica VOLCAT y cielo despejado efectivo implicito (supuesto: nube negra a 195 K y a 210 K)
    co = tuple(float(Z[horas[0]][k][13]) for k in ("fk1_planck", "fk2_planck", "bc1_planck", "bc2_planck"))
    eps = np.stack([Z[h]["geocatDIAGS1__vcat_ashdet_pix_2_7_10_11_13_14_15_cloud_emissivity_ch14_tot"] for h in horas])
    pir = np.stack([Z[h]["geocatL2__vcat_ashdet_pix_2_7_10_11_13_14_15_ash_probability_IR"] for h in horas])
    sesgo = np.stack([Z[h]["geocatDIAGS1__vcat_ashdet_obj_2_7_10_11_13_14_15_Bt14_Bias_Env_Per75"] for h in horas])
    Robs = planck(bt14, co)
    bt_ef = {}
    for tc in (195.0, 210.0):
        Rc = planck(tc, co)
        with np.errstate(invalid="ignore", divide="ignore"):
            bt_ef[tc] = planck_inv((Robs - eps * Rc) / (1 - eps), co)

    # 3. sitios
    lat_v = np.where(cubierto, tla, lat0); lon_v = np.where(cubierto, tlo, lon0)
    masc = {}
    for s, (la, lo) in SITIOS.items():
        masc[s] = puro & (elev >= 3800) & (dist_km(lat_v, lon_v, la, lo) <= 10)
    masc["Control bajo"] = puro & (elev <= 300) & (dist_km(lat_v, lon_v, *KILAUEA) > 15) & (dist_km(lat_v, lon_v, *SITIOS["Mauna Loa"]) > 15)
    masc["Haleakala (desc.)"] = puro & (elev >= 2800) & (dist_km(lat_v, lon_v, *HALEAKALA) <= 10)
    tierra_any = cubierto & (ftierra > 0)
    lejos = ~ndimage.binary_dilation(tierra_any, np.ones((11, 11), bool))
    masc["Oceano (desc.)"] = cubierto & (ftierra == 0) & lejos

    sitios, filas_csv = {}, []
    for s, m in masc.items():
        sel = desp & m[None]
        e = {"pixeles": int(m.sum()), "elev_media_m": round(float(np.nanmean(elev[m])), 0) if m.any() else None,
             "elev_max_m": round(float(np.nanmax(elev[m])), 0) if m.any() else None,
             "despejados_por_cuadro": {h: int(sel[k].sum()) for k, h in enumerate(horas)},
             "pruebas_pasadas_deciden": {n: int((tt[dec] & m[None]).sum()) for n, tt in
                                          (("t1_btd1112", t1), ("t2_btd3911", t2), ("t3_estable", t3), ("t4_bt250", t4))},
             "pixeles_cuadro_posibles_deciden": int(m.sum() * dec.sum()),
             "D_deciden": resumen(D[dec][sel[dec]]), "D_todos_cuadros": resumen(D[sel]),
             "bt11_obs_deciden": resumen(bt14[dec][sel[dec]]), "bt11_clr_deciden": resumen(clr14[dec][sel[dec]]),
             "eps14_volcat_deciden": resumen(eps[dec][sel[dec]]),
             "bt_clr_efectivo_volcat_195K_menos_obs": resumen((bt_ef[195.0] - bt14)[dec][sel[dec]]),
             "bt_clr_efectivo_volcat_210K_menos_obs": resumen((bt_ef[210.0] - bt14)[dec][sel[dec]]),
             "prob_ceniza_IR_deciden": resumen(pir[dec][sel[dec]]),
             "sesgo_bt14_env_p75_deciden": resumen(sesgo[dec][sel[dec]])}
        sitios[s] = e
        print(s, json.dumps({k: e[k] for k in ("pixeles", "elev_media_m", "D_deciden", "D_todos_cuadros")}, ensure_ascii=False), flush=True)
        for k, h in enumerate(horas):
            for (i, j) in zip(*np.nonzero(m)):
                filas_csv.append([s, h, int(i), int(j), round(float(lat_v[i, j]), 4), round(float(lon_v[i, j]), 4),
                                  round(float(elev[i, j]), 0), int(t1[k, i, j]), int(t2[k, i, j]), int(t3[k, i, j]),
                                  int(t4[k, i, j]), int(desp[k, i, j]), round(float(bt14[k, i, j]), 2),
                                  round(float(clr14[k, i, j]), 2), round(float(D[k, i, j]), 2),
                                  round(float(eps[k, i, j]), 4) if np.isfinite(eps[k, i, j]) else "",
                                  round(float(pir[k, i, j]), 4) if np.isfinite(pir[k, i, j]) else ""])
    res["sitios"] = sitios

    # descriptivo: D contra cota, tierra pura, cuadros que deciden
    tramos = []
    for lo in range(0, 4500, 500):
        m = puro & (elev >= lo) & (elev < lo + 500) & (dist_km(lat_v, lon_v, *KILAUEA) > 15)
        sel = desp[dec] & m[None]
        tramos.append({"tramo_m": f"{lo}-{lo + 500}", "pixeles": int(m.sum()), **resumen(D[dec][sel])})
    res["D_por_tramo_de_cota"] = tramos

    # regla
    ml, mk, ct = (sitios[s]["D_deciden"] for s in ("Mauna Loa", "Mauna Kea", "Control bajo"))
    motivo = []
    if ml.get("n", 0) < 5 or mk.get("n", 0) < 5:
        motivo.append("menos de 5 pixeles-cuadro despejados en alguna cumbre")
    if ct.get("n", 0) == 0 or abs(ct["mediana"]) > 2:
        motivo.append("control bajo sin datos o con |mediana D| > 2 K")
    if motivo:
        ver = "no concluyente (" + "; ".join(motivo) + ")"
    else:
        a, b = abs(ml["mediana"]), abs(mk["mediana"])
        if a <= 2 and b <= 2:
            ver = "VOLCAT corrige la cota (|mediana D| <= 2 K en las dos cumbres)"
        elif a >= 5 and b >= 5:
            ver = "VOLCAT no corrige la cota en su modelo radiativo; depende del sesgo local (|mediana D| >= 5 K en las dos cumbres)"
        else:
            ver = "no concluyente (cumbres entre 2 y 5 K o en lados distintos)"
    res["veredicto"] = ver
    print("VEREDICTO", ver, flush=True)
    json.dump(res, open(os.path.join(out, "c2b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(out, "c2b_pixeles_sitios.csv"), "w", encoding="utf-8") as f:
        f.write("sitio,hora,fila,col,lat,lon,elev_m,t1,t2,t3,t4,despejado,bt11_obs,bt11_clr_rtm,D,eps14_volcat,prob_ir\n")
        for row in filas_csv:
            f.write(",".join(str(x) for x in row) + "\n")
    np.savez_compressed(os.path.join(out, "c2b_mapas.npz"), elev=elev, ftierra=ftierra, cnt=cnt, lat=lat_v, lon=lon_v,
                        D=D, desp=desp, horas=np.array(horas))


if __name__ == "__main__":
    main(*sys.argv[1:5])
