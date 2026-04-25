# STATUS — Goes Dashboard

**Última actualización:** 2026-04-25
**Último commit relevante:** `1fc74f0` — "Sub-tabs por producto en Zona/Volcan + thumbnails en Series + mas compact"
**Deploy en producción:** https://goesvolcanic.streamlit.app
**Repo:** https://github.com/MendozaVolcanic/goes-volcanic-monitoring

> Este archivo es el resumen rápido de estado. Para info estructurada de
> integración con otros proyectos ver `INTEGRATION.md`. Para detalles técnicos
> ver `CLAUDE.md`.

---

## ✅ Completado en sesión 2026-04-25 (Tier 1 entero)

| Feature | Archivos | Commit |
|---|---|---|
| Hot spots NOAA FDCF (overlay en En Vivo) | `src/fetch/goes_fdcf.py`, `dashboard/views/live_viewer.py` | `b7fa1f7` |
| Series de tiempo por volcán + KPIs | `src/fetch/timeseries.py`, `dashboard/views/timeseries_viewer.py` | `b7fa1f7` |
| Export GeoTIFF (EPSG:4326) | `src/export/geotiff.py` + botones | `b7fa1f7` |
| Tab Altura de Pluma VOLCAT (Pavolonis 2013, 4 productos) | `dashboard/views/volcat_viewer.py` | `6e9aafb` |
| Cheat-sheet visual + ayuda contextual VOLCAT | `dashboard/views/volcat_viewer.py` | `d12c31a` |
| Sub-tabs por producto consistentes (Nacional/Zona/Volcán) | `dashboard/views/live_viewer.py` | `1fc74f0` |
| Thumbnails contextuales en Series (PICO + ÚLTIMO) | `dashboard/views/timeseries_viewer.py` | `1fc74f0` |
| Compactación universal de UI (~50-65% menos altura) | `dashboard/style.py` | `d12c31a` + `1fc74f0` |
| Cache buster RAMMB latest_times.json | `src/fetch/rammb_slider.py` | `3895618` |
| Fix doble-Láscar en vista Volcán | `dashboard/views/live_viewer.py` | `3895618` |
| Descarga MP4 (H.264) + GIF + ZIP de animaciones | `dashboard/views/rammb_viewer.py` | `8e9b0b2` |
| Investigación VOLCAT vs Wen-Rose (decisión: VOLCAT primario) | `docs/ALTURA_COLUMNA_INVESTIGACION.md` | `ac7292b` |
| Adopción del sistema sync con Integracion_Plataformas | `INTEGRATION.md` + `CLAUDE.md` | `64f0fc0` |

## 🟡 Pendiente — siguiente sesión

### Tier 2 (acordado, alto valor)

1. **🎯 PRÓXIMO ACORDADO: Estimación de altura de columna Wen-Rose 1994 (Fase 3)**
   - Solo como **fallback** y reanálisis histórico (Calbuco 2015, Hudson 2011, Chaitén 2008).
   - VOLCAT cubre Fase 1 (ya hecho).
   - ~600-800 LOC + validación contra eventos conocidos.
   - Detalle completo en `docs/ALTURA_COLUMNA_INVESTIGACION.md` (sección Fase 3).
   - Inputs disponibles: BTD (B14-B15), L1b S3. Faltan: Tsfc (LST L2 o GFS), perfil T(z) GFS via NOMADS/herbie.

2. **TROPOMI/Sentinel-5P SO2** → cubierto por proyecto **VolcPlume-v1** (no implementar acá, integrar después desde `Integracion_Plataformas/`).

3. **Comparación lado a lado** de 2 timestamps con sliders independientes.

4. **Reporte PDF diario automatizado** por volcán prioritario (GitHub Actions).

5. **Integración con VRP Chile / Lightning-v1** → trabajar desde `Integracion_Plataformas/propuestas/` (ver `goes_lightning/` ya scaffoldeado).

### Tier 3 (UX polish, no urgente)

- Permalinks (URL con `?ts=...&volcan=...`).
- Navegación con teclado en animación (← → para frames).
- Layout responsive para tablet.
- Modo guardia (full screen + auto-refresh sin controles).

### Tier 4 (institucional)

- Log de turnos.
- Anotación de scans (real / falso positivo / dudoso).
- Conexión con alertas SERNAGEOMIN.

### Tier 5 (robustez técnica)

- Tests para matemática geo (`reproject_to_latlon`, parallax, Planck).
- CI smoke test (que `render()` no tire excepciones).
- Logging persistente en S3.

---

## 📁 Carpetas hermanas relevantes (mismo padre `Volcanologia/`)

```
Volcanologia/
├── Goes/                              ← ESTE proyecto
├── Pronostico_Cenizas/                ← scaffolding modelo lagrangiano (no iniciado)
├── Integracion_Plataformas/           ← hub central de integraciones
│   ├── proyectos/
│   │   ├── INDICE.md                  ← regenerado por scripts/sync.py
│   │   ├── goes.md                    ← copia automática de Goes/INTEGRATION.md
│   │   ├── vrp_chile.md, valles.md, ovdas.md, ...
│   │   └── automatizacion_web.md      ← Lightning, VolcPlume (TROPOMI), NHI, ...
│   ├── propuestas/
│   │   └── goes_lightning/            ← piloto #1 GLM rayos (no iniciado)
│   └── scripts/
│       ├── sync.py                    ← orquestador
│       ├── proyectos.yaml             ← registro de 14 proyectos
│       └── INTEGRATION_TEMPLATE.md    ← plantilla
├── VRP Chile/                         ← térmico MODIS/VIIRS, operativo
├── Valles/                            ← hidrografía + población
├── OpenVIS/, openVIS-code/            ← infrasonido, en adaptación
└── OVDAS/                             ← assets institucionales
```

Y en `C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\`:
8 subproyectos volcanológicos automatizados (Lightning-v1, VolcPlume-v1 ←
TROPOMI ya implementado—, Copernicus-v1, Landsat-v1, LiCSAR-v1, Mirova-v1,
NHI-Tool, VegStress-v1).

---

## ⚙ Sistema de sync de docs activo

Cuando hagas cambios significativos a este proyecto:

1. Editar `Goes/INTEGRATION.md` → actualizar `last_updated` y secciones que cambien.
2. Desde `Integracion_Plataformas/`: `python scripts/sync.py`.
3. Commit + push.

Eso refresca `Integracion_Plataformas/proyectos/goes.md` automáticamente y regenera el `INDICE.md`.

---

## 🔧 Comandos útiles para arrancar

```bash
# Ver últimos commits
cd "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes"
git log --oneline -5

# Correr local
streamlit run dashboard/app.py

# Refrescar hub de integración
cd "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Integracion_Plataformas"
python scripts/sync.py

# Ver estado actual del proyecto
cat STATUS.md
```

---

## ⚠ Notas operacionales para sesiones futuras

- **Pricing**: Opus 4.7 [1m] cuesta ~3.5× más por turno cuando el contexto cruza 200K. Cerrar sesión y abrir nueva con `STATUS.md` + `INTEGRATION.md` es típicamente la mejor estrategia después de 30-40 mensajes densos.
- **Datos persistentes**: `data/raw/` y `data/processed/` están gitignored. Las imágenes se descargan y procesan en cada deploy de Streamlit Cloud.
- **Catálogo volcanes**: `src/volcanos.py` — 43 volcanes Chile, prioridad de 8.
- **Convenciones**: Kelvin para BT, WGS84 lat/lon, UTC timestamps. Coeficientes Planck siempre del NetCDF L1b (planck_fk1, fk2, bc1, bc2).
