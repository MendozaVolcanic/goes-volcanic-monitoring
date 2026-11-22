"""H19, exploracion de estructura (antes del criterio): que variables hay y como se codifican.
No calcula acuerdo de ninguna regla candidata. Uso: python -I h19_estructura.py REF HORA"""
import sys
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from h19_io import ruta, leer, atributos, PIX, OBJ, DB

ref, hora = sys.argv[1], sys.argv[2]
l2p = ruta(ref, "L2", hora)
for v in ["ash_probability", "ash_probability_IR", "ash_probability_SW_IR", "ash_probability_subset"]:
    print("ATTR", v, {k: str(x)[:120] for k, x in atributos(l2p, PIX + v).items()})
for v in ["Ash_Group_Id_2d", "Ice_Group_Id_2d", "Hot_Group_Id_2d"]:
    print("ATTR", v, {k: str(x)[:120] for k, x in atributos(l2p, v).items()})
L2 = leer(l2p)
for v in ["ash_probability", "ash_probability_IR", "ash_probability_SW_IR", "ash_probability_subset"]:
    a = L2[PIX + v]
    ok = np.isfinite(a)
    print(v, "validos", ok.sum(), "min", np.nanmin(a), "max", np.nanmax(a),
          ">=0.5:", (a >= 0.5).sum(), ">0:", (a > 0).sum(), "n valores distintos", len(np.unique(a[ok])))
for v in ["Ash_Group_Id_2d", "Ice_Group_Id_2d", "Hot_Group_Id_2d"]:
    a = L2[v]
    u, c = np.unique(a[np.isfinite(a)] if a.dtype.kind == "f" else a, return_counts=True)
    print(v, a.dtype, dict(zip(u.tolist()[:20], c.tolist()[:20])))

for tipo in ["ASHOBJ", "ICEOBJ", "HOTOBJ"]:
    p = ruta(ref, tipo, hora)
    O = leer(p, escalar=False)
    pre = tipo + "_"
    n = len(O[pre + "Object_Id"])
    print("==", tipo, "objetos", n, "pixeles en lista", len(O[pre + "Object_X_Index"]),
          "suma Object_Size", int(O[pre + "Object_Size"].sum()))
    for k in ["Mask", "Status", "Cmask", "Group_Id"]:
        a = O.get(k + DB)
        if a is not None:
            u, c = np.unique(a, return_counts=True)
            print("  ", k, dict(zip(u.tolist(), c.tolist())))
    for k in ["GId", "GAlertId", "GStatus", "GMerged", "GSpectFlag", "GSourceFlag", "GTime", "GTimeBirth",
              "GArea", "GLat", "GLon", "GSelectBirth", "GVolcIdBirth", "GIdBirth"]:
        a = O.get(k + DB)
        if a is not None:
            print("  ", k, a.tolist())
    extra = sorted(k for k in O if not k.startswith(pre))
    print("  variables sin prefijo:", extra[:40])
    ats = atributos(p, "Mask" + DB) if ("Mask" + DB) in O else {}
    print("  ATTR Mask", {k: str(x)[:400] for k, x in ats.items()})
    for k in ["Status", "Cmask", "Group_Id", "GStatus", "GSpectFlag", "GSourceFlag", "GSelectBirth", "GMerged"]:
        if (k + DB) in O:
            print("  ATTR", k, {kk: str(x)[:400] for kk, x in atributos(p, k + DB).items()})

for tipo in []:
    p = ruta(ref, tipo, hora)
    from pyhdf.SD import SD, SDC
    sd = SD(p, SDC.READ)
    print("==", tipo, "atributos globales:", list(sd.attributes().keys())[:30])
    for name, info in sorted(sd.datasets().items(), key=lambda kv: kv[1][3]):
        print("   ", name, info[1])
    sd.end()
