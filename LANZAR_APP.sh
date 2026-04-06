#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo ""
echo "=============================="
echo "  JST ALPHA - Iniciando..."
echo "=============================="
echo ""
echo "  Abriendo en: http://localhost:8501"
echo ""
streamlit run dashboard/app.py \
  --server.port 8501 \
  --server.headless false \
  --browser.gatherUsageStats false
