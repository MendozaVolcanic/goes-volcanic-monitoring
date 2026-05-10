# Setup automatizado para servidor SERNAGEOMIN (Windows PowerShell).
# Ver docs/DEPLOY_LOCALHOST.md para guia completa.
#
# Uso (correr como admin si vas a registrar el servicio NSSM):
#   .\scripts\setup_localhost.ps1
#
# Variables ajustables al inicio del script.

param(
    [string]$InstallDir = "C:\georiesgos\goes-volcanic-monitoring",
    [string]$LogDir = "C:\georiesgos\logs",
    [int]$Port = 8501,
    [switch]$InstallService,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "==> GOES Dashboard Setup (localhost)" -ForegroundColor Cyan
Write-Host "  InstallDir:  $InstallDir"
Write-Host "  LogDir:      $LogDir"
Write-Host "  Port:        $Port"
Write-Host "  Service:     $InstallService"
Write-Host ""

# 1. Verificar Python 3.12
Write-Host "==> Verificando Python 3.12..." -ForegroundColor Cyan
$pyCmd = "py -3.12"
try {
    $pyVer = & py -3.12 --version
    Write-Host "  $pyVer OK"
} catch {
    Write-Error "Python 3.12 no encontrado. Instalar de python.org primero."
    exit 1
}

# 2. Clonar / actualizar repo
if (Test-Path $InstallDir) {
    Write-Host "==> Repo ya existe, actualizando..." -ForegroundColor Cyan
    Set-Location $InstallDir
    git pull origin main
} else {
    Write-Host "==> Clonando repo..." -ForegroundColor Cyan
    $parent = Split-Path $InstallDir -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    git clone https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git $InstallDir
    Set-Location $InstallDir
}

# 3. Crear venv
$venvPath = Join-Path $InstallDir ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "==> Creando venv..." -ForegroundColor Cyan
    py -3.12 -m venv $venvPath
}

# 4. Instalar dependencias
Write-Host "==> Instalando dependencias..." -ForegroundColor Cyan
& "$venvPath\Scripts\python.exe" -m pip install --upgrade pip
& "$venvPath\Scripts\pip.exe" install -r requirements.txt

# 5. Tests (opcional)
if (-not $SkipTests) {
    Write-Host "==> Corriendo tests..." -ForegroundColor Cyan
    & "$venvPath\Scripts\python.exe" -m pytest tests/ -q
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Tests fallaron — revisar antes de continuar"
    } else {
        Write-Host "  Tests OK" -ForegroundColor Green
    }
}

# 6. Crear log dir
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# 7. NSSM service (opcional)
if ($InstallService) {
    Write-Host "==> Registrando servicio Windows con NSSM..." -ForegroundColor Cyan
    $nssm = Get-Command nssm -ErrorAction SilentlyContinue
    if (-not $nssm) {
        Write-Error "NSSM no encontrado en PATH. Bajar de https://nssm.cc/ y poner nssm.exe en C:\Windows\System32\"
        exit 1
    }

    $svcName = "GoesDashboard"
    # Remover si existe
    nssm stop $svcName 2>$null
    nssm remove $svcName confirm 2>$null

    $streamlit = Join-Path $venvPath "Scripts\streamlit.exe"
    $args = "run dashboard/app.py --server.address=0.0.0.0 --server.port=$Port --server.headless=true"

    nssm install $svcName $streamlit
    nssm set $svcName AppParameters $args
    nssm set $svcName AppDirectory $InstallDir
    nssm set $svcName AppStdout "$LogDir\goes_stdout.log"
    nssm set $svcName AppStderr "$LogDir\goes_stderr.log"
    nssm set $svcName AppRotateFiles 1
    nssm set $svcName AppRotateBytes 10485760  # 10 MB rotation
    nssm set $svcName Start SERVICE_AUTO_START

    nssm start $svcName
    Start-Sleep -Seconds 3
    sc.exe query $svcName
    Write-Host "  Servicio $svcName instalado y corriendo." -ForegroundColor Green
}

Write-Host ""
Write-Host "==> DONE." -ForegroundColor Green
Write-Host ""
Write-Host "Para correr manualmente (sin servicio):"
Write-Host "  cd $InstallDir"
Write-Host "  .venv\Scripts\activate"
Write-Host "  streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$Port"
Write-Host ""
Write-Host "Acceder desde otra PC en la red interna:"
Write-Host "  http://<ip-de-este-servidor>:$Port"
Write-Host ""
if ($InstallService) {
    Write-Host "Comandos del servicio:"
    Write-Host "  nssm restart GoesDashboard      # despues de git pull"
    Write-Host "  nssm stop GoesDashboard"
    Write-Host "  nssm start GoesDashboard"
    Write-Host "  Get-Content $LogDir\goes_stdout.log -Tail 50  # ver logs"
}
