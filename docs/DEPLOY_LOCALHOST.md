# Deploy localhost — Servidor Observatorio SERNAGEOMIN

Guía paso-a-paso para correr el dashboard en un servidor del observatorio
(Windows o Linux) sin depender de Streamlit Cloud. Útil cuando:

- Necesitamos uptime garantizado (Streamlit Cloud free tiene sleep mode + restarts).
- Queremos acceso desde la red interna sin pasar por internet.
- Vamos a iterar cambios rápidos sin esperar redeploy de Streamlit Cloud.

## Requisitos

- **Python 3.12** (estable, recomendado por el proyecto — ver `runtime.txt`).
  - Windows: descargar de python.org, instalar con "Add to PATH".
  - Linux: `apt install python3.12 python3.12-venv` (Ubuntu/Debian) o equivalente.
- **Git** instalado.
- **~2 GB de espacio libre** (código + cache local de tiles RAMMB).
- **Internet outbound** (para acceder a S3 NOAA y RAMMB CIRA).
- **Puerto 8501 libre** (el que usa Streamlit por defecto).

## Setup en 6 pasos (Windows)

```powershell
# 1. Clonar el repo en C:\georiesgos\goes-volcanic-monitoring (o donde prefieras)
cd C:\georiesgos
git clone https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git
cd goes-volcanic-monitoring

# 2. Crear entorno virtual aislado (recomendado)
py -3.12 -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias (hay 2 archivos: el principal incluye Streamlit + Plotly)
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verificar que los tests pasan
python -m pytest tests/ -q
# Debería mostrar: 44 passed in ~3s

# 5. Correr el dashboard local
streamlit run dashboard/app.py

# 6. Abrir en navegador
# http://localhost:8501
```

## Setup en 6 pasos (Linux/macOS)

```bash
# 1. Clonar
cd /opt
git clone https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git
cd goes-volcanic-monitoring

# 2. Entorno virtual
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Tests
python -m pytest tests/ -q

# 5. Correr
streamlit run dashboard/app.py

# 6. Acceder desde otra máquina en la red interna:
# http://<ip-del-servidor>:8501
```

> Si Streamlit no escucha en todas las interfaces, agregar
> `--server.address=0.0.0.0` al comando.

## Acceso desde otras máquinas del observatorio

Por defecto Streamlit escucha en `127.0.0.1` (solo local). Para que
otros equipos de la red puedan acceder:

```bash
streamlit run dashboard/app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true
```

Después acceder desde otras máquinas a `http://<ip-del-servidor>:8501`.

> Verificar que el firewall permita TCP 8501 entrante.

## Mantener corriendo 24/7 (auto-arranque)

### Windows: NSSM (Non-Sucking Service Manager)

NSSM permite registrar Streamlit como servicio Windows que arranca con el
sistema y se reinicia si crashea.

```powershell
# 1. Bajar NSSM de https://nssm.cc/download
# 2. Descomprimir y mover nssm.exe a C:\Windows\System32\

# 3. Registrar el servicio (correr como administrador)
nssm install GoesDashboard
# En el GUI:
#   Path: C:\georiesgos\goes-volcanic-monitoring\.venv\Scripts\streamlit.exe
#   Startup directory: C:\georiesgos\goes-volcanic-monitoring
#   Arguments: run dashboard/app.py --server.address=0.0.0.0 --server.headless=true
# Pestaña "I/O":
#   Output (stdout): C:\georiesgos\logs\goes_stdout.log
#   Error (stderr):  C:\georiesgos\logs\goes_stderr.log

# 4. Iniciar
nssm start GoesDashboard

# 5. Verificar
sc query GoesDashboard
# Debería decir RUNNING

# Comandos utiles:
nssm restart GoesDashboard   # Reinicio (después de git pull)
nssm stop GoesDashboard
nssm remove GoesDashboard    # Desinstalar
```

### Linux: systemd unit

