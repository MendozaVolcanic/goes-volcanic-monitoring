"""H7: aplica criterio_H7_seguimiento_2026-11-19.md (carpeta de notas local_f3a7d295...).

Entradas: objetos.json + huellas_h7.npz (volcat_obj.py), fdcf.jsonl (fetch_fdcf.py), BT por ventana de
det/cache y h7/cache (C11=b11 8,4 um, C14=b14 11,2 um, C15=b15 12,3 um; K, Planck del NetCDF L1b).
Salida: texto por stdout (se guarda como h7_resultado.txt).
"""
import os, json
from datetime import datetime, timedelta
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
CACHES = [os.path.join(DET, "cache"), os.path.join(HERE, "cache")]
H3CACHE = os.path.join(os.path.dirname(HERE), "h3", "cache")
VLAT, VLON = -36.86, -71.38
ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


DIST = hav(LAT, LON, VLAT, VLON)
SEED = DIST <= 10.0
K3 = np.ones((3, 3), bool)

# ---------------- VOLCAT
OBJ = {}
for r in json.load(open(os.path.join(HERE, "objetos.json"))):
    if "err" in r:
        continue
    OBJ[datetime.fromisoformat(r["dt"]).replace(second=0)] = r
HU = np.load(os.path.join(HERE, "huellas_h7.npz"))


def k(t):
    return t.strftime("%Y%m%d_%H%M")


def pub(t):
    return t in OBJ


def con_obj(t):
    return pub(t) and OBJ[t]["n50"] > 0


def anclado(t):
    return pub(t) and OBJ[t]["nanc"] > 0


def antecesor(t):
    """Cuadro anterior publicado (10 min; si no se publico, 20 min). Devuelve (t_prev, tiene_objeto)."""
    for m in (10, 20):
        tp = t - timedelta(minutes=m)
        if pub(tp):
            return tp, con_obj(tp)
    return None, None


# ---------------- ABI
def scan(t):
    for c in CACHES:
        p = os.path.join(c, k(t) + ".npz")
        if os.path.exists(p):
            z = np.load(p)
            return {b: z[b].astype("float64") for b in ("b11", "b14", "b15")}
    # respaldo de solo lectura: cache de la sesion H3 (misma ventana; verificado identico a det en 28-10 22:40)
    p = os.path.join(H3CACHE, k(t) + ".npz")
    if os.path.exists(p):
        z = np.load(p)
        return {f"b{b}": z[f"bt{b}"].astype("float64") for b in (11, 14, 15)}
    return None


# ---------------- FDCF
FD = {}
for ln in open(os.path.join(HERE, "fdcf.jsonl")):
    r = json.loads(ln)
    if r.get("scan"):
        FD[datetime.strptime(r["slot"], "%Y-%m-%d %H:%M")] = r


def hs10(t, con_tf=False):
    """Hot spots FDCF a <= 10 km en el scan t. None = scan no verificable."""
    r = FD.get(t)
    if r is None:
        return None
    n = sum(1 for h in r["hs"] if h["d_km"] <= 10)
    if con_tf:
        n += sum(1 for h in r["tf"] if h["d_km"] <= 10)
    return n


def senal_b(t, con_tf=False):
    v = [hs10(t - timedelta(minutes=m), con_tf) for m in (0, 10, 20)]
    if any(x for x in v if x):
        return True, v
    if any(x is None for x in v):
        return None, v
    return False, v


def senal_a(t, huella):
    s = scan(t)
    if s is None or not huella.any():
        return None, None
    hd = ndimage.binary_dilation(huella, structure=K3)
    btd = s["b14"] - s["b15"]
    v = btd[hd]
    return bool(np.nanmin(v) < -1.0), float(np.nanmin(v))


def senal_c(t):
    s, s0 = scan(t), scan(t - timedelta(minutes=10))
    if s is None or s0 is None:
        return None, None
    d = s["b14"] - s0["b14"]
    n = int(np.sum((d <= -2.0) & SEED))
    return n >= 2, n


def huella(t, tipo="anc"):
    return HU[k(t) + "_" + tipo]


# ---------------- Episodios
def rango(a, b):
    out = []; t = a
    while t <= b:
        out.append(t); t += timedelta(minutes=10)
    return out


EPIS = {
    "E1": rango(datetime(2026, 10, 28, 21, 50), datetime(2026, 10, 29, 1, 40)),
    "E2": rango(datetime(2026, 11, 10, 0, 0), datetime(2026, 11, 10, 23, 50)),
    "E3": rango(datetime(2026, 11, 14, 16, 40), datetime(2026, 11, 14, 22, 40)),
}
DIAS = {"E1": ["2026-10-28", "2026-10-29"], "E2": ["2026-11-10"], "E3": ["2026-11-14"]}


def fmt(x):
    return "NA" if x is None else ("si" if x is True else ("no" if x is False else str(x)))


