"""Reporte PDF diario para Volcan Lascar.

Genera un PDF de 1 pagina A4 con:
  - Header (fecha UTC + Chile, alerta operacional placeholder)
  - Ash RGB ultimo scan (zoom volcan)
  - Serie de tiempo % ash 24h
  - Tabla hot spots ultimas 24h dentro de 50 km
  - Footer (link dashboard, fuentes)

Output: reports/lascar/YYYY-MM-DD.pdf

Disenado para correr de GitHub Actions una vez al dia. Si un fetcher falla
no aborta — pone "sin datos" en el slot correspondiente. Asi el PDF se
genera siempre y queda traza historica aunque RAMMB/NOAA esten caidos.

Uso:
    python scripts/generate_lascar_report.py            # fecha actual
    python scripts/generate_lascar_report.py --date 2026-04-25
"""

import argparse
import logging
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# Permitir ejecucion desde raiz del repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import fetch_frame_for_bounds, get_latest_timestamps
from src.fetch.timeseries import fetch_volcano_timeseries
from src.volcanos import get_volcano

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lascar_report")

LASCAR = get_volcano("Láscar")
DASHBOARD_URL = "https://goesvolcanic.streamlit.app"
HOT_SPOT_RADIUS_KM = 50

# Bounds para frame Ash RGB — ~30 km de radio alrededor del crater
FRAME_RADIUS_DEG = 0.3


def _utc_to_chile(dt_utc: datetime) -> datetime:
    """UTC -> America/Santiago (UTC-3 estandar, sin DST por simplicidad CI)."""
    return dt_utc - timedelta(hours=3)


