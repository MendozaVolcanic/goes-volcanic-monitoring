"""Replay por fecha: cualquier volcan, cualquier dia que RAMMB conserve.

Para que sirve: revisar despues lo que mostro GOES-19 sobre un volcan en un
dia y una ventana horaria elegidos (por ejemplo, el SO2 de Lastarria del
14-11-2026), recorriendo los scans de a uno.

Como lista los scans (nov-2026): pide a RAMMB `<fecha>_by_hour.json` del dia
elegido, NO "los ultimos N". `latest_times.json` corta en 100 scans (unas
16 h), asi que la version anterior, que pedia 200 y prometia 28 dias, en
realidad cubria menos de un dia.

Cuanto conserva RAMMB (medido el 15-11-2026 para jma_so2, eumetsat_ash y
geocolor): un tramo continuo reciente (desde 01-09-2026, 76 dias) y, antes,
dias sueltos hasta jul-2025, algunos de los cuales ya no tienen imagenes
aunque sigan en la lista. La vista calcula ese limite en cada visita desde
`available_dates.json` y lo dice en pantalla; un dia que no esta se informa
como tal y nunca se reemplaza por otro.

Cuatro productos y reproduccion (15-11-2026): GeoColor, Ash RGB, SO2 y
VOLCAT del MISMO scan, lado a lado, para comparar contra una anomalia vista
en otro visor. El dia se puede reproducir entero: se baja una vez y la
animacion corre en el navegador (`dashboard/replay_dia.py`). Un producto sin
imagen en un scan queda vacio y dice por que; nunca toma el scan vecino.

No decide nada: muestra imagenes RAMMB y SSEC ya publicadas. La lectura (hay
pluma, es ceniza, es SO2, que altura) queda al geologo de turno.
"""

import logging
import time
from datetime import date, datetime, timedelta, timezone

import streamlit as st

try:
    from dashboard.style import header
    from dashboard.utils import CHILE_TZ, utc_to_chile
    from dashboard.replay_dia import (
        PANELES, PANELES_RAMMB, ROTULOS, emparejar, figura_dia,
        linea_de_tiempo, rotulo_slot, volcat_por_slot,
    )
    from src.fetch.rammb_slider import (
        fetch_frame_robust, zoom_reducido, ZOOM_VOLCAN, ZOOM_ZONE,
    )
    from src.volcanos import CATALOG, get_volcano
    # Listado por fecha (nov-2026): los scans salen del dia elegido, no de
    # `latest_times.json` (corta en 100). Los tiles pasan por el cache de
    # rammb_slider, tambien los de la sonda `tile_available`.
    from src.fetch.historic_rammb import (
        ESTADO_NO_CONSERVADO, ESTADO_PARCIAL, ESTADO_SIN_RESPUESTA,
        archive_span, fetch_available_dates, list_local_day,
        local_window_utc, tile_available,
    )
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

# Sugerencias, no la lista: volcanes con actividad frecuente donde casi
# siempre hay algo que ver. Van primero en el selector; el resto del catalogo
# viene despues.
ACTIVE_VOLCANOES = [
    {"name": "Sangay (Ecuador)", "rationale": "Actividad casi continua. Hot spots diarios."},
    {"name": "Reventador (Ecuador)", "rationale": "Explosiones diarias. Pluma frecuente."},
    {"name": "Sabancaya (Perú)", "rationale": "1-3 explosiones/día documentadas."},
    {"name": "Villarrica", "rationale": "Lago de lava activo. Hot spots térmicos."},
    {"name": "Lascar", "rationale": "Hot spots térmicos esporádicos."},
    {"name": "Copahue", "rationale": "Emisión sostenida de SO2."},
]

# Rotulos de los productos (los 4 se muestran juntos; ya no se elige uno).
PRODUCTS = ROTULOS

# Velocidades de reproduccion (cuadros por segundo). A 4 cuadros/s un dia de
# 144 scans dura 36 s.
VELOCIDADES = [1, 2, 4, 8, 12]

# Descargas en paralelo al cargar el dia: RAMMB entrega tiles chicos (24
# cuadros en ~5 s con 8 hilos, medido 15-11-2026); SSEC es un servidor
# universitario, por eso no mas que esto.
_HILOS = 8

# VOLCAT viene a 2 km por pixel: en un encuadre de 0,4 grados son ~45 pixeles.
# Se agranda con vecino mas cercano (cada color es una altura de la escala y
# un filtro suave inventaria alturas intermedias).
_ESCALA_VOLCAT = 4

