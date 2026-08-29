"""Exportacion de un frame satelital a archivo: PNG y GeoTIFF.

Por que un modulo propio: estas tres funciones vivian dentro de
`dashboard/views/live_viewer.py` y las necesitan ahora tambien los paneles de
la grilla de volcan (`modo_guardia_volcan.py`). Una vista importando de otra
vista solo para bajar un archivo es el acoplamiento que ya nos dejo dos
fuentes de verdad de las recetas de producto en esta rama. `map_helpers.py`
tampoco es el lugar: ese archivo dibuja mapas y leyendas, esto escribe
archivos.

Las dos salidas no son intercambiables:

- **PNG**: para informes y correo. Lleva el timestamp (y el encuadre) impresos
  en una banda al pie, asi que el archivo se explica solo cuando alguien lo
  encuentra suelto meses despues.
- **GeoTIFF**: para QGIS/ArcGIS. EPSG:4326, 3 bandas RGB, sin texto encima —
  el texto arruinaria el analisis del pixel.
"""

from __future__ import annotations

import logging

import numpy as np
import streamlit as st

logger = logging.getLogger(__name__)


def _fmt_size(n_bytes: int) -> str:
    """Tamano legible: KB debajo de 1 MB.

    Por que: el encuadre de un volcan pesa decenas de KB, no megas como el
    nacional. Con "MB" fijo el boton rotulaba "0.0 MB" y parecia que no iba a
    bajar nada.
    """
    kb = n_bytes / 1024
    return f"{kb/1024:.1f} MB" if kb >= 1024 else f"{kb:.0f} KB"


def img_to_png_bytes(arr: np.ndarray, label: str | None = None) -> bytes:
    """numpy array -> PNG bytes (con label opcional sobre-impreso al pie).

    Usado por los botones de descarga. label deberia ser el timestamp UTC +
    scope (volcan, encuadre) para que el archivo descargado sea
    autoexplicativo: si solo guardaste el PNG, no perdes el contexto.
    """
    import io as _io
    from PIL import Image as _PIL, ImageDraw as _ID, ImageFont as _IF

    img = _PIL.fromarray(arr).convert("RGB")
    if label:
        # Cinta inferior con timestamp
        draw = _ID.Draw(img)
        fs = max(11, int(img.width * 0.018))
        try:
            font = _IF.truetype("DejaVuSans-Bold.ttf", fs)
        except Exception:
            try:
                font = _IF.truetype("arial.ttf", fs)
            except Exception:
                font = _IF.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        th = bbox[3] - bbox[1]
        pad = max(5, fs // 3)
        band_h = th + pad * 2
        y0 = img.height - band_h
        overlay = _PIL.new("RGBA", img.size, (0, 0, 0, 0))
        odraw = _ID.Draw(overlay)
        odraw.rectangle([0, y0, img.width, img.height], fill=(0, 0, 0, 180))
        img = _PIL.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = _ID.Draw(img)
        draw.text((pad, y0 + pad), label, fill=(255, 255, 255), font=font)
        # Marca arriba-derecha
        brand = "GOES-19 / RAMMB-CIRA"
        bb = draw.textbbox((0, 0), brand, font=font)
        bw = bb[2] - bb[0]
        draw.text((img.width - bw - pad, pad), brand,
                  fill=(180, 200, 220), font=font)

    buf = _io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def png_download_button(arr: np.ndarray, filename: str, label_overlay: str,
                        button_label: str, key: str) -> None:
    """Boton de descarga compacto para un frame estatico."""
    if arr is None:
        return
    png = img_to_png_bytes(arr, label_overlay)
    st.download_button(
        f"⬇ {button_label} ({_fmt_size(len(png))})",
        data=png,
        file_name=filename,
        mime="image/png",
        key=key,
        width='stretch',
    )


def download_buttons(arr: np.ndarray, bounds: dict, base_filename: str,
                     label_overlay: str, prod_label: str,
                     key_prefix: str) -> None:
    """Pareja de botones PNG + GeoTIFF en columnas.

    PNG: visualizacion (con timestamp impreso en banda inferior, ideal para
    informes / mail).
    GeoTIFF: archivo georeferenciado para QGIS / analisis posterior. CRS
    EPSG:4326, 3 bandas RGB, sin overlay de texto.
    """
    if arr is None:
        return
    from src.export.geotiff import build_geotiff_bytes

    col_png, col_tif = st.columns(2)
    with col_png:
        png_download_button(
            arr,
            filename=f"{base_filename}.png",
            label_overlay=label_overlay,
            button_label=f"PNG · {prod_label}",
            key=f"{key_prefix}_png",
        )
    with col_tif:
        try:
            tif_bytes = build_geotiff_bytes(
                arr, bounds, description=label_overlay,
            )
        except Exception as e:
            logger.warning("GeoTIFF build failed: %s", e)
            tif_bytes = b""
        if tif_bytes:
            st.download_button(
                f"⬇ GeoTIFF · {prod_label} ({_fmt_size(len(tif_bytes))})",
                data=tif_bytes,
                file_name=f"{base_filename}.tif",
                mime="image/tiff",
                key=f"{key_prefix}_tif",
                width='stretch',
                help=(
                    "Imagen georeferenciada (EPSG:4326, RGB). Abre directo en "
                    "QGIS, ArcGIS o cualquier viewer GIS. Conserva las "
                    "coordenadas exactas de cada pixel."
                ),
            )
        else:
            # Sin bytes no hay archivo: mejor decirlo que ofrecer un boton que
            # baja 0 KB y se descubre recien al abrirlo en QGIS.
            st.caption("GeoTIFF no disponible para este frame")
