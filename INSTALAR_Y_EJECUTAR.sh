#!/bin/bash
# ─── SETUP INICIAL DEL PROYECTO ───────────────────────────────────

echo ""
echo "=============================="
echo "  APP TRADING - SETUP INICIAL"
echo "=============================="

# 1. Crear entorno virtual Python
echo ""
echo "[1/3] Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
echo ""
echo "[2/3] Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Dependencias instaladas"

# 3. Descargar datos históricos
echo ""
echo "[3/3] Descargando datos históricos (puede tardar 10-20 min)..."
python3 src/01_descargar_datos_historicos.py

echo ""
echo "=============================="
echo "  SETUP COMPLETADO"
echo "=============================="