```ini
# /etc/systemd/system/goes-dashboard.service
[Unit]
Description=GOES Volcanic Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=ovdas
WorkingDirectory=/opt/goes-volcanic-monitoring
Environment="PATH=/opt/goes-volcanic-monitoring/.venv/bin"
ExecStart=/opt/goes-volcanic-monitoring/.venv/bin/streamlit run dashboard/app.py \
    --server.address=0.0.0.0 \
    --server.headless=true
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/goes-dashboard/stdout.log
StandardError=append:/var/log/goes-dashboard/stderr.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/goes-dashboard
sudo systemctl daemon-reload
sudo systemctl enable goes-dashboard
sudo systemctl start goes-dashboard
sudo systemctl status goes-dashboard   # verificar
```

## Actualizar el dashboard (workflow típico)

Cuando hay cambios nuevos en GitHub:

```bash
cd /opt/goes-volcanic-monitoring         # o C:\georiesgos\goes-volcanic-monitoring
git pull origin main
.venv/bin/pip install -r requirements.txt --upgrade   # si cambió
sudo systemctl restart goes-dashboard    # Linux
nssm restart GoesDashboard               # Windows
```

> Streamlit detecta cambios en archivos automáticamente y refresca la
> página. El restart formal solo es necesario después de actualizar
> dependencias.

## Cache local (opcional, mejora performance)

El dashboard usa `@st.cache_data` con TTLs cortos por defecto (ver
`src/cache_ttl.py`). Para evitar re-bajar tiles de RAMMB/SSEC repetidos
entre sesiones del browser, opcionalmente:

```bash
# Linux/macOS: aumentar persist cache de Streamlit
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << 'EOF'
[server]
maxUploadSize = 200

[client]
caching = true

[browser]
gatherUsageStats = false
EOF
```

## Diferencias clave vs Streamlit Cloud

| Aspecto | Streamlit Cloud (free) | Localhost observatorio |
|---|---|---|
| Uptime | ~95% (sleep mode + restarts) | 99%+ (controlado por sysadmin) |
| Latencia | Depende de Cloudflare + cold start | LAN interna (1 ms) |
| Python version | Definida por `runtime.txt` | Vos elegís |
| Acceso | Internet público con URL pública | LAN interna (o VPN) |
| Costo | $0 | $0 + electricidad servidor |
| Deploy | Git push automático | Git pull + restart manual |
| Workflows GitHub Actions | Funcionan igual | Funcionan igual (independientes del deploy) |

> Los GitHub Actions (animation_cache, hires_visible, etc.) corren en
> infraestructura de GitHub independientemente de dónde se hospede el
> dashboard. Localhost simplemente lee los releases generados igual que
> Streamlit Cloud.

## Troubleshooting

### `KeyError: 'dashboard.style'` (race condition Python 3.14)
- **Causa**: usaste Python 3.14 que tiene bug en importlib.
- **Fix**: cambiá a Python 3.12 (`pyenv install 3.12` o el equivalente).

### Streamlit no inicia: `address already in use`
- Otro proceso ya escucha en 8501. Cambiá puerto: `--server.port=8502`.
- O matá el proceso anterior: Windows `netstat -ano | findstr 8501`,
  Linux `lsof -i :8501`.

### Slow first load
- El primer fetch de RAMMB tiles tarda 30-60s (descarga + cache).
- Después es rápido por cache de Streamlit.

### `ImportError` después de `git pull`
- Las dependencias cambiaron. Correr:
  `.venv/bin/pip install -r requirements.txt --upgrade`.

### Dashboard se cae después de 1 hora
- Probablemente es un fragment de auto-refresh con bug.
- Revisar logs: `journalctl -u goes-dashboard -n 100` (Linux) o el log de NSSM.

## Contacto

- Owner técnico del proyecto: Nicolás Mendoza (SERNAGEOMIN).
- Bugs/issues: GitHub https://github.com/MendozaVolcanic/goes-volcanic-monitoring/issues