# VOLCAT es lo caro de reproducir un dia: SSEC entrega el sector entero
# (Chile_North_2_km son ~0,55 MB por cuadro, medido 15-11-2026) aunque el
# encuadre sea de 0,4 grados. Con 8 hilos y una conexion lenta, el dia de
# Lastarria iba en 176 de 559 imagenes a los 8 min. Por eso la reproduccion
# baja primero GeoColor, Ash y SO2 (unos KB cada uno) y VOLCAT se agrega
# aparte, con el costo a la vista.
_MB_POR_CUADRO_VOLCAT = 0.55
_VOLCAT_SIN_CARGAR = "VOLCAT no cargado: usa «Agregar VOLCAT»"

# Canonical en src/config (REPLAY_RADIUS_DEG). Fallback hardcoded por
# si Streamlit Cloud falla el import durante hot-reload (gotcha CLAUDE.md).
try:
    from src.config import REPLAY_RADIUS_DEG as RADIUS_DEG
except Exception:
    RADIUS_DEG = 0.4  # ver src/config.py

# Radios ofrecidos (grados). 0.4 es el encuadre historico de la vista; 3
# grados alcanza para seguir una pluma larga.
RADIOS_DEG = [0.25, 0.4, 0.75, 1.0, 1.5, 2.0, 3.0]


def volcan_options() -> list[tuple[str, str]]:
    """(nombre, rotulo) para el selector: sugeridos primero, luego el resto
    del catalogo en su orden. Todos los volcanes del catalogo estan."""
    nombres = {v.name for v in CATALOG}
    out = [(a["name"], f"★ {a['name']}: {a['rationale']}")
           for a in ACTIVE_VOLCANOES if a["name"] in nombres]
    vistos = {n for n, _ in out}
    out += [(v.name, v.name) for v in CATALOG if v.name not in vistos]
    return out


# ── Datos (cache) ────────────────────────────────────────────────────
# Lo que se lista de un dia pasado no cambia; el dia de hoy si (entra un scan
# cada 10 min), por eso el TTL es corto igual.

@st.cache_data(ttl=3600, show_spinner=False)
def _fechas_listadas(product: str):
    return fetch_available_dates(product)


@st.cache_data(ttl=300, show_spinner=False)
def _scans_del_dia(product: str, dia: date, h_ini: int, h_fin: int):
    return list_local_day(product, dia, h_ini, h_fin, CHILE_TZ)


@st.cache_data(ttl=3600, show_spinner=False)
def _hay_imagenes(product: str, ts: str, bounds_key: tuple):
    lat_min, lat_max, lon_min, lon_max = bounds_key
    return tile_available(product, ts, {"lat_min": lat_min, "lat_max": lat_max,
                                        "lon_min": lon_min, "lon_max": lon_max})


def _texto_archivo(span: dict | None) -> str:
    """Limite real del archivo RAMMB, en palabras."""
    if span is None:
        return ("No se pudo leer la lista de días de RAMMB: no se sabe hasta "
                "dónde llega el archivo. Igual puedes pedir un día.")
    txt = (f"RAMMB conserva **continuo desde el "
           f"{span['continuo_desde']:%d-%m-%Y}** "
           f"({span['dias_continuos']} días, hasta el "
           f"{span['continuo_hasta']:%d-%m-%Y}).")
    if span["sueltos"]:
        tramos = ", ".join(
            f"{a:%d-%m-%Y}" if a == b else f"{a:%d-%m-%Y} a {b:%d-%m-%Y}"
            for a, b in span["sueltos"])
        txt += (f" Antes, solo días sueltos ({tramos}); algunos siguen en la "
                f"lista pero ya no tienen imágenes.")
    return txt


def _mover(key: str, paso: int, n: int):
    """Callback de ◀ ▶: corre el cuadro elegido sin salir de la ventana."""
    st.session_state[key] = min(max(st.session_state.get(key, 0) + paso, 0),
                                n - 1)


@st.cache_data(ttl=300, show_spinner=False)
def _volcat_del_dia(sector: str, instr: str, ini_iso: str, fin_iso: str):
    """Cuadros VOLCAT de la ventana. La lista de SSEC trae ~30 dias y pesa
    ~1 MB: no se pide en cada rerun."""
    from src.fetch.volcat_api import volcat_cuadros_entre
    return volcat_cuadros_entre(sector, instr, datetime.fromisoformat(ini_iso),
                                datetime.fromisoformat(fin_iso))


