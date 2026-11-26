r"""F1 (S28b): reaplica la regla escrita de cada criterio a las cifras de su resultados/*.json y compara con el rótulo
guardado. No corre ningún detector; sólo lee JSON del repo. Las reglas están copiadas del texto de cada criterio
(sección citada en cada bloque), no del código de la sesión: es el instrumento "criterio contra resultado".
"""
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OV = Path(__file__).resolve().parents[3]


def j(p):
    return json.loads((OV / p).read_text(encoding="utf-8"))


filas = []


def fila(medida, regla, rotulo_json):
    ok = (regla == rotulo_json) or (rotulo_json is not None and regla is not None and rotulo_json.startswith(regla))
    filas.append((medida, regla, rotulo_json, "coincide" if ok else "DIFIERE"))


# S23a, criterio_2026-11-24.md §4
a = j("s23_fondo_2025/resultados/s23a_resultado.json")
inst = j("s23_fondo_2025/resultados/instrumento_2025.json")
seco = j("s23_fondo_2025/resultados/seco.json")
i_ok = inst["cobertura_l1b"] >= .9 and inst["cobertura_acm"] >= .9 and inst["bt11_en_rango"] >= .999 \
    and inst["congelados"] == 0 and inst["I4_correlacion"] >= .9
if not i_ok or seco["fa_media_por_dia"] > .05:
    v = "INVÁLIDA"
elif a["P_evaluados"] < 5:
    v = "NO DECIDIBLE"
elif a["p25"] <= .05:
    v = "CONFIRMA" if a["R"] >= .5 else "PARCIAL"
else:
    v = "NO LLEGA" if a["poder"]["0.33"] >= .8 else "SIN PODER"
fila("S23a veredicto", v, a["veredicto"])
fila("S23a etiqueta", "SEPARA VOLCAT" if a["pN"] <= .05 else "NO SEPARA VOLCAT DEL RESTO DE 2026", a["etiqueta"])
print("S23a: EN_2026 =", a["EN_2026"], "pN =", a["pN"], "(con EN = 0 la cola es 0 para cualquier alcanzado: etiqueta "
      "que no puede fallar)")

# S25a, criterio_2026-11-25.md §4
z = j("s25a_crater/resultados/s25a_resultado.json")
zi = j("s25a_crater/resultados/instrumento.json")["2025"]
if zi["falla"]:
    v = "INVÁLIDA"
elif z["seco"]["fraccion"] > .05:
    v = "NO SIRVE"
elif z["P_evaluados"] < 10 or z["dias_con_P_evaluado"] < 2:
    v = "NO DECIDIBLE"
elif z["p25"] <= .01 and z["pN"] <= .05 and z["R"] >= .25 and z["dias_con_P_alcanzado"] >= 2:
    v = "ALCANZA"
elif z["p25"] <= .01:
    v = "PARCIAL"
else:
    v = "NO ALCANZA"
fila("S25a veredicto", v, z["veredicto"])
d14 = z["dia_14_11"]
fila("S25a 14-11", "14-11 ALCANZADO" if d14["P_alcanzados"] >= 3 and d14["p25"] <= .01 else "14-11 no alcanzado",
     z["veredicto_14_11"])

# S26a, criterio_2026-11-25.md §2 y §3
s = j("s26a_combinado/resultados/s26a_seco.json")
pst = None
for r in s["por_percentil"]:
    if r["union"]["global"] <= .05 and r["union"]["media_por_dia"] <= .05:
        pst = r["pct"]
        break
fila("S26a p*", str(pst), str(s["p_estrella"]))
u = j("s26a_combinado/resultados/s26a_desarrollo.json")["union"]
if pst is None:
    v = "NO SIRVE"
elif u["p25"] <= .01 and u["pN"] <= .05 and u["R"] >= .40 and u["dias_P_alcanzado"] >= 3:
    v = "ALCANZA (desarrollo)"
elif u["p25"] <= .01:
    v = "PARCIAL (desarrollo)"
else:
    v = "NO ALCANZA (desarrollo)"
fila("S26a desarrollo", v, j("s26a_combinado/resultados/s26a_desarrollo.json")["veredicto"])

# S25b, criterio_2026-11-25.md §3 y §5
b = j("s25b_fondo_2024/resultados/s25b_resultado.json")
ins = b["instrumento"]
fila("S25b (a)", "COMPARABLE" if ins["cobertura_l1b"] >= .9 and ins["cobertura_acm"] >= .9 and ins["I4_correlacion"] >= .9
     and ins["I5_iguales"] else "INVÁLIDA", b["veredicto_a"])
for ver in ("S23a", "S23b"):
    x = b["b"][ver]
    fr = [f["tasa"] for f in x["por_franja_2024"].values() if f["tasa"] is not None]
    if x["FA24_media_por_dia"] > .10:
        v = "NO AGUANTA"
    elif x["FA24_media_por_dia"] <= .05 and max(fr) <= .10:
        v = "AGUANTA"
    else:
        v = "DEGRADA"
    fila(f"S25b (b) {ver}", v, x["veredicto"])
    fila(f"S25b (b) {ver} etiqueta MÁS ESTRICTO", str(x["FA24_media_por_dia"] < .02), str(x["mas_estricto_fuera_de_muestra"]))
    print(f"S25b {ver}: franja máxima 2024 = {max(fr)} ({'>' if max(fr) > .05 else '<='} 0,05)")
