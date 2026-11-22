"""H21: avisos del VAAC Buenos Aires contra las 30 marcas de ceniza de VOLCAT en Nevados de Chillán.

Criterio pre-registrado: docs/own_volcat/h21_vaac/criterio_2026-11-22.md (commit 80aed90).

Qué hace, en el orden del criterio:
1. Lee los avisos (resultados/avisos_texto.txt, transcritos del SMN y verificados por hash contra el
   navegador) y separa sus campos.
2. Clasifica cada aviso en SI / POSIBLE / NO / INDETERMINADO. La clase que manda es la MANUAL
   (CLASIF_MANUAL), escrita leyendo cada texto con las definiciones del criterio; un lector por expresiones
   regulares con el léxico literal del criterio sirve de control (las dos tienen que coincidir, o se dice
   dónde no).
3. Para cada marca de VOLCAT busca el aviso de Chillán con OBS/EST VA DTG más cercano y aplica la ventana
   de ±60 min. Lo mismo para las horas de control (misma hora del día en días sin marca).
4. Sorteo pareado por hora del día (10.000) y Fisher como referencia. Poder: cuántas SI hacen falta.

Uso:  python -I h21_cruce.py <csv_eventos_grafana> <carpeta_resultados>
El CSV de eventos está fuera del repo (D:\\goes_notas\\s16\\sitio\\grafana\\...), sólo se lee.
"""
import csv
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VENTANA_MIN = 60
SEMILLA = 20261122
N_SORTEOS = 10_000