def evalua(t, tipo="anc"):
    a, amin = senal_a(t, huella(t, tipo))
    b, bv = senal_b(t)
    btf, _ = senal_b(t, con_tf=True)
    c, cn = senal_c(t)
    return dict(a=a, amin=amin, b=b, bv=bv, btf=btf, c=c, cn=cn)


def propia(e, usar_b=True, b_key="b"):
    vals = [e["a"], e["c"]] + ([e[b_key]] if usar_b else [])
    if any(v is True for v in vals):
        return True
    if any(v is None for v in vals):
        return None
    return False


def inicio_tramo(t):
    """Retrocede por la cadena de antecesores con objeto hasta el primer cuadro anclado del tramo."""
    primero = t if anclado(t) else None
    cur = t
    while True:
        tp, tiene = antecesor(cur)
        if tp is None or not tiene:
            return primero
        cur = tp
        if anclado(cur):
            primero = cur


def main():
    print("H7: resultado de la prueba (criterio_H7_seguimiento_2026-11-19.md). Generado por h7_analisis.py.")
    print("Signo: (a) BTD 11,2-12,3 um < -1 K en huella anclada dilatada 1 px; (b) hot spot FDCF Mask 10-15 a <= 10 km en t, t-10 o t-20;")
    print("(c) >= 2 px a <= 10 km con BT11,2 al menos 2 K mas fria que t-10. NA = dato faltante.\n")

    # ---- lineas base
    base = {}
    for E, dias in DIAS.items():
        slots = [t for t in sorted(OBJ) if t.strftime("%Y-%m-%d") in dias and not con_obj(t)]
        huellas_ep = [huella(t) for t in EPIS[E] if anclado(t)]
        bb = [senal_b(t)[0] for t in slots]
        bbtf = [senal_b(t, True)[0] for t in slots]
        cc = [senal_c(t)[0] for t in slots]
        aa = []; aany = []
        for t in slots:
            s = scan(t)
            if s is None:
                continue
            btd = s["b14"] - s["b15"]
            r = [bool(np.nanmin(btd[ndimage.binary_dilation(h, structure=K3)]) < -1.0) for h in huellas_ep]
            aa.extend(r); aany.append(any(r))
        def pr(v):
            v = [x for x in v if x is not None]
            return f"{sum(v)}/{len(v)} = {100*sum(v)/max(1,len(v)):.1f} %"
        base[E] = dict(b=[x for x in bb if x is not None])
        nb = [x for x in bb if x is not None]
        base[E]["frac_b"] = sum(nb) / max(1, len(nb))
        horas_abi = sorted({t.strftime("%d %H") for t in slots if scan(t) is not None})
        print(f"LINEA BASE {E} (dias {', '.join(dias)}; scans publicados SIN objeto VOLCAT a <= 50 km: {len(slots)})")
        print(f"  (b) hot spot FDCF Mask 10-15 (t, t-10, t-20): {pr(bb)}   [sensibilidad con Mask 30-35: {pr(bbtf)}]")
        print(f"  (c) crecimiento: {pr(cc)}  (solo scans con L1b en cache y su t-10)")
        print(f"  (a) BTD<-1 en huellas ancladas del episodio ({len(huellas_ep)} huellas) trasplantadas: pares {pr(aa)}; scans con alguna huella positiva {pr(aany)}")
        print(f"  horas con L1b en la linea base: {horas_abi[0]} a {horas_abi[-1]} ({len([t for t in slots if scan(t) is not None])} scans)")
        pos_c = [t for t in slots if senal_c(t)[0]]
        print(f"  (c) positivos en la linea base: {' '.join(f'{t:%d/%H:%M}' for t in pos_c)}")
        print()

    b_ok = all(base[E]["frac_b"] < 0.8 for E in base)
    b_glob = sum(sum(base[E]["b"]) for E in base) / max(1, sum(len(base[E]["b"]) for E in base))
    print(f"(b) discriminante? fraccion global de la linea base = {100*b_glob:.1f} %; por episodio " +
          ", ".join(f"{E} {100*base[E]['frac_b']:.1f} %" for E in base) +
          (" -> todas < 80 %: (b) ENTRA" if b_ok else " -> alguna >= 80 %: (b) NO discriminante, veredicto con (a) y (c)"))
    print()

    tot_sin = 0; tot_sin_ant = 0; tot_sin_pri = 0; primeros = {}
    for E, ts in EPIS.items():
        anc = [t for t in ts if anclado(t)]
        print(f"===== {E}: {ts[0]:%d-%m %H:%M} a {ts[-1]:%d-%m %H:%M} UTC, {len(anc)} cuadros anclados")
        no_pub = [f"{t:%H:%M}" for t in ts if not pub(t)]
        print(f"  slots no publicados por SSEC en la ventana: {', '.join(no_pub) if no_pub else 'ninguno'}")
        # tramos
        tramos = []
        for t in anc:
            tp, tiene = antecesor(t)
            if not tiene:
                tramos.append([t])
            else:
                if not tramos:
                    tramos.append([t])  # tramo que viene de antes de la ventana
                else:
                    tramos[-1].append(t)
        for i, tr in enumerate(tramos):
            ini = inicio_tramo(tr[0])
            nota = "" if ini == tr[0] else f"  (empieza ANTES de la ventana: primer cuadro anclado del tramo {ini:%d-%m %H:%M})"
            print(f"  tramo {i+1}: {tr[0]:%d-%m %H:%M} a {tr[-1]:%d-%m %H:%M} ({len(tr)} anclados){nota}")
        print("  cuadro       | antecesor (t_prev, objeto) | rol          | px VOLCAT | (a) BTDmin | (b) hs t,t-10,t-20 | (c) n px | propia")
        for t in anc:
            tp, tiene = antecesor(t)
            rol = "continuacion" if tiene else "PRIMERO"
            e = evalua(t)
            p = propia(e, b_ok)
            print(f"  {t:%d-%m %H:%M}  | {tp.strftime('%H:%M') if tp else '--:--'} {fmt(tiene):3s}               | {rol:12s} | {OBJ[t]['px_anc']:4d}/{OBJ[t]['abi_anc']:3d}abi | "
                  f"{fmt(e['a']):3s} {e['amin'] if e['amin'] is None else round(e['amin'], 2)!s:6s} | {fmt(e['b']):3s} {e['bv']!s:13s} | "
                  f"{fmt(e['c']):3s} {e['cn']!s:3s} | {fmt(p)}")
            if p is not True:
                tot_sin += 1
                tot_sin_ant += bool(tiene); tot_sin_pri += (not tiene)
        # tramos del mismo dia ANTERIORES a la ventana (informativo)
        dia0 = ts[0].replace(hour=0, minute=0)
        previos = [t for t in rango(dia0, ts[0] - timedelta(minutes=10)) if anclado(t)]
        if previos:
            print("  cuadros anclados del mismo dia ANTES de la ventana (informativo):")
            for t in previos:
                tp, tiene = antecesor(t); e = evalua(t)
                print(f"    {t:%d-%m %H:%M} antecesor {tp.strftime('%H:%M') if tp else '--:--'} {fmt(tiene)} -> {'continuacion' if tiene else 'PRIMERO'}; "
                      f"(a) {fmt(e['a'])} {None if e['amin'] is None else round(e['amin'], 2)}, (b) {fmt(e['b'])} {e['bv']}, "
                      f"(c) {fmt(e['c'])} {e['cn']} -> propia {fmt(propia(e, b_ok))}")
        # primer cuadro del primer tramo
        t1 = inicio_tramo(tramos[0][0])
        e1 = evalua(t1); p1 = propia(e1, b_ok)
        primeros[E] = (t1, p1, e1)
        print(f"  PRIMER CUADRO DEL PRIMER TRAMO: {t1:%d-%m %H:%M}: (a) {fmt(e1['a'])} BTDmin {e1['amin']}, (b) {fmt(e1['b'])} {e1['bv']}, "
              f"(c) {fmt(e1['c'])} n={e1['cn']} -> senal propia {fmt(p1)}")
        # sensibilidad huella_50
        print("  sensibilidad (a) con huella = todos los objetos a <= 50 km: " +
              " ".join(f"{t:%H:%M}:{fmt(senal_a(t, huella(t, '50'))[0])}" for t in anc))
        print()

    n_con = sum(1 for v in primeros.values() if v[1] is True)
    n_sin = sum(1 for v in primeros.values() if v[1] is False)
    print("TOTALES")
    print(f"  primer cuadro del primer tramo con senal propia: {n_con} de 3 episodios; sin senal: {n_sin}; NA: {3-n_con-n_sin}")
    print(f"  cuadros anclados sin senal propia (incluye NA): {tot_sin}; con antecesor (continuacion): {tot_sin_ant}; primeros de tramo: {tot_sin_pri}")
    fc = tot_sin_ant / tot_sin if tot_sin else float('nan')
    print(f"  fraccion continuacion = {100*fc:.1f} %; fraccion primeros = {100*(1-fc):.1f} %")
    if tot_sin < 5:
        v = "NO CONCLUYENTE (menos de 5 cuadros anclados sin senal)"
    elif n_con >= 2 and fc >= 0.70:
        v = "H7 SE SOSTIENE (>= 2 episodios con primer cuadro con senal y >= 70 % de los sin senal son continuacion)"
    elif n_sin >= 2 or (1 - fc) > 0.30:
        v = "H7 SE FALSA (" + ("primer cuadro sin senal en >= 2 episodios" if n_sin >= 2 else "") + \
            (" y " if n_sin >= 2 and (1 - fc) > 0.30 else "") + ("> 30 % de los sin senal son primeros de tramo" if (1 - fc) > 0.30 else "") + ")"
    else:
        v = "NO CONCLUYENTE"
    print("  VEREDICTO:", v)


if __name__ == "__main__":
    main()
