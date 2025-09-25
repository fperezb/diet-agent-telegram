#!/usr/bin/env python3
"""
Diet Agent - Versión simple para debugging
"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Variables globales
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "version": "simple"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook simple que responde a todos los mensajes"""
    try:
        update = request.get_json()
        logger.info(f"Update recibido: {update}")
        
        if update and 'message' in update:
            chat_id = update['message']['chat']['id']
            message_text = update['message'].get('text', '')
            
            logger.info(f"Mensaje: '{message_text}' de chat: {chat_id}")
            
            # Respuesta simple
            if message_text.startswith('/start'):
                response_text = "¡Hola! 👋 Soy tu Diet Agent.\n\nEnvíame una foto de comida y te ayudo con las calorías."
            elif message_text.startswith('/help'):
                response_text = "Comandos:\n/start - Iniciar\n/help - Ayuda\n\nEnvía fotos de comida para análisis."
            else:
                response_text = "📸 Envíame una foto de tu comida para analizarla."
            
            # Enviar respuesta
            send_message(chat_id, response_text)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"error": str(e)}), 500

def send_message(chat_id, text):
    """Enviar mensaje usando API de Telegram directamente"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        response = requests.post(url, json=data)
        logger.info(f"Respuesta enviada: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Mensaje enviado exitosamente")
        else:
            logger.error(f"Error enviando mensaje: {response.text}")
            
    except Exception as e:
        logger.error(f"Error en send_message: {e}")

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configurar webhook"""
    try:
        webhook_url = os.getenv('WEBHOOK_URL')
        url = f"{TELEGRAM_API_URL}/setWebhook"
        data = {"url": f"{webhook_url}/webhook"}
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return jsonify({"status": "success", "message": f"Webhook configurado en {webhook_url}/webhook"}), 200
        else:
            return jsonify({"error": response.text}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)