# ---------------------------------------------------------------------------------------------
# Clasificación manual: una línea por aviso, con la frase del texto que la decide.
# fuentes: SAT, CAM, PIREP (ARS/piloto), OVDAS_SERNAGEOMIN (SVO, OVDAS), SIGMET, MODELO (GFS).
# indep_rmk: el RMK (o ERUPTION DETAILS) describe una observación no satelital de ceniza o emisión.
# indep_lista: INFO SOURCE o RMK nombran una fuente no satelital (CAM, PIREP, OVDAS_SERNAGEOMIN).
# ---------------------------------------------------------------------------------------------
CLASIF_MANUAL = {
    "2026/024": ("SI", "EMISSIONS OF VA ARE SEEN IN SATELLITE IMAGERY; webcam tambien", True),
    "2026/025": ("NO", "VA NOT IDENTIFIABLE FM SATELLITE DATA", False),
    "2026/026": ("SI", "LIGHT VA CLD OBS IN SATELLITE", False),
    "2026/027": ("NO", "NOT IDENTIFIABLE FROM SATELLITE; NOT OBS ... DUE WX CLDS", False),
    "2026/028": ("SI", "LIGHT VA CLD OBS IN SATELLITE IMAGES (SVO solo en INFO SOURCE)", False),
    "2026/029": ("SI", "SATELLITE IMAGERY SHOWS VA PLUME; WEBCAM SHOWS PUFF EMISSIONS OF VA", True),
    "2026/030": ("POSIBLE", "SPORADIC WEAK EMISSIONS DETECTED ON SATELLITE (WEAK, lexico POSIBLE)", False),
    "2026/031": ("NO", "EST: UNABLE TO DETECT FROM SATELLITE ... DUE TO WX CLOUD COVER", False),
    "2026/032": ("NO", "VA NOT IDENTIFIABLE FROM STLT DATA", False),
    "2026/033": ("SI", "VA EMISSION DETECTED IN SATELLITE DATA", False),
    "2026/034": ("SI", "VA PLUME ... SEEN IN STLT IMAGERY; SVO REPORT PUFF EMISSION AT 27/1025Z", True),
    "2026/035": ("SI", "A FAINT VA PLUME ... CAN BE SEEN IN STLT IMAGERY", False),
    "2026/036": ("POSIBLE", "WEAK EMISSIONS ARE SEEN IN SATELLITE IMAGERY (WEAK)", False),
    "2026/037": ("POSIBLE", "WEAK SPORADIC EMISSIONS ARE DETECTED IN SATELLITE DATA (WEAK)", False),
    "2026/038": ("POSIBLE", "WEAK AND CONTINUOUS EMISSIONS OF STEAM AND LIG VA ... ON STLT DATA (WEAK)", False),
    "2026/039": ("POSIBLE", "WEAK AND CONTINUOUS EMISSIONS OF STEAM AND LIG VA ... ON STLT DATA (WEAK)", False),
    "2026/040": ("NO", "EST: UNABLE TO DETECT VA FROM SATELLITE IMAGERY DUE TO WX CLOUD COVER", False),
    "2026/041": ("NO", "VA NOT IDENTIFIABLE FROM SATELLITE DATA UNDER CLEAR SKIES", False),
    "2026/042": ("SI", "A FAINT VA PLUME ... CAN BE SEEN IN STLT IMAGERY", False),
    "2026/043": ("SI", "SPORADIC AND FAINT VA PULSES ... ARE SEEN IN STLT IMAGERY", False),
    "2026/044": ("NO", "VA NOT IDENTIFIABLE FROM SATELLITE IMAGERY UNDER CLEAR SKIES", False),
    "2026/517": ("NO", "Sabancaya: VA NOT SEEN IN STLT IMAGERY (solo control del lector)", False),
    "2026/045": ("NO", "ARS/SIGMET REPORT VA EMS, ... NO INDICATION OF VA IN STLT IMAGERY", True),
    "2026/046": ("NO", "ARS/SIGMET REPORT VA EMS, ... NO INDICATION OF VA IN STLT IMAGERY", True),
    "2026/047": ("SI", "VA DETECTED IN VIS SATELLITE IMAGERY; EST FL150 BASED ON ARS REPORT", True),
    "2026/048": ("SI", "VA SEEN IN SATELLITE DATA", False),
    "2026/049": ("NO", "VA NOT DETECTED IN SATELLITE IMAGERY UNDER SKC", False),
    "2026/050": ("NO", "SVO REPORT MINOR ERUPTION AT 2151Z TL FL190. VA NOT DETECTED IN SATELLITE", True),
    "2026/051": ("SI", "FAINT VA PLUME DETECTED IN SATELLITE IMAGERY (SVO solo en INFO SOURCE)", False),
    "2026/052": ("NO", "VA NOT DETECTED IN SATELLITE IMAGERY UNDER SKC", False),
    "2026/053": ("NO", "A PILOT REPORTED ASH ... NO INDICATION OF ASH IN SATELLITE IMAGERY", True),
    "2026/054": ("NO", "NOT IDENTIFIABLE FM SATELLITE; OVDAS WEBCAM ... PSBL LGT ASH", True),
    "2026/055": ("NO", "poligono de WEBCAMS; SATELLITE IMAGERY DOES NOT REVEAL THE PRESENCE OF ASH", True),
    "2026/056": ("SI", "A FAINT VA PLUME DETECTED IN STLT IMAGERY; WEBCAMS ... PSBL LGT ASH", True),
    "2026/057": ("NO", "NOT IDENTIFIABLE FROM SATELLITE; WEBCAM ... PSBL LGT VA", True),
}

