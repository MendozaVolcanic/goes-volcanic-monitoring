# STATUS — Goes Dashboard

## Estado actual (2026-04-12)
Infraestructura completa. GitHub Pages pendiente de activar.

## Objetivo
Dashboard automático de imágenes GOES-19 (Ash RGB + Ash/SO2 RGB) para monitoreo volcánico.

## Completado
- `goes_export.py` — genera PNGs cada 30 min, escribe meta_latest.json
  - Ash RGB (RAMMB/CIRA recipe: B15-B14 / B14-B11 / B13)
  - Ash/SO2 RGB (EUMETSAT recipe)
  - Historial: últimas 48 imágenes (~24h)
- `requirements_actions.txt` — sin cartopy/streamlit (solo pipeline deps para Actions)
- `.github/workflows/goes.yml` — cron */30 * * * *, commit docs/goes/
- `docs/index.html` — 4 tabs: última imagen, comparación Ash vs SO2, historial, interpretación

## Pendiente
- **GitHub Pages**: activar en Settings → Pages → main/docs

## Arquitectura
```
docs/goes/ash_rgb_latest.png          ← imagen más reciente
docs/goes/ash_so2_rgb_latest.png
docs/goes/meta_latest.json            ← timestamp + paths historial
docs/goes/history/                    ← últimas 48 imágenes
```

## Notas técnicas
- Fuente: NOAA S3 público (no requiere auth)
- cartopy excluido de requirements_actions.txt — causa fallos en Actions por libgeos-dev
- Streamlit/folium también excluidos del workflow
