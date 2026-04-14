"""
goes_export.py — Exporta últimas imágenes GOES-19 a docs/goes/ para GitHub Pages.

Corre el pipeline completo (descarga → proceso → PNG) y genera:
  docs/goes/ash_rgb_latest.png
  docs/goes/ash_so2_rgb_latest.png
  docs/goes/meta_latest.json

Uso:
  python goes_export.py          # última imagen disponible
  python goes_export.py --test   # verifica dependencias y conexión S3
"""

import json
import sys
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs" / "goes"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Mantener historial de últimas N imágenes en docs/goes/history/
HISTORY_DIR = DOCS_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
MAX_HISTORY = 48  # ~24h de imágenes cada 30 min


def exportar():
    print(f"\n{'='*60}")
    print(f"GOES EXPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    try:
        from src.fetch.goes_s3 import get_latest_time
        from src.process.pipeline import process_ash_rgb
    except ImportError as e:
        print(f"ERROR importando módulos: {e}")
        print("Verifica que estás ejecutando desde la carpeta raíz del proyecto GOES")
        sys.exit(1)

    # Obtener última hora disponible en S3
    print("Buscando última imagen disponible en GOES-19 S3...")
    try:
        dt = get_latest_time(band=14)
        print(f"Timestamp disponible: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
    except Exception as e:
        print(f"ERROR obteniendo timestamp: {e}")
        sys.exit(1)

    # Verificar si ya tenemos esta imagen
    ts_str = dt.strftime("%Y%m%d_%H%M")
    meta_path = DOCS_DIR / "meta_latest.json"
    if meta_path.exists():
        try:
            meta_prev = json.loads(meta_path.read_text())
            if meta_prev.get("timestamp_str") == ts_str:
                print(f"Imagen {ts_str} ya exportada. Sin cambios.")
                return 0
        except Exception:
            pass

    # Procesar
    print(f"\nProcesando pipeline para {dt.strftime('%Y-%m-%d %H:%M UTC')}...")
    try:
        resultado = process_ash_rgb(dt, save=True)
    except Exception as e:
        print(f"ERROR en pipeline: {e}")
        # Guardar meta de error para que el dashboard lo muestre
        meta_error = {
            "timestamp": dt.isoformat(),
            "timestamp_str": ts_str,
            "error": str(e),
            "productos": []
        }
        meta_path.write_text(json.dumps(meta_error, indent=2))
        return 1

    # Copiar PNGs a docs/goes/
    paths = resultado.get("paths", {})
    productos_exportados = []

    for producto in ["ash_rgb", "ash_so2_rgb"]:
        src = paths.get(producto)
        if src and Path(src).exists():
            # Latest
            dest_latest = DOCS_DIR / f"{producto}_latest.png"
            shutil.copy2(src, dest_latest)
            # Historia
            dest_history = HISTORY_DIR / f"{producto}_{ts_str}.png"
            shutil.copy2(src, dest_history)
            productos_exportados.append(producto)
            print(f"  Exportado: {dest_latest.name}")

    # Limpiar historial antiguo (mantener últimas MAX_HISTORY por tipo)
    for producto in ["ash_rgb", "ash_so2_rgb"]:
        archivos = sorted(HISTORY_DIR.glob(f"{producto}_*.png"))
        if len(archivos) > MAX_HISTORY:
            for f_old in archivos[:-MAX_HISTORY]:
                f_old.unlink()

    # Generar índice de historial
    historial = []
    for f in sorted(HISTORY_DIR.glob("ash_rgb_*.png"), reverse=True)[:MAX_HISTORY]:
        ts = f.stem.replace("ash_rgb_", "")
        try:
            dt_h = datetime.strptime(ts, "%Y%m%d_%H%M").replace(tzinfo=timezone.utc)
            historial.append({
                "ts": ts,
                "iso": dt_h.isoformat(),
                "label": dt_h.strftime("%d %b %H:%M"),
                "ash_rgb": f"history/ash_rgb_{ts}.png",
                "ash_so2_rgb": f"history/ash_so2_rgb_{ts}.png"
            })
        except ValueError:
            pass

    # Metadata
    meta = {
        "timestamp": dt.isoformat(),
        "timestamp_str": ts_str,
        "label": dt.strftime("%d %b %Y %H:%M UTC"),
        "satelite": "GOES-19",
        "productos": productos_exportados,
        "historial": historial[:24],  # últimas 24 entradas en JSON
        "algoritmos": {
            "ash_rgb": "RAMMB/CIRA Ash RGB (B15-B14 / B14-B11 / B13)",
            "ash_so2_rgb": "EUMETSAT Ash/SO2 RGB (B14-B15 / B11-B14 / B14)"
        }
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\nMetadata guardada: {meta_path}")

    print(f"\n{'='*60}")
    print(f"Exportación exitosa: {len(productos_exportados)} productos")
    print(f"{'='*60}\n")
    return 0


def test_conexion():
    """Verifica dependencias y conexión S3 sin procesar."""
    print("Test de conexión GOES S3...")
    try:
        import s3fs
        import xarray
        import numpy
        from PIL import Image
        print("  Dependencias: OK")
    except ImportError as e:
        print(f"  ERROR dependencias: {e}")
        return 1

    try:
        from src.fetch.goes_s3 import get_latest_time
        dt = get_latest_time(band=14)
        print(f"  S3 acceso: OK — última imagen: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
    except Exception as e:
        print(f"  ERROR S3: {e}")
        return 1

    print("Test exitoso.")
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(test_conexion())
    else:
        sys.exit(exportar())
