#!/usr/bin/env python3
"""
Diet Agent - Flask Webhook Version
Versión para deploy en servidores usando webhooks
"""

import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes,
    filters
)
from dotenv import load_dotenv
import asyncio
from threading import Thread

from food_analyzer import FoodAnalyzer
from calorie_calculator import CalorieCalculator

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Crear app Flask
app = Flask(__name__)

class DietAgentWebhook:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurada en las variables de entorno")
        
        self.food_analyzer = FoodAnalyzer()
        self.calorie_calculator = CalorieCalculator()
        self.bot = Bot(self.bot_token)
        
        # Configurar la aplicación de Telegram
        self.application = ApplicationBuilder().token(self.bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configurar handlers del bot"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.analyze_food_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida"""
        logger.info(f"Comando /start recibido de usuario: {update.effective_user.id}")
        
        welcome_message = (
            "¡Hola! 👋 Soy tu Agente Dietético personal\n\n"
            "📸 Envíame una foto de tu comida y te diré:\n"
            "• Qué alimentos identifico\n"
            "• Las calorías aproximadas\n"
            "• Información nutricional básica\n\n"
            "🌐 **Estoy funcionando en la nube!** 🌐\n\n"
            "¡Empezemos! Envía una foto de tu comida 🍽️"
        )
        
        try:
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            logger.info("Mensaje de bienvenida enviado exitosamente")
        except Exception as e:
            logger.error(f"Error enviando mensaje de bienvenida: {e}")
            # Intentar sin markdown como fallback
            await update.message.reply_text(welcome_message.replace('*', ''))
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help - Instrucciones de uso"""
        help_text = (
            "🤖 *Cómo usar el Diet Agent:*\n\n"
            "1. Envía una foto de tu comida 📸\n"
            "2. Espera el análisis automático 🧠\n"
            "3. Recibe información sobre:\n"
            "   • Alimentos identificados 🥗\n"
            "   • Calorías aproximadas 🔥\n"
            "   • Consejos nutricionales 💡\n\n"
            "*Comandos disponibles:*\n"
            "/start - Iniciar el bot\n"
            "/help - Mostrar esta ayuda\n"
            "/stats - Ver estadísticas de hoy\n\n"
            "🌐 Bot ejecutándose en modo webhook\n"
            "¡Disfruta de una alimentación más consciente! 🌟"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def analyze_food_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analizar foto de comida enviada por el usuario"""
        try:
            # Enviar mensaje de "procesando"
            processing_msg = await update.message.reply_text(
                "🧠 Analizando tu comida... \n⏳ Esto puede tomar unos segundos"
            )
            
            # Obtener la foto de mayor calidad
            photo = update.message.photo[-1]
            
            # Descargar la foto
            file = await context.bot.get_file(photo.file_id)
            photo_path = f"temp_photos/{photo.file_id}.jpg"
            
            # Crear directorio si no existe
            os.makedirs("temp_photos", exist_ok=True)
            
            # Descargar imagen
            await file.download_to_drive(photo_path)
            
            # Analizar la imagen con IA
            food_analysis = await self.food_analyzer.analyze_image(photo_path)
            
            if food_analysis:
                # Calcular calorías
                calorie_info = self.calorie_calculator.calculate_calories(food_analysis)
                
                # Generar respuesta
                response = self._format_analysis_response(food_analysis, calorie_info)
                
                # Eliminar mensaje de procesando
                await processing_msg.delete()
                
                # Enviar resultado
                await update.message.reply_text(response, parse_mode='Markdown')
                
            else:
                await processing_msg.edit_text(
                    "❌ No pude identificar comida en esta imagen.\n"
                    "Por favor, intenta con una foto más clara de tu comida."
                )
            
            # Limpiar archivo temporal
            if os.path.exists(photo_path):
                os.remove(photo_path)
                
        except Exception as e:
            logger.error(f"Error analizando foto: {e}")
            await update.message.reply_text(
                "🚫 Ocurrió un error al analizar la imagen.\n"
                "Por favor, intenta nuevamente."
            )
    
    def _format_analysis_response(self, food_analysis, calorie_info):
        """Formatear la respuesta del análisis"""
        response = "🍽️ *Análisis de tu comida:*\n\n"
        
        # Alimentos identificados
        response += "📋 *Alimentos identificados:*\n"
        for food in food_analysis.get('foods', []):
            response += f"• {food['name']} ({food['confidence']:.0%})\n"
        
        response += f"\n🔥 *Calorías totales estimadas:* {calorie_info['total_calories']} kcal\n\n"
        
        # Desglose nutricional
        if calorie_info.get('breakdown'):
            response += "📊 *Desglose nutricional:*\n"
            for nutrient, value in calorie_info['breakdown'].items():
                response += f"• {nutrient}: {value}\n"
        
        # Consejos
        if calorie_info.get('tips'):
            response += f"\n💡 *Consejo:* {calorie_info['tips']}"
        
        return response
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar estadísticas del día"""
        stats_text = (
            "📊 *Estadísticas de hoy:*\n\n"
            "🔥 Calorías totales: 0 kcal\n"
            "🍽️ Comidas analizadas: 0\n"
            "⏰ Última comida: --:--\n\n"
            "🌐 Servido desde la nube ☁️\n"
            "💡 ¡Envía fotos de tus comidas para ver tus estadísticas!"
        )
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto"""
        await update.message.reply_text(
            "📸 Por favor, envía una foto de tu comida para analizarla.\n"
            "Si necesitas ayuda, usa /help"
        )
    
    async def process_update(self, update_data):
        """Procesar update de Telegram"""
        try:
            logger.info(f"Procesando update: {update_data}")
            update = Update.de_json(update_data, self.bot)
            
            if update and update.message:
                logger.info(f"Mensaje recibido: {update.message.text if update.message.text else 'foto/archivo'}")
            
            await self.application.process_update(update)
            logger.info("Update procesado exitosamente")
        except Exception as e:
            logger.error(f"Error procesando update: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

# Crear instancia global
diet_agent = DietAgentWebhook()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para recibir updates de Telegram"""
    try:
        update_data = request.get_json()
        logger.info(f"Webhook recibido: {update_data}")
        
        # Procesar el update de forma síncrona pero rápida
        if update_data:
            # Crear un nuevo loop para esta request
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Procesar el update
                loop.run_until_complete(diet_agent.process_update(update_data))
            except Exception as e:
                logger.error(f"Error procesando update: {e}")
            finally:
                loop.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Diet Agent Webhook",
        "version": "1.0.0"
    }), 200

@app.route('/debug', methods=['GET'])
def debug_env():
    """Debug endpoint para verificar variables de entorno"""
    return jsonify({
        "telegram_token_set": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
        "openai_key_set": bool(os.getenv('OPENAI_API_KEY')),
        "webhook_url_set": bool(os.getenv('WEBHOOK_URL')),
        "port": os.getenv('PORT', 'not_set')
    }), 200

@app.route('/test_bot', methods=['GET'])
def test_bot():
    """Endpoint para probar que el bot funciona"""
    try:
        # Obtener información del bot
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_bot_info():
            bot_info = await diet_agent.bot.get_me()
            return {
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "bot_name": bot_info.first_name,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages
            }
        
        bot_data = loop.run_until_complete(get_bot_info())
        loop.close()
        
        return jsonify({
            "status": "bot_connected",
            "bot_info": bot_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error probando bot: {e}")
        return jsonify({
            "status": "bot_error", 
            "error": str(e)
        }), 500

@app.route('/send_test_message/<chat_id>', methods=['GET'])
def send_test_message(chat_id):
    """Enviar mensaje de prueba a un chat específico"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_message():
            await diet_agent.bot.send_message(
                chat_id=int(chat_id),
                text="🤖 ¡Mensaje de prueba desde el servidor!\n\nSi recibes esto, la conexión funciona correctamente."
            )
            return True
        
        result = loop.run_until_complete(send_message())
        loop.close()
        
        return jsonify({
            "status": "message_sent",
            "chat_id": chat_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error enviando mensaje de prueba: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Obtener información del webhook configurado"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_webhook_info():
            webhook_info = await diet_agent.bot.get_webhook_info()
            return {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
                "last_error_message": webhook_info.last_error_message,
                "max_connections": webhook_info.max_connections,
                "allowed_updates": webhook_info.allowed_updates
            }
        
        webhook_data = loop.run_until_complete(get_webhook_info())
        loop.close()
        
        return jsonify({
            "status": "success",
            "webhook_info": webhook_data,
            "expected_webhook_url": f"{os.getenv('WEBHOOK_URL', 'NOT_SET')}/webhook"
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo información del webhook: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configurar webhook de Telegram"""
    try:
        webhook_url = os.getenv('WEBHOOK_URL')
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL no configurada"}), 400
        
        # Configurar webhook
        response = diet_agent.bot.set_webhook(url=f"{webhook_url}/webhook")
        
        if response:
            return jsonify({
                "status": "success",
                "message": f"Webhook configurado en {webhook_url}/webhook"
            }), 200
        else:
            return jsonify({"error": "No se pudo configurar el webhook"}), 500
            
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)