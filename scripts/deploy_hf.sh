#!/bin/bash
# Deploy a Hugging Face Spaces (mirror de Streamlit Cloud).
#
# HF rechaza archivos >10MB (PDFs grandes en docs/) y archivos en commits
# pasados de la historia del branch. Por eso usamos ORPHAN branch
# (sin historia) con solo los archivos esenciales.
#
# Tambien: `.dockerignore` con `*.txt` excluiria requirements.txt y
# runtime.txt. Asegurate que solo matchee patterns especificos como
# `logs-mendozavolcanic-*.txt`.
#
# Uso:
#   export HF_TOKEN="hf_..."        # generar en https://huggingface.co/settings/tokens
#   bash scripts/deploy_hf.sh
#
# El branch main local NO se toca. El script crea un orphan branch
# temporal, hace force push a HF/main, y vuelve a main.

set -e

if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN no seteado."
    echo "Generalo en https://huggingface.co/settings/tokens (type Write) y:"
    echo "  export HF_TOKEN='hf_...'"
    exit 1
fi

HF_SPACE="mendozavolcanic/goes-volcanic-monitoring"
TEMP_BRANCH="hf-deploy-$(date +%s)"

echo "==> Asegurando que estamos en main..."
git checkout main

echo "==> Creando ORPHAN branch $TEMP_BRANCH (sin historia, evita rechazo HF por PDFs en commits viejos)..."
git checkout --orphan "$TEMP_BRANCH"

echo "==> Limpiando staging (todo desaged)..."
git rm -rf --cached . >/dev/null 2>&1 || true

echo "==> Agregando SOLO archivos esenciales para el Space..."
git add \
    Dockerfile \
    .dockerignore \
    .streamlit/config.toml \
    requirements.txt \
    requirements_actions.txt \
    runtime.txt \
    .python-version \
    pyproject.toml \
    README.md \
    dashboard/ \
    src/ \
    tests/ \
    data/hotspots_daily.json \
    data/frp_timeline.json \
    scripts/build_hires_cache.py \
    scripts/build_animation_cache.py \
    scripts/build_backfill.py \
    scripts/build_hotspots_daily.py \
    scripts/build_frp_timeline.py 2>&1 | tail -3

echo "==> Commit snapshot..."
git commit -m "HF Spaces deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)" --quiet

echo "==> Force push a HF Space ($HF_SPACE)..."
git push "https://mendozavolcanic:${HF_TOKEN}@huggingface.co/spaces/${HF_SPACE}" \
    "${TEMP_BRANCH}:main" --force

echo "==> Limpiando branch temporal..."
git checkout main -f
git branch -D "$TEMP_BRANCH"

echo ""
echo "DONE. Build en https://huggingface.co/spaces/${HF_SPACE}"
echo "App en https://mendozavolcanic-goes-volcanic-monitoring.hf.space"
echo ""
echo "Monitorear con:"
echo "  curl -s -H \"Authorization: Bearer \$HF_TOKEN\" \\"
echo "    \"https://huggingface.co/api/spaces/${HF_SPACE}/runtime\" | python -m json.tool"