def _imagen_volcat(meta: dict, bounds: dict):
    """Recorte del cuadro VOLCAT al encuadre, agrandado sin mezclar colores.
    None si SSEC no lo entrego."""
    import numpy as np

    from dashboard.views.volcat_viewer import _volcat_map_only
    from dashboard.volcat_loop import escalar_mapa, recortar_encuadre
    geo = _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                           meta.get("coords") or {})
    if not (geo and geo.get("png")):
        return None
    rec = recortar_encuadre(geo["png"], geo["bounds"], bounds)
    if rec is None:
        return None
    w, h = rec.size
    return np.asarray(escalar_mapa(rec, w * _ESCALA_VOLCAT,
                                   h * _ESCALA_VOLCAT))


def _barra_volcat(meta: dict | None):
    """Escala de altura de VOLCAT (la quemada por SSEC), o None."""
    if meta is None:
        return None
    try:
        import io

        import numpy as np
        from PIL import Image

        from dashboard.views.volcat_viewer import (
            _volcat_colorbar_split_vertical)
        _bt, ht = _volcat_colorbar_split_vertical(meta["image_url"])
        if not ht:
            return None
        return np.asarray(Image.open(io.BytesIO(ht)).convert("RGB"))
    except Exception:
        logger.warning("Replay: sin escala VOLCAT", exc_info=True)
        return None


def _texto_progreso(n: int, total: int, segundos: float) -> str:
    """'Bajando imágenes: 56 de 423 · faltan ~11 min'. El ritmo sale de lo
    ya bajado: depende de la conexion y de RAMMB, no de una cifra fija."""
    txt = f"Bajando imágenes: {n} de {total}"
    if 0 < n < total and segundos > 0:
        faltan = (total - n) * segundos / n
        txt += (f" · faltan ~{faltan / 60:.0f} min" if faltan >= 90
                else f" · faltan ~{faltan:.0f} s")
    return txt