def leer_avisos(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    bloques = re.split(r"^##### (\S+)\n", texto, flags=re.M)[1:]
    avisos = []
    for i in range(0, len(bloques), 2):
        nombre, cuerpo = bloques[i], bloques[i + 1]
        campos, actual = {}, None
        for linea in cuerpo.splitlines():
            m = re.match(r"^([A-Z][A-Z ]+?):\s?(.*)$", linea)
            if m:  # toda línea "CLAVE: ..." abre campo; las demás continúan el anterior
                actual = m.group(1)
                campos[actual] = m.group(2).strip()
            elif actual and linea.strip():
                campos[actual] += " " + linea.strip()
        avisos.append({"archivo": nombre, **campos})
    return avisos


def hora_obs(av):
    """OBS VA DTG (o EST VA DTG) como datetime UTC; el mes y el año salen de DTG."""
    dtg = datetime.strptime(av["DTG"], "%Y%m%d/%H%MZ").replace(tzinfo=timezone.utc)
    clave = "OBS VA DTG" if "OBS VA DTG" in av else "EST VA DTG"
    dia, hhmm = av[clave].rstrip("Z").split("/")
    t = dtg.replace(day=int(dia), hour=int(hhmm[:2]), minute=int(hhmm[2:]))
    if t > dtg + timedelta(hours=1):  # observación del día anterior al cambio de mes
        t -= timedelta(days=1)
    return t, ("OBS" if clave == "OBS VA DTG" else "EST")


SAT = r"(SAT|SATELLITE|SATELITE|STLT|IMAGERY|IMAGENES)"
NEG = (r"(NOT IDENTIFIABLE|NOT IDENTIFIED|NOT OBS|NOT OBSERVED|NOT VISIBLE|NOT DETECTED|NO VA DETECTED|"
       r"CANNOT BE SEEN|NO SE OBSERVA|NO IDENTIFICABLE)")
NUBE = r"(OBSCURED BY MET CLD|DUE TO MET CLD|CLOUD COVER)"
POSI = r"(POSSIBLE|PROBABLE|SUSPECTED|WEAK|POSIBLE|DEBIL)"
VISTO = (r"(VA OBS ON SAT|SEEN IN SATELLITE|IDENTIFIED IN SAT IMAGERY|SE OBSERVA EN IMAGENES|"
         r"OBS IN SATELLITE|SEEN IN STLT|DETECTED IN SATELLITE|DETECTED ON SATELLITE|DETECTED IN STLT|"
         r"DETECTED ON STLT|DETECTED IN VIS SATELLITE|SHOWS VA PLUME|SEEN IN SATELLITE IMAGERY|"
         r"DETECTED IN SATELLITE DATA|SEEN IN SATELLITE DATA)")


def lector_regex(av):
    """Léxico literal del criterio (más las formas 'SEEN/DETECTED IN ...' de SI). Sólo control."""
    cld = av.get("OBS VA CLD", av.get("EST VA CLD", ""))
    rmk = av.get("RMK", "")
    for campo in (cld, rmk):
        if re.search(NEG + r".{0,40}" + SAT, campo) or re.search(NUBE, campo):
            return "NO"
    tiene_nube = bool(re.search(r"(SFC|FL\d{3})/FL\d{3}", cld))
    if tiene_nube and (re.search(VISTO, rmk) or re.search(r"GOES|SAT", av.get("INFO SOURCE", ""))):
        if re.search(POSI + r".{0,60}" + SAT, rmk):
            return "POSIBLE"
        return "SI"
    return "INDETERMINADO"


def fuentes(av):
    txt = av.get("INFO SOURCE", "") + " " + av.get("RMK", "")
    f = []
    if re.search(r"GOES|SAT|STLT", txt):
        f.append("SAT")
    if re.search(r"WEBCAM", txt):
        f.append("CAM")
    if re.search(r"\bARS\b|PILOT|PIREP|AIREP", txt):
        f.append("PIREP")
    if re.search(r"\bSVO\b|SERNAGEOMIN|OVDAS", txt):
        f.append("OVDAS_SERNAGEOMIN")
    if re.search(r"SIGMET", txt):
        f.append("SIGMET")
    if re.search(r"GFS", txt):
        f.append("MODELO")
    return f


def leer_marcas(ruta):
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    todas = [datetime.fromtimestamp(int(r["Time"]) / 1000, tz=timezone.utc) for r in filas]
    marcas = [t for t, r in zip(todas, filas) if float(r["Ash Event"] or 0) > 0]
    return marcas, todas[0], todas[-1]


def cercano(t, avisos_chillan):
    mejor = min(avisos_chillan, key=lambda a: abs((a["t_obs"] - t).total_seconds()))
    dt = (mejor["t_obs"] - t).total_seconds() / 60
    return mejor, dt


def clase_en_ventana(t, avisos_chillan, ventana=VENTANA_MIN):
    av, dt = cercano(t, avisos_chillan)
    if abs(dt) <= ventana:
        return av["clase"], av, dt
    return "SIN AVISO", av, dt


def main(csv_eventos, carpeta):
    carpeta = Path(carpeta)
    base = Path(__file__).resolve().parents[1]
    avisos = leer_avisos(base / "resultados" / "avisos_texto.txt")
    log = []

    def p(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        log.append(s)

    # Una entrada por número de aviso: la última corrección (CCB) reemplaza a las anteriores.
    por_nr = {}
    for av in avisos:
        por_nr[av["ADVISORY NR"]] = av
    p(f"Avisos leidos: {len(avisos)} archivos, {len(por_nr)} numeros de aviso distintos")

    acuerdo, total = 0, 0
    filas_av = []
    for nr, av in sorted(por_nr.items(), key=lambda kv: kv[1]["DTG"]):
        av["t_obs"], av["tipo_hora"] = hora_obs(av)
        clase, frase, indep_rmk = CLASIF_MANUAL[nr]
        av["clase"], av["frase"], av["indep_rmk"] = clase, frase, indep_rmk
        av["fuentes"] = fuentes(av)
        av["indep_lista"] = any(f in av["fuentes"] for f in ("CAM", "PIREP", "OVDAS_SERNAGEOMIN"))
        av["cita_volcat"] = "VOLCAT" in av.get("INFO SOURCE", "")
        av["regex"] = lector_regex(av)
        total += 1
        acuerdo += av["regex"] == clase
        filas_av.append({
            "nr": nr, "archivo": av["archivo"], "volcan": av["VOLCANO"],
            "hora_obs_utc": av["t_obs"].strftime("%Y-%m-%d %H:%M"), "tipo_hora": av["tipo_hora"],
            "clase_manual": clase, "clase_regex": av["regex"], "fuentes": "+".join(av["fuentes"]),
            "indep_rmk": av["indep_rmk"], "indep_lista": av["indep_lista"], "cita_volcat": av["cita_volcat"],
            "frase": frase,
        })
    p(f"Lector regex vs manual: {acuerdo}/{total} iguales")
    for f in filas_av:
        if f["clase_manual"] != f["clase_regex"]:
            p(f"  distinto: {f['nr']} manual={f['clase_manual']} regex={f['clase_regex']} :: {f['frase']}")
    rng = random.Random(SEMILLA)
    muestra = rng.sample(filas_av, 10)
    iguales = sum(f["clase_manual"] == f["clase_regex"] for f in muestra)
    p(f"Control positivo del lector (10 al azar, semilla {SEMILLA}): {iguales}/10 iguales -> "
      f"{'PASA' if iguales == 10 else 'NO PASA: manda la clasificacion manual'}")
    p("  muestra:", ", ".join(f["nr"] for f in muestra))
    clases = [f["clase_manual"] for f in filas_av]
    p("Clases (todos los avisos):", {c: clases.count(c) for c in sorted(set(clases))})

    chillan = [av for av in por_nr.values() if "CHILLAN" in av["VOLCANO"]]
    numeros = sorted(int(nr.split("/")[1]) for nr, av in por_nr.items() if "CHILLAN" in av["VOLCANO"])
    huecos = [n for n in range(numeros[0], numeros[-1] + 1) if n not in numeros]
    p(f"Completitud Chillan: avisos 2026/{numeros[0]:03d} a 2026/{numeros[-1]:03d}, huecos: {huecos}")

    marcas, t0, t1 = leer_marcas(csv_eventos)
    p(f"Marcas VOLCAT: {len(marcas)} (CSV {t0:%Y-%m-%d %H:%M} a {t1:%Y-%m-%d %H:%M} UTC)")

    # ---- marcas ----
    filas_m = []
    for t in marcas:
        clase, av, dt = clase_en_ventana(t, chillan)
        clase3, _, _ = clase_en_ventana(t, chillan, 180)
        vigente = any(timedelta(0) <= t - datetime.strptime(a["DTG"], "%Y%m%d/%H%MZ").replace(
            tzinfo=timezone.utc) <= timedelta(hours=6) for a in chillan)
        filas_m.append({
            "marca_utc": t.strftime("%Y-%m-%d %H:%M:%S"),
            "aviso_cercano": av["ADVISORY NR"], "hora_obs_aviso": av["t_obs"].strftime("%Y-%m-%d %H:%M"),
            "dt_min": round(dt), "clase_aviso_cercano": av["clase"], "clase_1h": clase,
            "clase_3h": clase3, "episodio_vigente_6h": vigente,
            "fuentes": "+".join(av["fuentes"]) if clase != "SIN AVISO" else "",
            "indep_rmk": av["indep_rmk"] if clase != "SIN AVISO" else "",
            "indep_lista": av["indep_lista"] if clase != "SIN AVISO" else "",
            "cita_volcat": av["cita_volcat"] if clase != "SIN AVISO" else "",
            "frase": av["frase"] if clase != "SIN AVISO" else "",
        })
    cuenta = {}
    for f in filas_m:
        cuenta[f["clase_1h"]] = cuenta.get(f["clase_1h"], 0) + 1
    n_si = cuenta.get("SI", 0)
    n_si_pos = n_si + cuenta.get("POSIBLE", 0)
    n_si_indep = sum(1 for f in filas_m if f["clase_1h"] == "SI" and f["indep_rmk"] is True)
    n_si_indep_l = sum(1 for f in filas_m if f["clase_1h"] == "SI" and f["indep_lista"] is True)
    p(f"Marcas por clase a +-1 h: {cuenta}")
    p(f"  SI={n_si}  SI+POSIBLE={n_si_pos}  SI con fuente independiente en RMK={n_si_indep}  "
      f"(en INFO SOURCE o RMK={n_si_indep_l})")
    c3 = {}
    for f in filas_m:
        c3[f["clase_3h"]] = c3.get(f["clase_3h"], 0) + 1
    p(f"  Descriptivo +-3 h: {c3}; episodio vigente (aviso en las 6 h previas): "
      f"{sum(f['episodio_vigente_6h'] for f in filas_m)}/30")

    # ---- control ----
    dias_marca = {t.date() for t in marcas}
    dia = t0.date() + timedelta(days=1)
    dias_ctrl = []
    while dia < t1.date():
        if dia not in dias_marca:
            dias_ctrl.append(dia)
        dia += timedelta(days=1)
    p(f"Dias de control: {len(dias_ctrl)} ({dias_ctrl[0]} a {dias_ctrl[-1]})")
    ctrl_por_marca = []
    filas_c = []
    for t in marcas:
        lista = []
        for d in dias_ctrl:
            tc = datetime.combine(d, t.timetz())
            if any(abs((tc - m).total_seconds()) <= 3600 for m in marcas):
                continue
            clase, av, dt = clase_en_ventana(tc, chillan)
            lista.append(clase)
            filas_c.append({"marca_utc": t.strftime("%Y-%m-%d %H:%M:%S"),
                            "control_utc": tc.strftime("%Y-%m-%d %H:%M:%S"),
                            "clase_1h": clase, "aviso_cercano": av["ADVISORY NR"], "dt_min": round(dt)})
        ctrl_por_marca.append(lista)
    todas_c = [c for lista in ctrl_por_marca for c in lista]
    cc = {c: todas_c.count(c) for c in sorted(set(todas_c))}
    tasa_c = todas_c.count("SI") / len(todas_c)
    tasa_c_pos = (todas_c.count("SI") + todas_c.count("POSIBLE")) / len(todas_c)
    p(f"Horas de control: {len(todas_c)}; por clase {cc}")
    p(f"tasa_control SI = {tasa_c:.4f}; SI+POSIBLE = {tasa_c_pos:.4f}")
    p(f"tasa_marcas  SI = {n_si / 30:.4f}; SI+POSIBLE = {n_si_pos / 30:.4f}")

    rng = random.Random(SEMILLA)

    def sorteo(acepta):
        dist = []
        for _ in range(N_SORTEOS):
            dist.append(sum(acepta(rng.choice(lista)) for lista in ctrl_por_marca))
        return dist

    dist_si = sorteo(lambda c: c == "SI")
    dist_sp = sorteo(lambda c: c in ("SI", "POSIBLE"))
    p_si = sum(d >= n_si for d in dist_si) / N_SORTEOS
    p_sp = sum(d >= n_si_pos for d in dist_sp) / N_SORTEOS
    k_min = next(k for k in range(31) if sum(d >= k for d in dist_si) / N_SORTEOS < 0.05)
    k_min_sp = next(k for k in range(31) if sum(d >= k for d in dist_sp) / N_SORTEOS < 0.05)
    p(f"Sorteo pareado ({N_SORTEOS}): media SI control = {sum(dist_si) / N_SORTEOS:.2f}/30, "
      f"p(SI >= {n_si}) = {p_si:.4f}; poder: hacen falta {k_min} SI para p < 0,05")
    p(f"  SI+POSIBLE: media {sum(dist_sp) / N_SORTEOS:.2f}/30, p(>= {n_si_pos}) = {p_sp:.4f}; "
      f"hacen falta {k_min_sp}")
    try:
        from scipy.stats import fisher_exact
        n_c_si = todas_c.count("SI")
        _, pf = fisher_exact([[n_si, 30 - n_si], [n_c_si, len(todas_c) - n_c_si]], alternative="greater")
        p(f"Fisher unilateral (referencia, supone horas independientes): p = {pf:.4f}")
    except ImportError:
        p("Fisher: scipy no disponible")

    # ---- veredicto, reglas del criterio ----
    cubiertas = len(marcas)  # el listado del SMN cubre todo el periodo (completitud arriba)
    if cubiertas < 24 or huecos:
        ver = "SIN DATO"
    elif n_si >= 10 and p_si < 0.05 and n_si_indep >= 5:
        ver = "COINCIDE CON FUENTE INDEPENDIENTE"
    elif n_si >= 10 and p_si < 0.05:
        ver = "COINCIDE SOLO POR SATELITE"
    else:
        ver = "NO COINCIDE"
    p(f"VEREDICTO: {ver}")

    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, filas in (("avisos.csv", filas_av), ("marcas.csv", filas_m), ("control.csv", filas_c)):
        with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
    (carpeta / "resumen.json").write_text(json.dumps({
        "marcas_por_clase_1h": cuenta, "marcas_por_clase_3h": c3, "n_si": n_si, "n_si_posible": n_si_pos,
        "n_si_indep_rmk": n_si_indep, "n_si_indep_lista": n_si_indep_l, "horas_control": len(todas_c),
        "control_por_clase": cc, "tasa_control_si": tasa_c, "tasa_control_si_posible": tasa_c_pos,
        "p_sorteo_si": p_si, "p_sorteo_si_posible": p_sp, "k_min_si": k_min, "k_min_si_posible": k_min_sp,
        "huecos_numeracion": huecos, "lector_regex_acuerdo": [acuerdo, total], "veredicto": ver,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    (carpeta / "analisis.log").write_text("\n".join(log) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