c = b["c"]
v = "ESTABLE" if c["mediana_abs_dif"] <= .10 and c["max_abs_dif"] <= .25 else (
    "INESTABLE" if c["mediana_abs_dif"] > .20 else "INTERMEDIO")
fila("S25b (c)", v, c["veredicto"])

# S28a, criterio_2026-11-25.md §5
q = j("s28a_vecinas/resultados/s28a_resultado.json")
for per in ("noche", "dia"):
    vec = {s_: q["vecinas"][s_]["principal"][per]["union"] for s_ in ("antuco", "longavi")}
    rch = q["chillan"][per]["todos"]["R"]
    if any(min(x["2025"][1], x["2026"][1]) < 300 for x in vec.values()):
        v = "NO DECIDIBLE"
    else:
        sube = {k: x["R"] >= 1.5 and x["IC95"][0] > 1 for k, x in vec.items()}
        baja = {k: x["R"] <= 1.5 for k, x in vec.items()}
        if all(baja.values()) and all(x["IC95"][1] < rch for x in vec.values()):
            v = "SE SOSTIENE"
        elif all(sube.values()):
            v = "NO SE SOSTIENE"
        elif sum(sube.values()) == 1 and all(sube[k] or baja[k] for k in vec):
            v = "MIXTO"
        else:
            v = "NO CONCLUYENTE"
    fila(f"S28a {per}", v, q["veredicto"][per])

# S26b, criterio_2026-11-25.md §4
e = j("s26b_noche_crater/resultados/s26b_resultado.json")
e3 = e["E3"]
p_sin = min(e3["bajo_limite"]["p_vs_2025"], e3["epoca_21-09_a_11-10"]["p_vs_2025"])
med5 = e["E5"]["F_noche"]["mediana_K"]
p1 = e["E1"]["p_mannwhitney_encendidas_mayor"]
if (e["E1"]["noches_bajo_limite"] < 5 and e3["epoca_21-09_a_11-10"]["cuadros"][1] < 100) or e["E5"]["F_noche_cuadros"] < 20:
    v = "NO DECIDIBLE"
elif p1 <= .01 and e3["bajo_limite"]["p_vs_2025"] > .05 and med5 >= 3:
    v = "EL CALOR EXPLICA"
elif p_sin <= .01 and med5 < 3:
    v = "EL CALOR NO EXPLICA"
else:
    v = "MIXTO"
fila("S26b", v, e["veredicto"])

# S27a, criterio_2026-11-25.md §3
t = j("s27a_noche_causa/resultados/s27a_resultado.json")
P = t["P"]
if P["poder_pluma_ideal"]["p_corrimiento"] > .01:
    v = "SIN PODER (no decidible)"
elif P["2026"]["cuadros"] < 30 or P["2026"]["noches"] < 8:
    v = "NO DECIDIBLE"
else:
    v = "?"
fila("S27a P", v, P["veredicto"])
print("S27a P: piso del nulo por corrimiento con", P["poder_pluma_ideal"]["n_corrimientos"], "corrimientos =",
      round(1 / (1 + P["poder_pluma_ideal"]["n_corrimientos"]), 4), "> 0,01 (umbral inalcanzable, F2)")
N = t["N"]["controles"]
if any(min(x["2025"][1], x["2026"][1]) < 300 for x in N.values()):
    v = "NO DECIDIBLE"
elif all(x["R"] >= 3 and x["p_fisher"] <= .01 for x in N.values()):
    v = "NIEVE SÍ"
elif all(x["R"] <= 1.5 or x["p_fisher"] > .05 for x in N.values()):
    v = "NIEVE NO"
else:
    v = "NO DECIDIBLE"
fila("S27a N", v, t["N"]["veredicto"])
D = t["D"]
d3, d4 = D["D3_toda_la_noche"]["mediana_fraccion_por_noche"] >= .5, (
    D["D4_de_dia"]["mediana_A_dia_15_21UTC"] <= -.3
    and D["D4_de_dia"]["mediana_A_dia_15_21UTC"] <= D["D4_de_dia"]["mediana_A_noche"] + .2)
d2 = len(set(D["D2_fijo"]["primera_mitad"]) & set(D["D2_fijo"]["segunda_mitad"])) >= 2
d1 = not P["veredicto"].startswith("PLUMA SÍ")
v = "DEPÓSITO SÍ" if (d1 and d2 and d3 and d4) else ("DEPÓSITO NO" if (not d3 and not d4) else "NO DECIDIBLE")
fila("S27a D", v, D["veredicto"])

# S27b, criterio §4
k = j("s27b_altura_desfase/resultados/s27b_resultado.json")
pd_ = k["prueba_decide"]
v = "NO DECIDIBLE" if not pd_["llegadas"] else "?"
fila("S27b conjunto", v, k["veredicto_conjunto"])
for ll in k["llegadas"]:
    if "veredicto_caso" in ll:
        print("S27b: la llegada", ll["llegada"], "lleva veredicto_caso", ll["veredicto_caso"],
              "contra la sombra de 4,7 km, que es del 08-11 (criterio §3.7 y §4)")

print("\nmedida | regla del criterio aplicada al JSON | rótulo guardado | ")
for f in filas:
    print(" | ".join(str(x) for x in f))