def _cargar_cuadros(slots, par, vmatch, bounds, notas, nota_volcat,
                    progreso=None, productos=PANELES,
                    base: list[dict] | None = None) -> list[dict]:
    """Baja `productos` de cada slot. Lo que falta queda None con su motivo:
    no se rellena con el scan vecino.

    Con `base` completa cuadros ya cargados (se usa para agregar VOLCAT
    despues de los tres de RAMMB sin volver a bajarlos)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if base is not None:
        cuadros = {c["slot"]: c for c in base}
    else:
        cuadros = {s: {"slot": s, "imgs": {pid: None for pid in PANELES},
                       "motivos": {}} for s in slots}
    if "volcat" not in productos:
        # "No cargado" solo donde SSEC SI tiene cuadro; donde no lo tiene se
        # dice eso, que es otra cosa.
        for s in slots:
            if base is None or cuadros[s]["imgs"].get("volcat") is None:
                cuadros[s]["motivos"]["volcat"] = (
                    _VOLCAT_SIN_CARGAR if vmatch.get(s) is not None
                    else (nota_volcat or "SSEC no publicó este cuadro"))
    tareas = {}

    def _rammb(prod, ts):
        img, _used, zoom = fetch_frame_robust(
            prod, [ts], bounds, zoom_preferred=ZOOM_VOLCAN,
            zoom_fallback=ZOOM_ZONE)
        return img, zoom

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=_HILOS) as ex:
        for s in slots:
            for prod in PANELES_RAMMB:
                if prod not in productos:
                    continue
                ts = par[s].get(prod)
                if ts is None:
                    cuadros[s]["motivos"][prod] = (
                        notas.get(prod) or "RAMMB no publicó este scan")
                else:
                    tareas[ex.submit(_rammb, prod, ts)] = (s, prod)
            if "volcat" not in productos:
                continue
            cuadros[s]["motivos"].pop("volcat", None)
            meta = vmatch.get(s)
            if meta is None:
                cuadros[s]["motivos"]["volcat"] = (
                    nota_volcat or "SSEC no publicó este cuadro")
            else:
                tareas[ex.submit(_imagen_volcat, meta, bounds)] = (s, "volcat")
        total = max(len(tareas), 1)
        for n, fut in enumerate(as_completed(tareas), start=1):
            s, pid = tareas[fut]
            try:
                res = fut.result()
            except Exception:
                logger.warning("Replay: fallo %s %s", pid, s, exc_info=True)
                res = (None, None) if pid != "volcat" else None
            if pid == "volcat":
                img = res
                if img is None:
                    cuadros[s]["motivos"][pid] = "no se pudo bajar de SSEC"
            else:
                img, zoom = res
                if img is None:
                    cuadros[s]["motivos"][pid] = "RAMMB no entregó la imagen"
                elif zoom_reducido(pid, zoom, ZOOM_VOLCAN):
                    # Solo si vino mas grueso de lo que el producto publica
                    # (Ash y SO2 topan en zoom 3: eso no es una degradacion).
                    cuadros[s]["motivos"][pid] = "⚠ zoom 3"
            cuadros[s]["imgs"][pid] = img
            if progreso is not None and (n % 8 == 0 or n == total):
                progreso.progress(n / total, text=_texto_progreso(
                    n, total, time.monotonic() - t0))
    return [cuadros[s] for s in slots]


def render():
    from dashboard.manuals import render_manual
    render_manual("replay")
    header(
        "🔁 Replay por fecha: actividad real GOES-19",
        "GeoColor, Ash RGB, SO2 y VOLCAT del mismo scan, para cualquier "
        "volcán y día que RAMMB conserve",
    )

    # ── Selectores ──
    opciones = volcan_options()
    rotulos = dict(opciones)
    c1, c3 = st.columns([2.6, 1.2])
    with c1:
        volcan_name = st.selectbox(
            "Volcán", [n for n, _ in opciones],
            format_func=lambda n: rotulos[n],
            index=0, key="replay_volcan_nombre",
            help="★ = sugerencias con actividad frecuente. Más abajo está "
                 "todo el catálogo.",
        )
    with c3:
        radio = st.select_slider(
            "Radio (grados)", options=RADIOS_DEG, value=RADIUS_DEG,
            format_func=lambda r: f"{r:g}° (~{r * 111:.0f} km)",
            key="replay_radio",
        )

    hoy_chile = utc_to_chile(datetime.now(timezone.utc)).date()
    # Los tres productos RAMMB listan los mismos dias (medido 15-11-2026);
    # el limite que se muestra sale del SO2.
    fechas = _fechas_listadas("jma_so2")
    span = archive_span(fechas) if fechas else None
    # El calendario parte en el dia listado mas viejo; dias del medio que no
    # esten se avisan al elegirlos. Sin lista, se deja un año hacia atras.
    minimo = fechas[0] if fechas else hoy_chile - timedelta(days=365)

    d1, d2 = st.columns([1.2, 2.2])
    with d1:
        dia = st.date_input(
            "Día (hora de Chile)", value=hoy_chile,
            min_value=minimo, max_value=hoy_chile,
            format="DD-MM-YYYY", key="replay_dia",
        )
    with d2:
        h_ini, h_fin = st.slider(
            "Ventana horaria (hora de Chile)", 0, 24, (0, 24),
            format="%d:00", key="replay_ventana",
        )
    if h_fin <= h_ini:
        st.warning("La ventana horaria está vacía: elige un fin mayor que el inicio.")
        return

    ini_utc, fin_utc = local_window_utc(dia, h_ini, h_fin, CHILE_TZ)
    st.caption(
        f"{dia:%d-%m-%Y} de {h_ini:02d}:00 a {h_fin:02d}:00 hora de Chile = "
        f"{ini_utc:%d-%m %H:%M} a {fin_utc:%d-%m %H:%M} UTC. "
        + _texto_archivo(span)
    )

    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcán {volcan_name} no encontrado en catálogo.")
        return
    bounds = {
        "lat_min": v.lat - radio, "lat_max": v.lat + radio,
        "lon_min": v.lon - radio, "lon_max": v.lon + radio,
    }
    bkey = (bounds["lat_min"], bounds["lat_max"],
            bounds["lon_min"], bounds["lon_max"])

    # ── Scans del dia, producto por producto ──
    # Cada producto se lista aparte: RAMMB puede tener un dia para Ash y no
    # para SO2, y un hueco de uno no borra a los otros.
    listas, notas, avisos = {}, {}, []
    with st.spinner("Pidiendo a RAMMB los scans de ese día…"):
        for prod in PANELES_RAMMB:
            ts, estado = _scans_del_dia(prod, dia, h_ini, h_fin)
            if estado == ESTADO_SIN_RESPUESTA:
                notas[prod] = "RAMMB no respondió"
                continue
            if estado == ESTADO_NO_CONSERVADO:
                notas[prod] = "RAMMB no conserva este día"
                continue
            if not ts:
                notas[prod] = "sin scans en la ventana"
                continue
            # La lista de RAMMB trae dias cuyas imagenes ya se borraron: se
            # prueba un tile del encuadre antes de ofrecerlos (medido nov-2026).
            hay = _hay_imagenes(prod, ts[len(ts) // 2], bkey)
            if hay is False:
                notas[prod] = "RAMMB ya borró las imágenes de este día"
                continue
            if hay is None:
                avisos.append(f"No se pudo confirmar que RAMMB tenga las "
                              f"imágenes de {ROTULOS[prod]} (sin respuesta); "
                              f"se intenta igual.")
            if estado == ESTADO_PARCIAL:
                avisos.append(f"Una parte del día no respondió en RAMMB para "
                              f"{ROTULOS[prod]}: pueden faltar scans (no es "
                              f"que no los haya).")
            listas[prod] = ts

    if not listas:
        detalle = "; ".join(f"{ROTULOS[p]}: {n}" for p, n in notas.items())
        if all(n == "RAMMB no respondió" for n in notas.values()):
            st.error("RAMMB no respondió: no se sabe si ese día existe. "
                     "Prueba de nuevo en unos segundos.")
        else:
            st.error(f"No hay imágenes RAMMB del {dia:%d-%m-%Y} en esa "
                     f"ventana ({detalle}). No se muestra otro día en su "
                     f"lugar. " + _texto_archivo(span))
        return
    for a in avisos:
        st.warning(a)

    slots = linea_de_tiempo(listas)
    par = emparejar({p: listas.get(p, []) for p in PANELES_RAMMB}, slots)

    # ── VOLCAT de la misma ventana ──
    from src.fetch.volcat_api import resolve_volcat_sector
    from dashboard.views.modo_guardia_volcan import etiqueta_sector_volcat
    sector, instr = resolve_volcat_sector(v)
    vres = _volcat_del_dia(sector, instr, ini_utc.isoformat(),
                           fin_utc.isoformat())
    nota_volcat = None
    if not vres["ok"]:
        nota_volcat = "SSEC no respondió"
    elif vres["desde"] is not None and fin_utc <= vres["desde"]:
        nota_volcat = (f"SSEC conserva VOLCAT desde el "
                       f"{utc_to_chile(vres['desde']):%d-%m-%Y}")
    vmatch = volcat_por_slot(vres["frames"], slots)

    cuentas = [f"{ROTULOS[p]} {len(listas.get(p, []))}" for p in PANELES_RAMMB]
    cuentas.append(f"VOLCAT {sum(m is not None for m in vmatch.values())}")
    st.success(f"📡 {len(slots)} scans en la ventana ({rotulo_slot(slots[0])} "
               f"a {rotulo_slot(slots[-1])}). Imágenes por producto: "
               + " · ".join(cuentas) + ".")
    if nota_volcat:
        st.warning(f"VOLCAT: {nota_volcat}. Sin VOLCAT no se sabe la altura; "
                   f"los otros tres productos se muestran igual.")

    # ── Leyendas, en el orden de los paneles ──
    from dashboard.map_helpers import render_compact_legend
    cols = st.columns(len(PANELES))
    for col, pid in zip(cols, PANELES):
        with col:
            render_compact_legend(pid, symbols=("volcano",), height_px=30)

    modo = st.radio("Modo", ["▶ Reproducir el día", "Cuadro a cuadro"],
                    horizontal=True, key="replay_modo",
                    label_visibility="collapsed")
    regla = st.toggle(
        "📏 Regla", value=False, key="replay_regla",
        help="Arrastra sobre cualquiera de los cuatro paneles para medir en "
             "km. No corrige el paralaje: una pluma alta aparece corrida "
             "hacia el sur (0,4 a 1,5 km por km de altura).",
    )
    meta_barra = next((m for m in vmatch.values() if m is not None), None)

    if modo == "Cuadro a cuadro":
        # La key lleva dia y ventana: con otra lista de scans el indice
        # guardado no significa lo mismo y se vuelve al primer cuadro.
        n = len(slots)
        key = f"replay_idx_{dia:%Y%m%d}_{h_ini}_{h_fin}"
        if st.session_state.get(key, 0) >= n:
            st.session_state[key] = 0
        b1, s, b2 = st.columns([0.6, 8, 0.6])
        with b1:
            st.button("◀", key=f"{key}_ant", on_click=_mover,
                      args=(key, -1, n), help="Scan anterior", width="stretch")
        with b2:
            st.button("▶", key=f"{key}_sig", on_click=_mover,
                      args=(key, 1, n), help="Scan siguiente", width="stretch")
        with s:
            idx = st.select_slider(
                "Scan (mueve el slider o usa ◀ ▶)", options=list(range(n)),
                format_func=lambda i: rotulo_slot(slots[i]),
                key=key, label_visibility="collapsed",
            )
        cuadros = _cargar_cuadros([slots[idx]], par, vmatch, bounds, notas,
                                  nota_volcat)
        ms = 250
    else:
        fps = st.select_slider(
            "Velocidad (cuadros por segundo)", options=VELOCIDADES, value=4,
            key="replay_fps",
            help=f"A 4 cuadros/s los {len(slots)} scans duran "
                 f"{len(slots) / 4:.0f} s.",
        )
        ms = int(1000 / fps)
        clave = (v.name, radio, dia.isoformat(), h_ini, h_fin)
        guardado = st.session_state.get("replay_dia_cuadros")
        n_volcat = sum(m is not None for m in vmatch.values())
        mb_volcat = n_volcat * _MB_POR_CUADRO_VOLCAT
        if guardado is None or guardado["clave"] != clave:
            st.info(
                f"Para reproducir se bajan una vez los {len(slots)} scans de "
                f"GeoColor, Ash RGB y SO2. RAMMB entrega tiles enteros (uno "
                f"por producto y scan, de hasta ~0,7 MB), así que un día "
                f"completo son unos cientos de MB: con buena conexión es "
                f"cerca de un minuto, con una lenta pueden ser varios (el "
                f"progreso dice cuánto falta). Si buscas una hora puntual, "
                f"achica la ventana horaria. VOLCAT se agrega después con su "
                f"propio botón: ~{_MB_POR_CUADRO_VOLCAT:g} MB por cuadro, "
                f"~{mb_volcat:.0f} MB para esta ventana. Ya cargado, la "
                f"reproducción corre en tu navegador.")
            if not st.button(f"⬇ Cargar {len(slots)} scans y reproducir",
                             type="primary", key="replay_cargar"):
                return
            barra = st.progress(0.0, text="Bajando imágenes…")
            cuadros = _cargar_cuadros(slots, par, vmatch, bounds, notas,
                                      nota_volcat, progreso=barra,
                                      productos=PANELES_RAMMB)
            barra.empty()
            # Un solo dia en memoria: otro dia reemplaza al anterior.
            guardado = {"clave": clave, "cuadros": cuadros,
                        "con_volcat": False}
            st.session_state["replay_dia_cuadros"] = guardado
        cuadros = guardado["cuadros"]
        if not guardado["con_volcat"] and n_volcat:
            if st.button(f"➕ Agregar VOLCAT ({n_volcat} cuadros, "
                         f"~{mb_volcat:.0f} MB)", key="replay_volcat"):
                barra = st.progress(0.0, text="Bajando cuadros VOLCAT…")
                cuadros = _cargar_cuadros(slots, par, vmatch, bounds, notas,
                                          nota_volcat, progreso=barra,
                                          productos=("volcat",), base=cuadros)
                barra.empty()
                guardado.update(cuadros=cuadros, con_volcat=True)

    fig = figura_dia(cuadros, v.lat, v.lon, bounds, ms_por_cuadro=ms,
                     regla=regla, titulo=v.name,
                     barra_volcat=_barra_volcat(meta_barra))
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": regla, "displaylogo": False})

    st.caption(
        f"VOLCAT: sector **{etiqueta_sector_volcat(sector)}**; sin dibujo = "
        f"VOLCAT no detecta ceniza en ese cuadro, no es una falla. Un panel "
        f"vacío dice por qué no hay imagen; nunca se rellena con el scan de al "
        f"lado. Para hot spots o un loop descargable de ese momento, abre Modo "
        f"Evento o Loops."
    )

    with st.expander("📚 Calbuco 2015: caso histórico (sin datos disponibles)"):
        st.markdown(
            "Calbuco 22-Apr-2015 21:04 UTC sigue siendo el evento canónico "
            "para validar **Wen-Rose 1994** (~21 km confirmado por radiosonda). "
            "Pero como GOES-13 archive no está en RAMMB, no podemos hacer "
            "replay con los productos actuales del dashboard.\n\n"
            "**Para usarlo en el futuro** necesitamos:\n"
            "- Backfill desde `s3://noaa-goes13` (5 bandas IR, adaptar la receta Ash RGB)\n"
            "- O bundle de PNGs públicos de archivo en `data/historic/calbuco_2015/`\n\n"
            "Sesión dedicada futura, ~500 LOC."
        )
