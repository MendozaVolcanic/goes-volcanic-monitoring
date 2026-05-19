# Dockerfile para Hugging Face Spaces (sdk: docker).
#
# HF Spaces ya no muestra "Streamlit" como SDK nativo en la UI desde
# mayo 2026 — solo Gradio / Docker / Static. Por eso usamos Docker
# con la receta minima para correr el dashboard Streamlit.
#
# HF expone el contenedor en puerto 7860 (default Docker SDK).
# El comando final usa --server.address=0.0.0.0 + --server.headless=true
# para que Streamlit escuche en todas las interfaces sin tratar de
# abrir un browser.

FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema requeridas por cartopy, pyproj, rasterio:
# - libgeos-dev: geometria (cartopy, shapely)
# - libproj-dev: proyecciones (pyproj)
# - libgdal-dev: raster IO (rasterio)
# - gcc/g++: compilacion de wheels que no tienen binario
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev libproj-dev libgdal-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# HF runtime user (UID 1000) — sin esto puede haber permission issues
RUN useradd -m -u 1000 user
ENV PATH="/home/user/.local/bin:$PATH"
ENV HOME=/home/user

# Instalar deps primero (mejor cache layer)
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar el resto del repo
COPY --chown=user:user . .

USER user

EXPOSE 7860

# Streamlit en HF Spaces:
# - puerto 7860 (default HF Docker)
# - 0.0.0.0 para escuchar fuera del container
# - headless para no abrir browser
# - no auto-open browser en server side
# - enableCORS=false porque HF maneja CORS via su proxy
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
