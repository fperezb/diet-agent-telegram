#!/usr/bin/env python3
"""
Diet Agent - Bot de Telegram para análisis nutricional de comidas
Analiza fotos de comida e identifica alimentos y calorías
"""

import os
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes,
    filters
)
from dotenv import load_dotenv

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

class DietAgent:
    def __init__(self):
        self.food_analyzer = FoodAnalyzer()
        self.calorie_calculator = CalorieCalculator()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida"""
        welcome_message = (
            "¡Hola! 👋 Soy tu Agente Dietético personal\n\n"
            "📸 Envíame una foto de tu comida y te diré:\n"
            "• Qué alimentos identifico\n"
            "• Las calorías aproximadas\n"
            "• Información nutricional básica\n\n"
            "¡Empezemos! Envía una foto de tu comida 🍽️"
        )
        await update.message.reply_text(welcome_message)
    
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
        # TODO: Implementar sistema de estadísticas
        stats_text = (
            "📊 *Estadísticas de hoy:*\n\n"
            "🔥 Calorías totales: 0 kcal\n"
            "🍽️ Comidas analizadas: 0\n"
            "⏰ Última comida: --:--\n\n"
            "💡 ¡Envía fotos de tus comidas para ver tus estadísticas!"
        )
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto"""
        await update.message.reply_text(
            "📸 Por favor, envía una foto de tu comida para analizarla.\n"
            "Si necesitas ayuda, usa /help"
        )

def main():
    """Función principal"""
    # Verificar token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
        return
    
    # Crear instancia del agente
    diet_agent = DietAgent()
    
    # Crear aplicación del bot
    app = ApplicationBuilder().token(bot_token).build()
    
    # Registrar handlers
    app.add_handler(CommandHandler("start", diet_agent.start))
    app.add_handler(CommandHandler("help", diet_agent.help_command))
    app.add_handler(CommandHandler("stats", diet_agent.stats_command))
    app.add_handler(MessageHandler(filters.PHOTO, diet_agent.analyze_food_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, diet_agent.handle_text))
    
    # Iniciar bot
    logger.info("🤖 Diet Agent iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main()