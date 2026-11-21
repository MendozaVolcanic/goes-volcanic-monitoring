import json, math
import numpy as np
import paso3_objetos as p

res = json.load(open("paso3_objetos.json"))["res"]
g = json.load(open(p.GVP))["features"]
V = [(f["properties"]["Volcano_Name"], f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]) for f in g]
V = [v for v in V if p.hav(v[1], v[2], *p.CHI) > 5]  # sin Chillan
VLAT = np.array([v[1] for v in V]); VLON = np.array([v[2] for v in V])
print("volcanes GVP sin Chillan:", len(V))

hmap, W = res[0][2], res[0][3]
rr, cc = np.mgrid[0:hmap, 0:W]
LAT = p.LAT0 - rr * p.dp; LON = p.LON0 + cc * p.dp
area = (p.dp * 111.32) ** 2 * np.cos(np.radians(LAT))
dmin = np.full(LAT.shape, np.inf)
for la, lo in zip(VLAT, VLON):
    dmin = np.minimum(dmin, p.hav(LAT, LON, la, lo))
dchi = p.hav(LAT, LON, *p.CHI)
val = p.VALIDO[:hmap, :W] & (dchi > 50)
A_band = {"A": (val & (dmin <= 10)), "B": (val & (dmin > 10) & (dmin <= 50)), "C": (val & (dmin > 50))}
A_km2 = {k: float(area[m].sum()) for k, m in A_band.items()}
print("area km2", {k: round(v) for k, v in A_km2.items()})


def banda(lat, lon):
    d = p.hav(lat, lon, VLAT, VLON).min()
    return "A" if d <= 10 else ("B" if d <= 50 else "C"), d


def corre(excluir16, etiqueta):
    frames = [r for r in res if not (excluir16 and "2026-11-16" in r[0])]
    nf = len(frames)
    cnt = {"A": 0, "B": 0, "C": 0}; dia = {"A": 0, "B": 0, "C": 0}; tam = {"A": [], "B": [], "C": []}
    cnt_all = {"A": 0, "B": 0, "C": 0}; nombres = {}
    for _, _, _, _, rows in frames:
        for t, s, manto, la, lo, z in rows:
            if manto or p.hav(la, lo, *p.CHI) <= 50:
                continue
            # centroide fuera de la zona util (no deberia pasar con VALIDO, pero por si acaso)
            b, d = banda(la, lo)
            cnt_all[b] += 1; tam[b].append(s)
            if 4 <= s <= 36:
                cnt[b] += 1; dia[b] += z < 80
                if b != "C":
                    k = V[int(np.argmin(p.hav(la, lo, VLAT, VLON)))][0]; nombres[k] = nombres.get(k, 0) + 1
    D = {k: cnt[k] / A_km2[k] / nf for k in cnt}
    DAB = (cnt["A"] + cnt["B"]) / (A_km2["A"] + A_km2["B"]) / nf
    R = DAB / D["C"] if D["C"] > 0 else float("inf")
    print(f"\n== {etiqueta}: {nf} cuadros")
    print(" objetos chicos (4-36 px):", cnt, " todos (>3 px, sin manto):", cnt_all)
    print(" densidad por 1e4 km2 por 1000 cuadros:", {k: round(v * 1e7, 3) for k, v in D.items()}, "A+B", round(DAB * 1e7, 3))
    print(" R = D(A+B)/D(C) =", round(R, 2), " D(A)>=D(B):", D["A"] >= D["B"])
    print(" fraccion diurna (cenit < 80) chicos:", {k: (f"{dia[k]}/{cnt[k]}") for k in cnt})
    print(" mediana tamano todos:", {k: (float(np.median(v)) if v else None) for k, v in tam.items()})
    print(" volcanes con objetos chicos en A+B:", sorted(nombres.items(), key=lambda x: -x[1])[:12])


corre(False, "16 dias")
corre(True, "sin 16-11")
