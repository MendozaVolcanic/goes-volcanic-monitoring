# -*- coding: utf-8 -*-
"""H28: lee los logs de alertas de VOLCAT (geocatASHOBJ.*.A?_I?_H?_S?.log) de un
paquete de prueba de SSEC y saca tablas propias con los bloques donde VOLCAT
decide algo sobre un objeto de ceniza:

  plumas.csv      un renglon por "Processing plume" / "Processing spectral feature"
                  (candidato a grupo), con sus pruebas de contraste, sus conteos
                  (Time Trend Count, etc.) y el veredicto KEEPING / ELIMINATING.
  historia.csv    un renglon por objeto comparado contra la historia
                  (HISTORY_GROUP2OBJECT), con distancia, umbral, similitudes y si
                  se cumplio "Temporal selection criteria met".
  grupos.csv      un renglon por grupo clasificado (Group Index / History Index /
                  conteos / "Group classification").
  cuadros.csv     un renglon por cuadro: hora, archivos L1 temporales, numero de
                  alertas, de grupos validos sin alerta, MATCH de pluma por volcan.

No copia el log: guarda solo los numeros de los bloques de decision.

Uso:
  python -I h28_parse_logs.py <carpeta_logs> <carpeta_salida> <etiqueta> [hora_min hora_max]

hora_min y hora_max (HHMMSS, inclusive) dejan fuera los cuadros de prueba: los logs
que caen fuera del rango NO se abren.

Por que existe (SDA, Res. CPLT 372): H28 busca la regla con que VOLCAT publica un
objeto que su propio pixel no ve. Este script NO decide nada del dashboard; solo
ordena lo que el log de SSEC imprime para poder contarlo.
"""
import csv
import glob
import os
import re
import sys

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
BIG = 1e30  # los logs imprimen 3.4e38 (huge) como "sin dato"


