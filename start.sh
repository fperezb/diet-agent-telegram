#!/bin/bash

# Script de inicio rápido para Diet Agent

echo "🤖 Diet Agent - Bot de Telegram para Análisis Nutricional"
echo "=========================================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Verificar archivos de configuración
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "📝 Copiando plantilla..."
    cp .env.example .env
    echo ""
    echo "🔧 IMPORTANTE: Edita el archivo .env con tus tokens:"
    echo "   - TELEGRAM_BOT_TOKEN (desde @BotFather)"
    echo "   - OPENAI_API_KEY (desde platform.openai.com)"
    echo ""
    echo "📖 Instrucciones completas en README.md"
    exit 1
fi

echo ""
echo "🚀 ¿Cómo quieres ejecutar el bot?"
echo "1) Modo polling (desarrollo local)"
echo "2) Modo webhook (para deploy en servidor)"
echo ""
read -p "Selecciona una opción (1-2): " option

case $option in
    1)
        echo "🏃 Ejecutando en modo polling..."
        python3 main.py
        ;;
    2)
        echo "🌐 Ejecutando en modo webhook..."
        python3 app_webhook.py
        ;;
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac