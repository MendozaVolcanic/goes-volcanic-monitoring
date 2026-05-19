#!/bin/bash
# Deploy a Hugging Face Spaces (mirror de Streamlit Cloud).
#
# HF rechaza archivos >10MB y carpetas grandes (data/, PDFs). Este script
# crea un branch temporal sin esos archivos y hace force-push solo de
# eso al Space. El branch main local NO se toca.
#
# Uso:
#   export HF_TOKEN="hf_..."        # generar en https://huggingface.co/settings/tokens
#   bash scripts/deploy_hf.sh
#
# Requiere git remote 'hf' configurado:
#   git remote add hf https://huggingface.co/spaces/mendozavolcanic/goes-volcanic-monitoring

set -e

if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN no seteado."
    echo "Generalo en https://huggingface.co/settings/tokens (type Write) y:"
    echo "  export HF_TOKEN='hf_...'"
    exit 1
fi

# Branch limpio sin archivos pesados
TEMP_BRANCH="hf-deploy-$(date +%s)"
echo "==> Creando branch temporal $TEMP_BRANCH desde main..."
git checkout -b "$TEMP_BRANCH"

echo "==> Removiendo archivos pesados del staging (no del filesystem)..."
git rm --cached -r data/ docs/papers_links/ docs/manuales_pdf/ "Logs pruebas/" 2>/dev/null || true
git rm --cached docs/*.pdf 2>/dev/null || true

echo "==> Commit snapshot HF..."
git commit -m "HF Spaces deploy snapshot (excluye data/ y PDFs)" --quiet || true

echo "==> Push --force a HF Space..."
PUSH_URL="https://mendozavolcanic:${HF_TOKEN}@huggingface.co/spaces/mendozavolcanic/goes-volcanic-monitoring"
git push "$PUSH_URL" "$TEMP_BRANCH:main" --force

echo "==> Limpiando branch temporal..."
git checkout main -f
git branch -D "$TEMP_BRANCH"

echo ""
echo "DONE. Build en https://huggingface.co/spaces/mendozavolcanic/goes-volcanic-monitoring"
echo "App en https://mendozavolcanic-goes-volcanic-monitoring.hf.space"