def fnum(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    if abs(v) > BIG:
        return None
    return v


def kv_pairs(line):
    """'A: 1, B: 2.5' -> dict. Las claves pueden traer espacios y parentesis."""
    out = {}
    for m in re.finditer(r"([A-Za-z][A-Za-z0-9 /_\-\(\)\^=\+\.]*?):\s*(" + NUM + r"|NA)", line):
        out[m.group(1).strip()] = m.group(2)
    return out


def parse_log(path):
    name = os.path.basename(path)
    m = re.search(r"\.(\d{7})\.(\d{6})\.(A[YN]_I[YN]_H[YN]_S[YN])\.log$", name)
    frame = {"archivo": name, "dia": m.group(1), "hora": m.group(2), "sufijo": m.group(3)}
    plumas, historia, grupos, matches = [], [], [], []
    with open(path, "r", errors="replace") as fh:
        lines = [l.rstrip("\n") for l in fh]

    seccion = None      # 'strong' | 'weak' | None
    fase = ""           # ICE | ASH | HOT | SO2: ultimo "Assessing objects ... (X)"
    grouping_opt = None
    mode4_only = None
    cur_plume = None    # bloque de pluma / objeto espectral abierto
    cur_hist = None     # objeto de historia abierto
    last_group = None
    pendientes, indexables, clase = [], [], ""
    i = 0
    n = len(lines)
    while i < n:
        l = lines[i]
        s = l.strip()
        mf = re.search(r"Assessing objects (?:with|without) volcanoes \((\w+)\)", l)
        if mf:
            fase = mf.group(1)
        if "Looking for strong plumes" in l:
            seccion = "strong"
        elif "Looking for weak plumes" in l:
            seccion = "weak"
        elif "Assessing objects without volcanoes (ASH)" in l:
            seccion = None
        elif s.startswith("MATCH:") or s.startswith("NO MATCH:"):
            nums = re.findall(NUM, s)
            matches.append({"seccion": seccion, "match": int(s.startswith("MATCH:")),
                            "vol_idx": nums[0] if nums else "", "resto": " ".join(nums[1:])})
        elif s.startswith("Grouping Option:"):
            grouping_opt = s.split(":")[1].strip()
        elif s.startswith("Mode 4 Only:"):
            mode4_only = s.split(":")[1].strip()
        # ---------------- bloque de pluma / objeto espectral
        elif "OBJECT_GROUPING_CONTRAST_ASH" in l and ("Processing plume" in l or "Processing spectral feature" in l):
            cur_plume = {"fase": fase, "tipo": "plume" if "Processing plume" in l else "spectral",
                         "indice": l.rsplit(":", 1)[1].strip(), "grouping_opt": grouping_opt,
                         "mode4_only": mode4_only, "veredicto": "", "msgs": []}
            plumas.append(cur_plume)
        elif cur_plume is not None and s.startswith("****"):
            cur_plume = None
        elif cur_plume is not None:
            p = cur_plume
            if "BULK_SPECTRAL_CONTRAST" in l:
                p["bulk"] = "FAILED" if "FAILED" in l else ("PASSED" if "PASSED" in l else l.split(" : ")[-1][:60])
                if "does not have a sufficient nighttime NIR" in l:
                    p["sin_nir_noche"] = 1
            elif s.startswith("L1 Count:"):
                d = kv_pairs(s)
                for k in ("L1 Count", "L2 Count", "L3 Count", "L4 Count"):
                    p[k] = d.get(k)
            elif s.startswith("Mean SW (Group)"):
                v = re.findall(NUM, s)
                p["sw_grp"], p["sw_env"], p["sw_dif"], p["sw_flag"] = v[0], v[1], v[2], v[3]
            elif s.startswith("Mean 8511 (Group)"):
                v = re.findall(NUM, s.replace("8511", ""))
                p["b8511_grp"], p["b8511_env"], p["b8511_dif"], p["b8511_flag"] = v[0], v[1], v[2], v[3]
            elif re.match(r"Plume \d+ has a BT sdev", s):
                v = re.findall(NUM, s)
                p["vol_idx"], p["bt_sdev"], p["poly_pix"] = v[0], v[1], v[2]
            elif s.startswith("Min in-feature BTD"):
                v = re.findall(NUM, s)
                p["btd_in"], p["btd_in_n"] = v[0], v[1]
            elif s.startswith("Min out of feature BTD"):
                v = re.findall(NUM, s)
                p["btd_out"], p["btd_out_n"] = (v[0] if fnum(v[0]) is not None else ""), v[1]
            elif s.startswith("In-feature minus out of feature"):
                v = re.findall(NUM, s)
                p["btd_in_menos_out"] = v[0] if fnum(v[0]) is not None else ""
            elif s.startswith("Object with ID of") and "RGB1" in s:
                v = re.findall(NUM, s.replace("RGB1", ""))
                p["obj_pix_total"] = p.get("obj_pix_total", 0) + int(v[3])
                p["obj_ids"] = (p.get("obj_ids", "") + " " + v[0]).strip()
                p["_rgb"] = "rgb1"
            elif s.startswith("Object with ID of") and "RGB2" in s:
                p["_rgb"] = "rgb2"
            elif s.startswith("Min Dist (avg)"):
                v = re.findall(NUM, s)
                k = p.get("_rgb", "rgb1")
                p[k + "_mindist_avg"] = (p.get(k + "_mindist_avg", "") + " " + v[0]).strip()
                p[k + "_mindist_max"] = (p.get(k + "_mindist_max", "") + " " + v[1]).strip()
                p[k + "_swfrac"] = (p.get(k + "_swfrac", "") + " " + v[3]).strip()
            elif re.match(r"Plume \d+ is composed of", s):
                v = re.findall(NUM, s)
                k = "rgb1" if "RGB1" in s else "rgb2"
                p[k + "_fallan"], p[k + "_de"] = v[1], v[2]
            elif s.startswith("Feature PASSED") or s.startswith("Feature FAILED"):
                ok = "PASSED" if "PASSED" in s else "FAILED"
                if "without distance check" in s:
                    p["contraste_sin_dist"] = ok
                elif "with distance check" in s:
                    p["contraste_con_dist"] = ok
                elif "cloud noise" in s:
                    p["ruido_nube"] = ok
                else:
                    p["msgs"].append(s)
            elif "OBJECT_GROUPING_CONTRAST_ASH" in l:
                msg = l.split(" : ", 1)[1].strip()
                if msg.startswith("KEEPING") or msg.startswith("ELIMINATING"):
                    p["veredicto"] = msg.split()[0]
                    p["veredicto_txt"] = msg
                else:
                    p["msgs"].append(msg)
            elif re.match(r"Group Idx\s", s):
                p["group_idx_linea"] = " ".join(s.split()[2:])
            elif ":" in s:
                d = kv_pairs(s)
                for k, v in d.items():
                    p[k] = v
        # ---------------- historia: objeto contra grupo historico
        elif s.startswith("VOLCAT_HISTORY_UTILS:HISTORY_GROUP2OBJECT>>"):
            d = kv_pairs(s.split(">>", 1)[1])
            cur_hist = {"fase": fase, "Obj Id": d.get("Obj Id"), "Selection Opt": d.get("Selection Opt"),
                        "Explosive Frac": d.get("Explosive Frac"), "Area": d.get("Area(km^2)"),
                        "Count": d.get("Count"), "Kd Group": d.get("Kd Group"),
                        "criterio_cumplido": 0, "rama": "", "seleccionado": 0}
            historia.append(cur_hist)
        elif cur_hist is not None and s.startswith("Hist Idx:"):
            d = kv_pairs(s)
            # puede haber varias lineas Hist Idx (un objeto contra varios grupos): guardar la de menor distancia
            dist = fnum(d.get("Dist(km)"))
            prev = fnum(cur_hist.get("Dist(km)"))
            cur_hist["n_hist"] = cur_hist.get("n_hist", 0) + 1
            if prev is None or (dist is not None and dist < prev):
                cur_hist["Hist Idx"] = d.get("Hist Idx")
                cur_hist["Time diff(s)"] = d.get("Time diff(s)")
                cur_hist["Dist(km)"] = d.get("Dist(km)")
                cur_hist["Dist Thresh(km)"] = d.get("Dist Thresh(km)")
                cur_hist["Inside Polygon"] = d.get("Inside Polygon (0=NO)")
        elif cur_hist is not None and re.match(r"\d+>>", s):
            rama = s.split(">>")[0]
            d = kv_pairs(s.split(">>", 1)[1])
            cur_hist["rama"] = (cur_hist["rama"] + "," + rama).strip(",")
            for k in ("Refined Dist(km)", "Refined Dist Threshold(km)", "Out of Range Count",
                      "Area Hist(km^2)", "Group Id", "Overlap Frac", "Emiss Sim", "Reff Sim", "Beta85 Sim"):
                if k in d:
                    v = d[k]
                    cur_hist[k] = v if fnum(v) is not None else ""
            if "Selection Opt" in d:
                cur_hist["Selection Opt (rama)"] = d["Selection Opt"]
        elif s.startswith("Temporal selection criteria met"):
            if cur_hist is not None:
                cur_hist["criterio_cumplido"] = 1
                cur_hist["criterio_txt"] = s
                cur_hist["criterio_tipo"] = s.split(" for ")[1].split()[0] if " for " in s else ""
        elif s.startswith("***SELECTED object"):
            oid = re.findall(r"\d+", s)
            for h in historia:
                if oid and h.get("Obj Id") == oid[0]:
                    h["seleccionado"] = 1
        elif s.startswith("Obj:") and "Kd ct" in s:
            d = kv_pairs(s)
            for h in historia:
                if h.get("Obj Id") == d.get("Obj"):
                    for k in ("Kd frac", "NN Pix Dist", "Thresh", "Poly frac (orig)", "Poly frac (new)",
                              "Poly frac ratio", "Area frac"):
                        if k in d:
                            h["filtro " + k] = d[k]
        # ---------------- grupos y clasificacion
        elif "IDENTIFY_ALERT_OBJECTS" in l and "Classifying" in l:
            # los bloques ORGANIZE_GROUP_OUTPUT que vienen ANTES de esta linea son de este tipo
            # (ash, ice, ...). Sin esto, el grupo de hielo 1 pisaba al grupo de ceniza 1.
            clase = l.rsplit("Classifying", 1)[1].split()[0]
            for g_ in pendientes:
                g_["tipo"] = clase
            indexables = pendientes
            pendientes = []
        elif "ORGANIZE_GROUP_OUTPUT" in l and "coherent BTD tendency" in l:
            v = re.findall(NUM, l.split(" : ", 1)[1])
            last_group = {"tipo": "", "btd_tend_n": v[0], "pix": v[1]}
            grupos.append(last_group)
            pendientes.append(last_group)
        elif "ORGANIZE_GROUP_OUTPUT" in l and "within previously detected feature" in l and last_group is not None:
            v = re.findall(NUM, l.split(" : ", 1)[1])
            last_group["en_rasgo_previo_n"] = v[0]
        elif "ORGANIZE_GROUP_OUTPUT" in l and "Tracking feature with area" in l and last_group is not None:
            v = re.findall(NUM, l.split(" : ", 1)[1].replace("km^2", ""))
            last_group["area_km2"], last_group["hist_method"], last_group["cur_method"] = v[0], v[1], v[2]
        elif s.startswith("Group Index:"):
            d = kv_pairs(s)
            gi = int(d.get("Group Index", "0"))
            if 0 < gi <= len(indexables):
                g = indexables[gi - 1]
            else:
                g = {"tipo": clase}
                grupos.append(g)
            g["Group Index"] = d.get("Group Index")
            g["History Index"] = d.get("History Index")
            g["Time Diff(s)"] = d.get("Time Diff(s)")
            last_group = g
        elif s.startswith("Always Alert Flag:") and last_group is not None:
            d = kv_pairs(s)
            for k in ("Always Alert Flag", "Missing History Count", "Time Trend Count", "K-d Overlap Count"):
                last_group["cl " + k] = d.get(k)
        elif s.startswith("Group classification:") and last_group is not None:
            last_group["clasificacion"] = s.split(":", 1)[1].strip()
        elif s.startswith("Feature is missing from current image") or s.startswith("Feature is likely mostly present"):
            frame.setdefault("historia_faltante", []).append(s)
        elif s.startswith("Xmin:"):
            d = kv_pairs(s)
            frame.setdefault("historia_faltante", []).append(
                "Pixel Count=%s Missing Count=%s Missing Frac=%s" % (d.get("Pixel Count"), d.get("Missing Count"), d.get("Missing Frac")))
        elif s.startswith("Number of missing features"):
            frame["n_rasgos_faltantes"] = s.rsplit(":", 1)[1].strip()
        elif s.startswith("STARTING DATE/TIME OF IMAGE:"):
            frame["inicio_imagen"] = s.split(":", 1)[1].replace("[UTC]", "").strip()
        elif s.startswith("L1 FILE(S) - TEMPORAL:"):
            frame["n_l1_temporales"] = len([x for x in s.split(":", 1)[1].split(",") if x.strip()])
        elif s.startswith("NUMBER OF ASH CLOUD ALERTS:"):
            frame["alertas_ceniza"] = s.rsplit(":", 1)[1].strip()
        elif s.startswith("NUMBER OF Cb ALERTS:"):
            frame["alertas_cb"] = s.rsplit(":", 1)[1].strip()
        elif s.startswith("NUMBER OF VALID NON-ALERT ASH GROUPS:"):
            frame["grupos_ceniza_sin_alerta"] = s.rsplit(":", 1)[1].strip()
        elif s.startswith("NUMBER OF VALID NON-ALERT VOLCANIC CB GROUPS:"):
            frame["grupos_cb_sin_alerta"] = s.rsplit(":", 1)[1].strip()
        elif s.startswith("Alert Status:"):
            frame.setdefault("alert_status", []).append(s.split(":", 1)[1].strip())
        elif s.startswith("Identification Method:"):
            frame.setdefault("metodo", []).append(s.split(":", 1)[1].strip())
        elif s.startswith("Median Probability of Pixels:"):
            frame.setdefault("prob_mediana_pct", []).append(re.findall(NUM, s)[0])
        elif s.startswith("Total Area:"):
            frame.setdefault("area_alerta_km2", []).append(re.findall(NUM, s)[0])
        elif s.startswith("Creating history file") or "Creating history file" in s:
            frame["crea_historia"] = 1
        i += 1

    frame["match_plumas"] = ";".join("%s:%s:%s:%s" % (m_["seccion"], "M" if m_["match"] else "N", m_["vol_idx"], m_["resto"]) for m_ in matches)
    for k in ("alert_status", "metodo", "prob_mediana_pct", "area_alerta_km2", "historia_faltante"):
        if k in frame:
            frame[k] = " | ".join(frame[k])
    for p in plumas:
        p["msgs"] = " | ".join(p["msgs"])
        p.pop("_rgb", None)
    return frame, plumas, historia, grupos


def write_csv(path, rows, first):
    keys = list(first)
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    logdir, outdir, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(logdir, "geocatASHOBJ.*.A?_I?_H?_S?.log")))
    if len(sys.argv) >= 6:
        lo, hi = sys.argv[4], sys.argv[5]
        files = [f for f in files if lo <= re.search(r"\.(\d{6})\.A[YN]_", os.path.basename(f)).group(1) <= hi]
    cuadros, P, H, G = [], [], [], []
    for f in files:
        fr, pl, hi, gr = parse_log(f)
        cuadros.append(fr)
        for rows, acc in ((pl, P), (hi, H), (gr, G)):
            for j, r in enumerate(rows):
                r2 = {"caso": tag, "hora": fr["hora"], "n": j + 1}
                r2.update(r)
                acc.append(r2)
        fr["n_plumas"] = len(pl)
        fr["n_hist_obj"] = len(hi)
        fr["n_grupos"] = len(gr)
        fr["caso"] = tag
    write_csv(os.path.join(outdir, tag + "_cuadros.csv"), cuadros, ["caso", "dia", "hora", "sufijo", "inicio_imagen"])
    write_csv(os.path.join(outdir, tag + "_plumas.csv"), P, ["caso", "hora", "n", "tipo", "veredicto"])
    write_csv(os.path.join(outdir, tag + "_historia.csv"), H, ["caso", "hora", "n", "Obj Id", "criterio_cumplido", "seleccionado"])
    write_csv(os.path.join(outdir, tag + "_grupos.csv"), G, ["caso", "hora", "n", "clasificacion"])
    print(tag, "cuadros", len(cuadros), "plumas", len(P), "historia", len(H), "grupos", len(G))


if __name__ == "__main__":
    main()