def _safe_call(label: str, fn, *args, **kwargs):
    """Ejecutar fetcher con captura de excepcion. Loggear y devolver None si falla.

    El reporte debe generarse aunque algun fetcher caiga — mejor un PDF con
    "sin datos" que no tener PDF.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.warning("%s fallo: %s", label, e)
        log.debug(traceback.format_exc())
        return None


def fetch_latest_ash_frame() -> tuple[np.ndarray | None, str | None]:
    """Bajar el ultimo frame Ash RGB centrado en Lascar."""
    bounds = {
        "lat_min": LASCAR.lat - FRAME_RADIUS_DEG,
        "lat_max": LASCAR.lat + FRAME_RADIUS_DEG,
        "lon_min": LASCAR.lon - FRAME_RADIUS_DEG,
        "lon_max": LASCAR.lon + FRAME_RADIUS_DEG,
    }
    timestamps = _safe_call("get_latest_timestamps", get_latest_timestamps, "eumetsat_ash", n=1)
    if not timestamps:
        return None, None
    ts = timestamps[0]
    img = _safe_call("fetch_frame_for_bounds", fetch_frame_for_bounds,
                     "eumetsat_ash", ts, bounds, zoom=4)
    return img, ts


def fetch_24h_timeseries() -> list:
    """% pixeles ash ultimos 144 frames (~24h cadencia 10 min)."""
    pts = _safe_call("fetch_volcano_timeseries", fetch_volcano_timeseries,
                     LASCAR.lat, LASCAR.lon, "eumetsat_ash", n_frames=144)
    return pts or []


def fetch_recent_hotspots() -> list[HotSpot]:
    """Hotspots FDCF en bbox ~100 km alrededor de Lascar (1 hora)."""
    bounds = {
        "lat_min": LASCAR.lat - 0.5, "lat_max": LASCAR.lat + 0.5,
        "lon_min": LASCAR.lon - 0.5, "lon_max": LASCAR.lon + 0.5,
    }
    result = _safe_call("fetch_latest_hotspots", fetch_latest_hotspots,
                        bounds=bounds, hours_back=1)
    if not result:
        return []
    hotspots, _ = result
    # Filtro fino por distancia real al crater
    out = []
    for h in hotspots:
        dlat = (h.lat - LASCAR.lat) * 111.0
        dlon = (h.lon - LASCAR.lon) * 111.0 * np.cos(np.radians(LASCAR.lat))
        if np.hypot(dlat, dlon) <= HOT_SPOT_RADIUS_KM:
            out.append(h)
    return out


def render_pdf(out_path: Path, report_date: datetime) -> None:
    """Construye el PDF A4 de 1 pagina."""
    log.info("Bajando datos...")
    ash_img, ash_ts = fetch_latest_ash_frame()
    timeseries = fetch_24h_timeseries()
    hotspots = fetch_recent_hotspots()
    log.info("ash_img=%s | ts_points=%d | hotspots=%d",
             "OK" if ash_img is not None else "MISSING",
             len(timeseries), len(hotspots))

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(8.27, 11.69))  # A4 vertical en pulgadas
    fig.suptitle(
        f"Volcán Láscar — Reporte diario GOES-19\n"
        f"{report_date.strftime('%Y-%m-%d')} (UTC)",
        fontsize=14, fontweight="bold", y=0.97,
    )

    gs = fig.add_gridspec(
        nrows=4, ncols=2,
        height_ratios=[0.6, 2.5, 2.0, 1.5],
        hspace=0.45, wspace=0.25,
        left=0.08, right=0.95, top=0.92, bottom=0.05,
    )

    # ── Header info ──────────────────────────────────────────────
    ax_h = fig.add_subplot(gs[0, :])
    ax_h.axis("off")
    chile_now = _utc_to_chile(report_date)
    info = (
        f"Coordenadas: {LASCAR.lat}°S, {abs(LASCAR.lon)}°W   |   "
        f"Elevación: {LASCAR.elevation} m   |   "
        f"Región: {LASCAR.region}\n"
        f"Generado UTC: {report_date.strftime('%Y-%m-%d %H:%M')}   |   "
        f"Hora Chile (aprox): {chile_now.strftime('%H:%M')}\n"
        f"Dashboard NRT: {DASHBOARD_URL}"
    )
    ax_h.text(0.0, 0.5, info, fontsize=9, va="center", family="monospace")

    # ── Ash RGB ──────────────────────────────────────────────────
    ax_ash = fig.add_subplot(gs[1, 0])
    if ash_img is not None:
        ax_ash.imshow(ash_img, extent=[
            LASCAR.lon - FRAME_RADIUS_DEG, LASCAR.lon + FRAME_RADIUS_DEG,
            LASCAR.lat - FRAME_RADIUS_DEG, LASCAR.lat + FRAME_RADIUS_DEG,
        ])
        ax_ash.plot(LASCAR.lon, LASCAR.lat, "r^", markersize=10,
                    markeredgecolor="white", markeredgewidth=1.5)
        ax_ash.set_title(f"Ash RGB — scan {ash_ts}", fontsize=10)
        ax_ash.set_xlabel("Longitud", fontsize=8)
        ax_ash.set_ylabel("Latitud", fontsize=8)
        ax_ash.tick_params(labelsize=7)
    else:
        ax_ash.text(0.5, 0.5, "Sin datos\nAsh RGB", ha="center", va="center",
                    fontsize=11, color="gray")
        ax_ash.set_xticks([]); ax_ash.set_yticks([])

    # ── Hot spots tabla ──────────────────────────────────────────
    ax_hs = fig.add_subplot(gs[1, 1])
    ax_hs.axis("off")
    ax_hs.set_title(f"Hot spots FDCF (≤{HOT_SPOT_RADIUS_KM} km)", fontsize=10)
    if hotspots:
        rows = [["Conf.", "T (K)", "FRP (MW)", "Δd (km)"]]
        for h in hotspots[:10]:
            dlat = (h.lat - LASCAR.lat) * 111.0
            dlon = (h.lon - LASCAR.lon) * 111.0 * np.cos(np.radians(LASCAR.lat))
            d = float(np.hypot(dlat, dlon))
            rows.append([h.confidence[:4], f"{h.temp_k:.0f}", f"{h.frp_mw:.1f}", f"{d:.1f}"])
        tbl = ax_hs.table(cellText=rows[1:], colLabels=rows[0],
                          loc="center", cellLoc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.4)
    else:
        ax_hs.text(0.5, 0.5, "Sin hotspots\nen 24h", ha="center", va="center",
                   fontsize=11, color="gray")

    # ── Time series ──────────────────────────────────────────────
    ax_ts = fig.add_subplot(gs[2, :])
    avail = [p for p in timeseries if p.available]
    if avail:
        xs = [p.dt for p in avail]
        ys = [p.metric * 100 for p in avail]
        ax_ts.plot(xs, ys, "-o", markersize=3, color="#c0392b", linewidth=1.2)
        ax_ts.fill_between(xs, 0, ys, color="#c0392b", alpha=0.15)
        ax_ts.set_title(
            f"Serie 24h — fracción de píxeles con firma de ceniza (n={len(avail)})",
            fontsize=10,
        )
        ax_ts.set_ylabel("% píxeles con ash", fontsize=9)
        ax_ts.set_xlabel("UTC", fontsize=9)
        ax_ts.tick_params(labelsize=8)
        ax_ts.grid(alpha=0.3)
        # Anotar pico
        i_max = int(np.argmax(ys))
        ax_ts.annotate(f"pico {ys[i_max]:.1f}%",
                       xy=(xs[i_max], ys[i_max]),
                       xytext=(10, 10), textcoords="offset points",
                       fontsize=8, color="#c0392b",
                       arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8))
    else:
        ax_ts.text(0.5, 0.5, "Sin serie de tiempo disponible",
                   ha="center", va="center", fontsize=11, color="gray",
                   transform=ax_ts.transAxes)
        ax_ts.set_xticks([]); ax_ts.set_yticks([])

    # ── Footer ───────────────────────────────────────────────────
    ax_f = fig.add_subplot(gs[3, :])
    ax_f.axis("off")
    footer = (
        "Fuentes: RAMMB/CIRA (Ash RGB), NOAA NESDIS FDCF L2 (hot spots),\n"
        "        SSEC/CIMSS VOLCAT (altura — ver dashboard).\n"
        "Algoritmo Ash RGB: receta EUMETSAT (B15-B14, B14-B11, B13).\n"
        "BTD < -1 K = firma de ceniza (Prata 1989).\n"
        "Reporte automatico — verificar en dashboard antes de decisiones operativas.\n"
        "SERNAGEOMIN — generado por GitHub Actions sin intervencion humana."
    )
    ax_f.text(0.0, 0.95, footer, fontsize=7.5, va="top", family="monospace",
              color="#555")

    with PdfPages(out_path) as pp:
        pp.savefig(fig, bbox_inches="tight")
        # Metadata embebido
        d = pp.infodict()
        d["Title"] = f"Lascar reporte {report_date.strftime('%Y-%m-%d')}"
        d["Author"] = "SERNAGEOMIN — GOES Volcanic Monitor"
        d["Subject"] = "Reporte diario automatico"
        d["Keywords"] = "Lascar, GOES-19, Ash RGB, FDCF, ceniza"
        d["CreationDate"] = report_date

    plt.close(fig)
    log.info("PDF generado: %s", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: hoy UTC)")
    ap.add_argument("--out-dir", default="reports/lascar",
                    help="Directorio de salida")
    args = ap.parse_args()

    if args.date:
        report_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        report_date = datetime.now(timezone.utc)

    out_path = Path(args.out_dir) / f"{report_date.strftime('%Y-%m-%d')}.pdf"
    render_pdf(out_path, report_date)


if __name__ == "__main__":
    main()
