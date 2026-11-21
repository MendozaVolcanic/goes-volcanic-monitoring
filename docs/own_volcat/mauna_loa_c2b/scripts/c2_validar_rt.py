"""C2: el modelo radiativo de H3, con los insumos bajados de nuevo, reproduce el cielo despejado guardado?

Por que: el 20-11 se borro la carpeta dl de H3 (continuo MT_CKD 4.3 y SRF del ABI). Se bajaron otra vez de sus
fuentes a D:\\goes_cache\\rt. Si son los mismos archivos y el codigo es el mismo, el cielo despejado que H11 guardo
por pixel (rt_h11, calculado el 19-20-11 con los originales) tiene que salir igual. Vara (plan 21-11, la de la
etapa 2): error p95 de la BT despejada de C14 <= 0,3 K en 5 escenas de H3.

Seleccion de escenas (fijada antes de correr): de los archivos rt_h11 de pares con origen H3, ordenados por
nombre, 5 a intervalos iguales (np.linspace). Por escena, hasta 300 pixeles al azar con semilla 0. Se recalcula
R_clr con rt_niveles.radiancias_pixel (el mismo camino que lo genero) desde el GFS y la escena de la cache
rescatada, y se pasa a BT con los coeficientes Planck del L1b de esa escena.

Uso (python -I, con las variables de entorno de la cache rescatada):
  H11_H3=...\\trabajo\\h3  H11_B73=...\\trabajo\\b73  H11_TRABAJO=...\\trabajo\\rv  H3_RT_DL=D:\\goes_cache\\rt
  python -I c2_validar_rt.py <carpeta_salida>
"""
import os, sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "reproducir_volcat", "scripts"))
import numpy as np  # noqa: E402
import comun_h11 as C  # noqa: E402
import rt_niveles as R  # noqa: E402

N_ESC, N_PX, SEMILLA = 5, 300, 0


def main(out):
    os.makedirs(out, exist_ok=True)
    print("rt desde", C.rt.__file__, "| lbl.DL", C.rt.lbl.DL, "| LUT", C.rt.LBL, flush=True)
    h3 = sorted({p["pos"] for p in C.pares() if p["origen"] == "H3"})
    archivos = sorted(f for f in os.listdir(C.RTDIR) if f.endswith(".npz") and f.split("_")[0] + "_" + f.split("_")[1] in h3)
    sel = [archivos[i] for i in np.linspace(0, len(archivos) - 1, N_ESC).round().astype(int)]
    print("archivos H3 en rt_h11:", len(archivos), "| elegidos:", sel, flush=True)
    rng = np.random.default_rng(SEMILLA)
    filas, todos = [], []
    for f in sel:
        z = np.load(os.path.join(C.RTDIR, f))
        rol = f[:-4].split("_")[2]; dt = C.dtk("_".join(f.split("_")[:2]))
        esc = C.load(dt); gpath = C.path_gfs(dt)
        assert os.path.basename(gpath) == str(z["gfs"]), (gpath, z["gfs"])
        n = len(z["ys"]); idx = np.sort(rng.choice(n, min(N_PX, n), replace=False))
        ys, xs = z["ys"][idx], z["xs"][idx]
        g = dict(np.load(gpath)); la, lo = C.LAT[ys, xs], C.LON[ys, xs]
        T = np.stack([R._i2(g, g["T"][i], la, lo) for i in range(len(g["p"]))], 1)
        q = np.stack([R._i2(g, g["q"][i], la, lo) for i in range(len(g["p"]))], 1)
        o3 = np.stack([R._i2(g, g["o3"][i], la, lo) for i in range(len(g["p"]))], 1)
        ps, ts = R._i2(g, g["psfc"], la, lo), R._i2(g, g["tskin"], la, lo)
        t0 = time.time()
        rc = np.array([R.radiancias_pixel(g["p"], T[i], q[i], o3[i], ps[i], ts[i], C.SEC[ys[i], xs[i]], False)[0]
                       for i in range(len(idx))])
        d = {}
        for j, b in enumerate(C.BANDS):
            bt_new = C.rt.bt_de_rad(rc[:, j], esc["co"][b]); bt_old = C.rt.bt_de_rad(z["rclr"][idx, j], esc["co"][b])
            d[b] = bt_new - bt_old
        e14 = np.abs(d[14]); todos.append(e14)
        fila = {"archivo": f, "rol": rol, "gfs": str(z["gfs"]), "n_px": int(len(idx)), "seg": round(time.time() - t0, 1),
                "dif_psfc_hPa_max": float(np.abs(ps - z["psfc"][idx]).max()),
                "dif_tskin_K_max": float(np.abs(ts - z["tskin"][idx]).max())}
        for b in C.BANDS:
            fila[f"C{b}_p95_abs_K"] = float(np.percentile(np.abs(d[b]), 95))
            fila[f"C{b}_max_abs_K"] = float(np.abs(d[b]).max())
            fila[f"C{b}_media_K"] = float(d[b].mean())
        filas.append(fila); print(json.dumps(fila, ensure_ascii=False), flush=True)
        np.savez(os.path.join(out, f"c2_{f}"), ys=ys, xs=xs, rclr_nuevo=rc, rclr_guardado=z["rclr"][idx],
                 **{f"dbt{b}": d[b] for b in C.BANDS})
    a = np.concatenate(todos)
    res = {"n_px": int(a.size), "C14_p95_abs_K": float(np.percentile(a, 95)), "C14_max_abs_K": float(a.max()),
           "vara_K": 0.3, "cumple": bool(np.percentile(a, 95) <= 0.3), "escenas": filas,
           "insumos": {"lbl.DL": C.rt.lbl.DL, "LUT": C.rt.LBL, "rt": C.rt.__file__}}
    json.dump(res, open(os.path.join(out, "c2_validacion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("TOTAL", json.dumps({k: v for k, v in res.items() if k != "escenas"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
