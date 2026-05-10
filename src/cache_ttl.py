"""TTL constants para `@st.cache_data` en todo el dashboard.

Centraliza los valores TTL usados en cada vista para que sean coherentes
entre paginas. Usar el nombre semantico (`TTL_FRAME_IMAGE`) en vez del
numero magico (`7200`) hace evidente la intencion y permite ajustar
TODAS las llamadas de un tipo en un solo lugar.

Filosofia:
- TS LIST (latest_times.json): cambia cada 10 min, queremos detectar nuevo
  scan rapido → TTL corto (15-30s).
- FRAME (PNG de un ts especifico): el frame NO cambia una vez publicado
  (es un asset estatico) → TTL largo (2h+).
- HOTSPOTS NRT: NOAA FDCF actualiza c/10 min → TTL 5 min.
- VOLCAT NRT: SSEC RealEarth actualiza c/10 min → TTL 5 min.
- WIND GFS: NOAA publica cada 6 horas → TTL 1 hora.
- MANIFESTS de releases (animation_cache, hires): cambian segun cron del
  workflow (1h o 30 min) → TTL 2 min para detectar pronto.
- HISTORIC (backfill): los datos NUNCA cambian (eventos pasados) → TTL alto.
"""

# Timestamps / scan times (JSON pequeño, queremos refresh rapido)
TTL_TIMESTAMPS_LIST = 30          # Modo Guardia, Mosaico, Comparador
TTL_TIMESTAMPS_LIST_FAST = 15     # Live viewer (la pagina principal)

# Frames de imagenes RAMMB (un PNG asociado a un ts especifico).
# El frame NUNCA cambia una vez publicado por RAMMB → TTL muy largo.
TTL_FRAME_IMAGE = 7200            # 2 horas

# Productos NRT que cambian cada 10 min
TTL_HOTSPOTS = 300                # FDCF NRT (5 min)
TTL_VOLCAT = 300                  # SSEC RealEarth NRT (5 min)

# Otros productos
TTL_WIND_GFS = 3600               # GFS publica cada 6h, cache 1h
TTL_MANIFEST = 120                # Manifests JSON pequeños (animation, hires)

# Historico (datos que ya no cambian)
TTL_HISTORIC = 3600               # Backfill events, archive RAMMB
TTL_HISTORIC_LONG = 7200          # Hot spots historicos, etc.
