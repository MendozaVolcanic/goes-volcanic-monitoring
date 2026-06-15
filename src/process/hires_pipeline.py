"""Pipeline hi-res NOAA: descarga bandas L1b -> recorte por scope -> RGB.

Genera composites a 0.5 km/px (4× mejor que RAMMB zoom 4 = 1.7 km/px).

Uso:
    result = build_hires_for_scopes(
        dt=datetime(2026, 5, 9, 18, 0, tzinfo=timezone.utc),
        scopes={"villarrica": {"lat": -39.42, "lon": -71.93}, ...},
        radius_deg=0.5,
    )
    # result["villarrica"] = numpy (H, W, 3) uint8 listo para guardar/mostrar

Decisiones clave:
- Todas las bandas se descargan UNA vez por scan (~330 MB total). Despues
  recortamos por scope sin re-descargar.
- AMBOS modes hacen super-bbox slicing: se calcula la sub-region 0.5km que
  cubre todos los scopes y se materializa SOLO eso (refl + get_lat_lon).
  Jamas tocamos full-disk (B2 0.5km = 1.9 GB, get_lat_lon 1km = varios GB).
- mode 'color': PAN-SHARPENING. El color sale de B1/B2/B3 a 1 km y el detalle
  de B2 nativa a 0.5 km se inyecta (High-Pass Modulation) -> true-color a
  0.5 km/px (4× RAMMB) sin shift de color. Reemplazo del downsample 2x viejo.
- mode 'mono_05km': solo banda 2 a 0.5 km nativa, sepia monocromatica.
- De noche (sun < 5°) genero pseudo-color desde banda 13 IR (2 km nativo).

Performance esperado en runner GH:
- Descarga 4 bandas: ~30s (S3 NOAA paralelo)
- Procesar bandas (BT/refl, lat/lon una vez): ~10s
- Recorte + RGB para 8 scopes: ~10s
- Total: ~50-60s por scan.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import xarray as xr

from src.fetch.goes_s3 import download_band, open_band
from src.process.brightness_temp import rad_to_bt
from src.process.geo import bbox_indices, crop_to_bounds, get_lat_lon
from src.process.geocolor_lite import (
    band2_monochrome_05km, bt_to_pseudo_color_ir, rad_to_reflectance,
    solar_elevation, true_color_rgb,
)

logger = logging.getLogger(__name__)

# Constantes fisicas canonical desde src/config (con try/except fallback,
# mismo patron que MOSAICO_RADIUS_DEG en dashboard/views/).
try:
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
    from src.config import GOES19_PERSPECTIVE_POINT_HEIGHT as _H_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0
    _H_DEFAULT = 35786023.0

# Bandas a descargar:
#   1 = azul visible 0.47um, 1km/px
#   2 = rojo visible 0.64um, 0.5km/px (la "hi-res" que da el x4)
#   3 = NIR vegetacion 0.86um, 1km/px
#   13 = clean IR window 10.3um, 2km/px (night fallback)
BANDS_HIRES = [1, 2, 3, 13]

# Umbral solar elevation para day/night switch
DAY_NIGHT_THRESHOLD_DEG = 5.0


def _downsample_2x(arr: np.ndarray) -> np.ndarray:
    """Downsample 2x usando block_reduce mean (anti-aliasing decente)."""
    h, w = arr.shape[:2]
    h2, w2 = h // 2, w // 2
    if arr.ndim == 2:
        return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).mean(axis=(1, 3))
    else:
        return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, -1).mean(axis=(1, 3))


def _scope_pixel_bounds(ds: "xr.Dataset", lat_c: float, lon_c: float,
                        radius_deg: float, sat_lon: float = _SAT_LON_DEFAULT
                        ) -> tuple[int, int, int, int] | None:
    """Devolver (r0, r1, c0, c1) en pixels del Dataset para cubrir el bbox.

    Sin allocar grids 2D. Usa solo los arrays 1D x/y del dataset (87 KB c/u
    vs 940 MB de un meshgrid full de 21696×21696). Critico para mono_05km
    en runner GH free que solo tiene 7 GB RAM.
    """
    try:
        from pyproj import Proj
    except ImportError:
        return None

    h = float(ds["goes_imager_projection"].attrs.get(
        "perspective_point_height", _H_DEFAULT))
    p = Proj(proj="geos", lon_0=sat_lon, h=h, ellps="GRS80", sweep="x")

    x_arr = ds["x"].values  # 1D, ~21696 elementos
    y_arr = ds["y"].values  # 1D, idem

    cols, rows = [], []
    # Probar 9 puntos (4 esquinas + 4 medios + centro) para asegurar cobertura
    test_pts = []
    for dlat in (-radius_deg, 0, radius_deg):
        for dlon in (-radius_deg, 0, radius_deg):
            test_pts.append((lat_c + dlat, lon_c + dlon))
    for lat, lon in test_pts:
        try:
            x_m, y_m = p(lon, lat)
        except Exception:
            continue
        if not (np.isfinite(x_m) and np.isfinite(y_m)):
            continue
        x_rad = x_m / h
        y_rad = y_m / h
        # argmin |array - target| funciona en arrays ascendentes o descendentes
        col = int(np.argmin(np.abs(x_arr - x_rad)))
        row = int(np.argmin(np.abs(y_arr - y_rad)))
        cols.append(col)
        rows.append(row)

    if not rows:
        return None

    # Margen de 5 pixels para no perder bordes
    margin = 5
    return (max(0, min(rows) - margin),
            min(len(y_arr), max(rows) + margin + 1),
            max(0, min(cols) - margin),
            min(len(x_arr), max(cols) + margin + 1))


def _download_bands_parallel(dt: datetime, bands: list[int]) -> dict[int, str]:
    """Bajar todas las bandas en paralelo. Devuelve dict band -> path."""
    out = {}
    def _one(b):
        p = download_band(dt, b)
        return b, p

    with ThreadPoolExecutor(max_workers=4) as ex:
        for b, p in ex.map(_one, bands):
            if p is not None:
                out[b] = str(p)
            else:
                logger.warning("Band %d no descargado", b)
    return out


def build_hires_for_scopes(
    dt: datetime,
    scopes: dict[str, dict],
    radius_deg: float = 0.5,
    mode: str = "color",
) -> tuple[dict[str, np.ndarray | None], dict[str, dict]]:
    """Genera RGB hi-res para cada scope a partir del mismo scan L1b.

    Args:
        dt:           datetime UTC del scan deseado (NOAA elige el mas cercano).
        scopes:       dict scope_id -> {"lat": float, "lon": float}.
                      Por scope generamos un bbox cuadrado de ±radius_deg.
        radius_deg:   medio-tamanio del bbox en grados (default 0.5° ≈ 55 km).
        mode:         "color" (default): TrueColor pan-sharpened a 0.5km/px
                      diurno (4× RAMMB) + IR 2km nocturno.
                      "mono_05km": SOLO banda 2 a 0.5 km/px (4× zoom real).
                                   No baja b1 ni b3. Diurno solamente.

    Returns:
        Tupla `(images, meta)`:
          - `images`: dict scope_id -> numpy (H,W,3) uint8 RGB (None si fallo)
          - `meta`:   dict scope_id -> {"sun_alt": float (deg),
                                         "render": str}
            donde render ∈ {"visible_color", "visible_mono", "ir_pseudo",
                           "skip_night", "no_data", "error"}.
    """
    # 1. Descargar bandas. En mono_05km solo necesitamos banda 2 (visible
    # rojo 0.5km/px) — ahorra ~130 MB de download skipping b1+b3.
    bands_to_download = [2] if mode == "mono_05km" else BANDS_HIRES
    logger.info("Descargando bandas %s para %s (mode=%s)...",
                bands_to_download, dt.strftime("%Y-%m-%d %H:%M UTC"), mode)
    band_paths = _download_bands_parallel(dt, bands_to_download)
    if 2 not in band_paths:
        logger.error("Banda 2 indispensable no disponible")
        return {sid: None for sid in scopes}

    # 2. Abrir datasets en modo LAZY (no materializamos Rad full-disk).
    #    AMBOS modes hacen super-bbox slicing: jamas allocamos full-disk ni
    #    reflectancia (B2 0.5km = 1.9 GB) ni get_lat_lon 1km (varios GB de
    #    arrays intermedios). Critico para el runner HF (7 GB). El modo color
    #    ANTES materializaba B2 0.5km full + get_lat_lon 1km full -> OOM
    #    (hallazgo audit jun 2026). Ahora deferido al super-bbox como mono.
    datasets: dict[int, xr.Dataset] = {}
    for b, p in band_paths.items():
        datasets[b] = open_band(p)

    # 3. Super-bbox sobre la grilla 0.5 km de B2 (la mas fina) que cubre
    #    TODOS los scopes (~5000×1300 px ≈ 26 MB). Snap a multiplos de 4 para
    #    que la sub-region 0.5km mapee limpio a 1km (//2) y 2km (//4) por el
    #    anidamiento del fixed grid ABI (cada banda gruesa = block-mean de la
    #    fina, indices anidados por potencias de 2).
    all_bounds = []
    for sid, sinfo in scopes.items():
        pb = _scope_pixel_bounds(datasets[2], sinfo["lat"], sinfo["lon"],
                                 radius_deg)
        if pb is not None:
            all_bounds.append(pb)
    if not all_bounds:
        logger.error("super-bbox: no pude calcular pixel bounds de ningun scope")
        for ds in datasets.values():
            ds.close()
        return ({sid: None for sid in scopes},
                {sid: {"render": "error", "sun_alt": None} for sid in scopes})

    ny5 = int(datasets[2].sizes["y"])
    nx5 = int(datasets[2].sizes["x"])
    super_r0 = (min(b[0] for b in all_bounds) // 4) * 4
    super_r1 = min(((max(b[1] for b in all_bounds) + 3) // 4) * 4, ny5)
    super_c0 = (min(b[2] for b in all_bounds) // 4) * 4
    super_c1 = min(((max(b[3] for b in all_bounds) + 3) // 4) * 4, nx5)
    logger.info("super-bbox 0.5km: rows[%d:%d] cols[%d:%d] = %d x %d px",
                super_r0, super_r1, super_c0, super_c1,
                super_r1 - super_r0, super_c1 - super_c0)

    # Invariante de anidamiento ABI RadF: B2 0.5km = 2× B1/B3 1km = 4× B13 2km.
    # Los //2, //4 y el pan_crop=refls[2][2*r0:...] dependen de esto. Si alguna
    # banda NO fuera RadF full-disk (p.ej. RadC/RadM, otro origin de grid), el
    # recorte quedaria geograficamente CORRIDO sin lanzar excepcion. Lo chequeo
    # y, si no se cumple, logueo fuerte y NO pan-sharpenamos (mejor sin hi-res
    # que una imagen mal georreferenciada). Con RadF (hardcodeado en
    # download_band) siempre se cumple — es defensa ante cambios futuros.
    nest_ok = all(
        datasets[b].sizes["y"] * 2 == ny5 and datasets[b].sizes["x"] * 2 == nx5
        for b in (1, 3) if b in datasets
    ) and (13 not in datasets or (
        datasets[13].sizes["y"] * 4 == ny5
        and datasets[13].sizes["x"] * 4 == nx5))
    if mode == "color" and not nest_ok:
        logger.error("Anidamiento ABI roto (bandas no RadF?): B2=%dx%d -> "
                     "SIN pan-sharpen para este scan", ny5, nx5)

    # Grillas/arrays por resolucion. Solo materializamos sub-regiones.
    refls: dict[int, np.ndarray] = {}
    refl_b2_lo = None           # B2 degradada a 1 km (canal rojo del color LR)
    bt_ir = None                # B13 BT a 2 km (night IR pseudo-color)
    lat_hi = lon_hi = None      # grilla 0.5 km (pan + mono)
    lat_lo = lon_lo = None      # grilla 1 km   (color LR)
    lat_ir = lon_ir = None      # grilla 2 km   (night IR)

    # B2 nativa 0.5 km (sub-region) — pan (color) o canal mono.
    ds2_s = datasets[2].isel(y=slice(super_r0, super_r1),
                             x=slice(super_c0, super_c1))
    refls[2] = rad_to_reflectance(ds2_s["Rad"], ds2_s)
    lat_hi, lon_hi = get_lat_lon(ds2_s)
    ds2_s.close()

    if mode == "color" and nest_ok:
        # B1, B3 a 1 km: bounds = super//2 (anidamiento ABI).
        r0_1, r1_1 = super_r0 // 2, super_r1 // 2
        c0_1, c1_1 = super_c0 // 2, super_c1 // 2
        for b in (1, 3):
            if b not in datasets:
                continue
            ds_b = datasets[b].isel(y=slice(r0_1, r1_1), x=slice(c0_1, c1_1))
            refls[b] = rad_to_reflectance(ds_b["Rad"], ds_b)
            if lat_lo is None:
                lat_lo, lon_lo = get_lat_lon(ds_b)
            ds_b.close()
        # B2 degradada a 1 km = canal rojo del color LR (alineado a B1/B3).
        refl_b2_lo = _downsample_2x(refls[2])
        # Alinear shapes (off-by-1 por anidamiento) -> recortar a min comun.
        if lat_lo is not None and 1 in refls and 3 in refls:
            mh = min(refls[1].shape[0], refls[3].shape[0],
                     refl_b2_lo.shape[0], lat_lo.shape[0])
            mw = min(refls[1].shape[1], refls[3].shape[1],
                     refl_b2_lo.shape[1], lat_lo.shape[1])
            refls[1] = refls[1][:mh, :mw]
            refls[3] = refls[3][:mh, :mw]
            refl_b2_lo = refl_b2_lo[:mh, :mw]
            lat_lo = lat_lo[:mh, :mw]
            lon_lo = lon_lo[:mh, :mw]

        # B13 a 2 km (night IR fallback): bounds = super//4.
        if 13 in datasets:
            r0_4, r1_4 = super_r0 // 4, super_r1 // 4
            c0_4, c1_4 = super_c0 // 4, super_c1 // 4
            ds13_s = datasets[13].isel(y=slice(r0_4, r1_4),
                                       x=slice(c0_4, c1_4))
            bt_ir = rad_to_bt(ds13_s).values
            lat_ir, lon_ir = get_lat_lon(ds13_s)
            ds13_s.close()

    # 5. Por cada scope: decidir day/night + recortar + RGB.
    # `out_meta` registra qué modo se usó por scope (visible/IR) + sun_alt
    # para que el dashboard pueda mostrar al usuario QUÉ está viendo.
    out: dict[str, np.ndarray | None] = {}
    out_meta: dict[str, dict] = {}
    for sid, scope_info in scopes.items():
        lat_c = scope_info["lat"]
        lon_c = scope_info["lon"]
        bounds = {
            "lat_min": lat_c - radius_deg, "lat_max": lat_c + radius_deg,
            "lon_min": lon_c - radius_deg, "lon_max": lon_c + radius_deg,
        }
        sun_alt = solar_elevation(lat_c, lon_c, dt)
        is_day = sun_alt >= DAY_NIGHT_THRESHOLD_DEG

        out_meta[sid] = {"sun_alt": round(sun_alt, 1), "render": None}
        try:
            if mode == "mono_05km":
                # Modo 0.5 km/px: solo banda 2 monocromatica.
                # Solo tiene sentido de dia (visible necesita sol).
                if not is_day:
                    logger.info("[%s] mono_05km NOCHE (sun=%.1f°) -> skip",
                                sid, sun_alt)
                    out[sid] = None
                    out_meta[sid]["render"] = "skip_night"
                    continue
                b2_crop, _, _ = crop_to_bounds(
                    xr.DataArray(refls[2], dims=["y", "x"]),
                    lat_hi, lon_hi, bounds)
                if b2_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = band2_monochrome_05km(b2_crop)
                out_meta[sid]["render"] = "visible_mono"
                logger.info("[%s] mono_05km DIA sun=%.1f° -> %s (0.5km/px)",
                            sid, sun_alt, rgb.shape)
            elif (is_day and 1 in refls and 3 in refls
                  and refl_b2_lo is not None and lat_lo is not None):
                # TrueColor diurno PAN-SHARPENED a 0.5 km/px (4× RAMMB):
                # color de B1/B2lo/B3 a 1 km + detalle de B2 nativa 0.5 km.
                # Recorto UNA vez en la grilla 1 km y derivo el pan como
                # EXACTAMENTE 2× los mismos indices (anidamiento ABI: 1km
                # pixel k <-> 0.5km pixels 2k,2k+1). Asi color y detalle quedan
                # co-registrados — sin ghosting por recortes independientes.
                idx = bbox_indices(lat_lo, lon_lo, bounds)
                if idx is None:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                r0, r1, c0, c1 = idx
                b1_crop = refls[1][r0:r1, c0:c1]
                b2lo_crop = refl_b2_lo[r0:r1, c0:c1]
                b3_crop = refls[3][r0:r1, c0:c1]
                pan_crop = refls[2][2 * r0:2 * r1, 2 * c0:2 * c1]
                if b2lo_crop.size == 0 or pan_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = true_color_rgb(b1_crop, b2lo_crop, b3_crop,
                                     pan=pan_crop)
                out_meta[sid]["render"] = "visible_color"
                logger.info("[%s] DIA sun=%.1f° -> TrueColor pan-sharp %s (0.5km/px)",
                            sid, sun_alt, rgb.shape)
            elif bt_ir is not None and lat_ir is not None:
                # Night IR pseudo-color (2 km nativo).
                bt_crop, _, _ = crop_to_bounds(
                    xr.DataArray(bt_ir, dims=["y", "x"]),
                    lat_ir, lon_ir, bounds)
                if bt_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = bt_to_pseudo_color_ir(bt_crop)
                out_meta[sid]["render"] = "ir_pseudo"
                logger.info("[%s] NOCHE sun=%.1f° -> IR pseudo-color %s",
                            sid, sun_alt, rgb.shape)
            else:
                logger.warning("[%s] sin datos visible NI IR -> None", sid)
                out[sid] = None
                out_meta[sid]["render"] = "no_data"
                continue
            out[sid] = rgb
        except Exception as e:
            logger.exception("[%s] error: %s", sid, e)
            out[sid] = None
            out_meta[sid]["render"] = "error"

    # Cerrar datasets
    for ds in datasets.values():
        ds.close()
    # Devolver tupla (imagenes, metadata por scope) para que el caller
    # registre QUE TIPO de render salio (visible vs IR) y muestre al user.
    return out, out_meta
