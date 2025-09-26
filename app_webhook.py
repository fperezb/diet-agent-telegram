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
from datetime import datetime

from food_analyzer import FoodAnalyzer
from calorie_calculator import CalorieCalculator
from diet_database import DietDatabase

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
        
        # Cargar IDs de usuarios autorizados
        allowed_ids_str = os.getenv('ALLOWED_USER_IDS', '')
        self.allowed_user_ids = set()
        if allowed_ids_str:
            try:
                self.allowed_user_ids = set(int(id.strip()) for id in allowed_ids_str.split(',') if id.strip())
                logger.info(f"Usuarios autorizados cargados: {len(self.allowed_user_ids)} usuarios")
            except ValueError as e:
                logger.error(f"Error parsing ALLOWED_USER_IDS: {e}")
        else:
            logger.warning("ALLOWED_USER_IDS no configurada - el bot estará abierto a todos los usuarios")
        
        self.food_analyzer = FoodAnalyzer()
        self.calorie_calculator = CalorieCalculator()
        self.database = DietDatabase()
        self.bot = Bot(self.bot_token)
        
        # Configurar la aplicación de Telegram
        self.application = ApplicationBuilder().token(self.bot_token).build()
        self._setup_handlers()
        self._initialized = False
    
    async def initialize(self):
        """Inicializar la aplicación y bot de manera asíncrona"""
        if not self._initialized:
            # Inicializar el bot primero
            await self.bot.initialize()
            # Luego inicializar la aplicación
            await self.application.initialize()
            self._initialized = True
            logger.info("Bot y aplicación de Telegram inicializados correctamente")
    
    async def shutdown(self):
        """Cerrar recursos de manera limpia"""
        if self._initialized:
            await self.application.shutdown()
            await self.bot.shutdown()
            self._initialized = False
            logger.info("Bot y aplicación cerrados correctamente")
    
    def is_user_authorized(self, user_id: int) -> bool:
        """Verificar si el usuario está autorizado para usar el bot"""
        # Si no hay lista de usuarios autorizados, permitir a todos
        if not self.allowed_user_ids:
            return True
        return user_id in self.allowed_user_ids
    
    async def send_unauthorized_message(self, update: Update):
        """Enviar mensaje cuando el usuario no está autorizado"""
        unauthorized_msg = (
            "🚫 *Acceso no autorizado*\n\n"
            "Lo siento, no tienes permisos para usar este bot.\n"
            "Si crees que esto es un error, contacta al administrador.\n\n"
            f"Tu ID de usuario: `{update.effective_user.id}`"
        )
        try:
            await update.message.reply_text(unauthorized_msg, parse_mode='Markdown')
        except Exception:
            # Fallback sin markdown
            await update.message.reply_text(unauthorized_msg.replace('*', '').replace('`', ''))
        
        logger.warning(f"Usuario no autorizado intentó acceder: {update.effective_user.id} (@{update.effective_user.username})")
    
    def _setup_handlers(self):
        """Configurar handlers del bot"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("setmeta", self.set_goal_command))
        self.application.add_handler(CommandHandler("mensual", self.monthly_stats_command))
        self.application.add_handler(CommandHandler("clear_my_data", self.clear_user_data_command))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.analyze_food_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida"""
        user_id = update.effective_user.id
        logger.info(f"Comando /start recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
        
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
        user_id = update.effective_user.id
        logger.info(f"Comando /help recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
            
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
            "/stats - Ver estadísticas de hoy\n"
            "/setmeta - Configurar meta diaria de calorías\n"
            "/mensual - Ver reporte del mes actual\n\n"
            "🌐 Bot ejecutándose en modo webhook\n"
            "¡Disfruta de una alimentación más consciente! 🌟"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def analyze_food_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analizar foto de comida enviada por el usuario"""
        user_id = update.effective_user.id
        logger.info(f"Foto recibida de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
            
        try:
            # Enviar mensaje de "procesando"
            processing_msg = await update.message.reply_text(
                "🧠 Analizando tu comida... \n⏳ Esto puede tomar unos segundos"
            )
            
            # Obtener la foto de mayor calidad
            photo = update.message.photo[-1]
            
            # Capturar el texto/caption que escribió el usuario con la foto
            user_text = update.message.caption or ""
            logger.info(f"Usuario escribió con la foto: '{user_text}'")
            
            # Descargar la foto
            file = await context.bot.get_file(photo.file_id)
            photo_path = f"temp_photos/{photo.file_id}.jpg"
            
            # Crear directorio si no existe
            os.makedirs("temp_photos", exist_ok=True)
            
            # Descargar imagen
            await file.download_to_drive(photo_path)
            
            # Analizar la imagen con IA incluyendo el texto del usuario
            food_analysis = await self.food_analyzer.analyze_image(photo_path, user_text)
            
            if food_analysis:
                # Calcular calorías
                calorie_info = self.calorie_calculator.calculate_calories(food_analysis)
                
                # Verificar meta calórica ANTES de guardar
                goal_check = self.database.check_calorie_limit(user_id, calorie_info['total_calories'])
                
                # Guardar en base de datos con macronutrientes
                try:
                    # Extraer macronutrientes del breakdown
                    breakdown = calorie_info.get('breakdown', {})
                    protein = float(breakdown.get('Proteína', '0g').replace('g', ''))
                    carbs = float(breakdown.get('Carbohidratos', '0g').replace('g', ''))
                    fat = float(breakdown.get('Grasas', '0g').replace('g', ''))
                    
                    meal_id = self.database.save_meal(
                        user_id=user_id,
                        foods=food_analysis.get('foods', []),
                        total_calories=calorie_info['total_calories'],
                        total_protein=protein,
                        total_carbs=carbs,
                        total_fat=fat,
                        photo_file_id=photo.file_id
                    )
                    logger.info(f"Comida guardada en BD: meal_id={meal_id} con macros P:{protein}g C:{carbs}g F:{fat}g")
                except Exception as e:
                    logger.error(f"Error guardando comida en BD: {e}")
                
                # Obtener total diario actualizado
                daily_stats = self.database.get_daily_calories(user_id)
                
                # Generar respuesta con totales diarios y alertas de meta
                response = self._format_analysis_response(food_analysis, calorie_info, daily_stats, goal_check)
                
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
    
    def _format_analysis_response(self, food_analysis, calorie_info, daily_stats=None, goal_check=None):
        """Formatear la respuesta del análisis"""
        response = "🍽️ *Análisis de tu comida:*\n\n"
        
        # Alimentos identificados
        response += "📋 *Alimentos identificados:*\n"
        for food in food_analysis.get('foods', []):
            response += f"• {food['name']} ({food['confidence']:.0%})\n"
        
        response += f"\n🔥 *Esta comida:* {calorie_info['total_calories']} kcal\n"
        
        # Agregar totales diarios si están disponibles
        if daily_stats and daily_stats.get('total_calories', 0) > 0:
            response += f"📊 *Total del día:* {daily_stats['total_calories']} kcal\n"
            response += f"🍽️ *Comidas registradas hoy:* {daily_stats['meal_count']}\n"
            
            # Agregar macronutrientes diarios
            if daily_stats.get('total_protein', 0) > 0:
                response += f"📈 *Macros del día:*\n"
                response += f"• Proteína: {daily_stats['total_protein']}g\n"
                response += f"• Carbohidratos: {daily_stats['total_carbs']}g\n"
                response += f"• Grasas: {daily_stats['total_fat']}g\n"
        
        # Agregar información de meta y alertas
        if goal_check and goal_check.get('has_goal'):
            response += f"\n🎯 *Meta diaria:* {goal_check['daily_goal']} kcal\n"
            response += f"📈 *Progreso:* {goal_check['projected_percentage']}% de tu meta\n"
            
            if goal_check['remaining_calories'] > 0:
                response += f"✨ *Calorías restantes:* {goal_check['remaining_calories']} kcal\n"
            
            # Mensaje de alerta según el estado
            response += f"\n{goal_check['message']}\n"
            
            # Consejos adicionales según el estado
            if goal_check['status'] == 'exceed':
                response += "\n💡 *Consejos:*\n"
                response += "• Considera comidas más ligeras el resto del día\n"
                response += "• Aumenta tu actividad física\n"
                response += "• Bebe más agua para sentirte saciado\n"
            elif goal_check['status'] == 'warning':
                response += "\n💡 Planifica bien tus próximas comidas para mantenerte en meta.\n"
        
        response += "\n"
        
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
        user_id = update.effective_user.id
        logger.info(f"Comando /stats recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
        
        try:
            # Obtener estadísticas reales de la base de datos
            daily_stats = self.database.get_daily_calories(user_id)
            
            # Obtener meta del usuario
            user_goal = self.database.get_user_goal(user_id)
            
            stats_text = f"📊 *Estadísticas de hoy:*\n\n"
            stats_text += f"🔥 *Calorías consumidas:* {daily_stats['total_calories']} kcal\n"
            
            # Mostrar información de meta si existe
            if user_goal:
                goal_calories = user_goal['daily_calorie_goal']
                percentage = (daily_stats['total_calories'] / goal_calories) * 100 if goal_calories > 0 else 0
                remaining = max(0, goal_calories - daily_stats['total_calories'])
                
                stats_text += f"🎯 *Meta diaria:* {goal_calories} kcal\n"
                stats_text += f"📈 *Progreso:* {percentage:.1f}%\n"
                
                if remaining > 0:
                    stats_text += f"✨ *Calorías restantes:* {remaining} kcal\n"
                else:
                    excess = daily_stats['total_calories'] - goal_calories
                    stats_text += f"⚠️ *Exceso:* {excess} kcal\n"
                
                # Indicador visual del progreso
                if percentage < 50:
                    stats_text += f"📊 {'█' * int(percentage/10)}{'░' * (10-int(percentage/10))} 💚\n"
                elif percentage < 80:
                    stats_text += f"📊 {'█' * int(percentage/10)}{'░' * (10-int(percentage/10))} 💛\n"
                elif percentage < 100:
                    stats_text += f"📊 {'█' * int(percentage/10)}{'░' * (10-int(percentage/10))} 🧡\n"
                else:
                    stats_text += f"📊 {'█' * 10} 🔴\n"
            else:
                stats_text += f"🎯 *Meta:* No configurada (usa /setmeta)\n"
            
            stats_text += f"🍽️ *Comidas analizadas:* {daily_stats['meal_count']}\n"
            
            if daily_stats['last_meal_time']:
                stats_text += f"⏰ *Última comida:* {daily_stats['last_meal_time']}\n"
            else:
                stats_text += f"⏰ *Última comida:* --:--\n"
            
            # Mostrar desglose de comidas si hay
            if daily_stats['meals']:
                stats_text += f"\n📝 *Detalle del día:*\n"
                for i, meal in enumerate(daily_stats['meals'], 1):
                    stats_text += f"{i}. *{meal['time']}h* - {meal['calories']} kcal\n"
                    stats_text += f"   {meal['foods']}\n"
            
            stats_text += f"\n🌐 Servido desde la nube ☁️"
            
            if daily_stats['meal_count'] == 0:
                stats_text += f"\n💡 ¡Envía fotos de tus comidas para empezar a trackear!"
            
            if not user_goal:
                stats_text += f"\n🎯 Usa /setmeta para establecer tu objetivo diario"
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            stats_text = (
                "📊 *Estadísticas de hoy:*\n\n"
                "❌ Error cargando datos\n"
                "Intenta nuevamente en un momento"
            )
            
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto"""
        user_id = update.effective_user.id
        logger.info(f"Mensaje de texto recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
            
        await update.message.reply_text(
            "📸 Por favor, envía una foto de tu comida para analizarla.\n"
            "Si necesitas ayuda, usa /help"
        )
    
    async def set_goal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /setmeta - Establecer meta diaria de calorías"""
        user_id = update.effective_user.id
        logger.info(f"Comando /setmeta recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
        
        # Verificar si se proporcionó la meta
        args = context.args
        if not args:
            help_text = (
                "🎯 *Configurar Meta Diaria*\n\n"
                "*Uso:* `/setmeta [calorías]`\n\n"
                "*Ejemplos:*\n"
                "• `/setmeta 2000` - Meta de 2000 kcal/día\n"
                "• `/setmeta 1800` - Meta de 1800 kcal/día\n\n"
                "*Guías generales:*\n"
                "• Mantenimiento: 2000-2500 kcal\n"
                "• Pérdida de peso: 1500-2000 kcal\n"
                "• Ganancia muscular: 2500-3000 kcal\n\n"
                "💡 Consulta a un nutricionista para metas personalizadas"
            )
            await update.message.reply_text(help_text, parse_mode='Markdown')
            return
        
        try:
            # Parsear la meta de calorías
            calorie_goal = int(args[0])
            
            # Validar rango razonable
            if calorie_goal < 800 or calorie_goal > 5000:
                await update.message.reply_text(
                    "⚠️ Meta fuera del rango saludable (800-5000 kcal).\n"
                    "Por favor, ingresa una meta más realista."
                )
                return
            
            # Guardar en base de datos
            success = self.database.set_daily_goal(user_id, calorie_goal)
            
            if success:
                # Obtener estadísticas actuales para mostrar progreso
                daily_stats = self.database.get_daily_calories(user_id)
                current_calories = daily_stats['total_calories']
                percentage = (current_calories / calorie_goal) * 100 if calorie_goal > 0 else 0
                
                response = (
                    f"🎯 *Meta establecida exitosamente*\n\n"
                    f"📊 *Meta diaria:* {calorie_goal} kcal\n"
                    f"🔥 *Consumo actual:* {current_calories} kcal ({percentage:.1f}%)\n"
                    f"📈 *Restante:* {max(0, calorie_goal - current_calories)} kcal\n\n"
                )
                
                if percentage < 50:
                    response += "💚 ¡Vas muy bien! Tienes margen para más comidas."
                elif percentage < 80:
                    response += "💛 Buen progreso, mantén el control de las porciones."
                elif percentage < 100:
                    response += "🧡 Te acercas a tu meta, ¡cuidado con las próximas comidas!"
                else:
                    response += "🔴 Ya superaste tu meta de hoy. ¡Mañana será mejor!"
                
                response += f"\n\nAhora recibirás alertas cuando una comida pueda hacerte exceder tu meta. 🚨"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    "❌ Error guardando tu meta. Intenta nuevamente."
                )
                
        except ValueError:
            await update.message.reply_text(
                "❌ Por favor, ingresa un número válido de calorías.\n"
                "Ejemplo: `/setmeta 2000`"
            )
        except Exception as e:
            logger.error(f"Error en comando setmeta: {e}")
            await update.message.reply_text(
                "❌ Ocurrió un error. Intenta nuevamente."
            )
    
    async def monthly_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /mensual - Mostrar estadísticas del mes"""
        user_id = update.effective_user.id
        logger.info(f"Comando /mensual recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
        
        try:
            # Enviar mensaje de procesando (puede ser lenta la consulta)
            processing_msg = await update.message.reply_text("📊 Generando reporte mensual... ⏳")
            
            # Obtener estadísticas mensuales
            monthly_stats = self.database.get_monthly_summary(user_id)
            
            # Formatear respuesta
            response = self._format_monthly_response(monthly_stats)
            
            # Actualizar mensaje
            await processing_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas mensuales: {e}")
            await processing_msg.edit_text(
                "❌ Error generando el reporte mensual.\n"
                "Intenta nuevamente en un momento."
            )
    
    def _format_monthly_response(self, stats: dict) -> str:
        """Formatear el reporte mensual"""
        response = f"📊 *Reporte Mensual - {stats['month_name']}*\n\n"
        
        # Resumen general
        response += f"📅 *Días rastreados:* {stats['days_tracked']}/{stats['days_in_month']}\n"
        response += f"🔥 *Total consumido:* {stats['total_calories']:,} kcal\n"
        response += f"🍽️ *Total de comidas:* {stats['total_meals']}\n"
        response += f"📈 *Promedio diario:* {stats['avg_daily_calories']} kcal\n"
        
        # Información de meta si existe
        if stats.get('daily_goal'):
            goal = stats['daily_goal']
            total_goal = stats.get('total_goal_calories', 0)
            performance = stats.get('goal_performance', {})
            
            response += f"\n🎯 *Meta vs Realidad:*\n"
            response += f"• Meta diaria: {goal} kcal\n"
            response += f"• Meta mensual: {total_goal:,} kcal\n"
            
            if total_goal > 0:
                surplus_deficit = stats['total_calories'] - total_goal
                if surplus_deficit > 0:
                    response += f"• Exceso: +{surplus_deficit:,} kcal 📈\n"
                else:
                    response += f"• Déficit: {surplus_deficit:,} kcal 📉\n"
            
            response += f"\n📊 *Cumplimiento de Meta:*\n"
            response += f"• Días en meta: {performance.get('days_on_target', 0)} 💚\n"
            response += f"• Días sobre meta: {performance.get('days_over', 0)} 🔴\n"
            response += f"• Días bajo meta: {performance.get('days_under', 0)} 🔵\n"
            response += f"• Tasa de éxito: {performance.get('success_rate', 0)}% ✨\n"
        
        # Mejor y peor día
        if stats.get('best_day') and stats.get('worst_day'):
            best = stats['best_day']
            worst = stats['worst_day']
            
            response += f"\n🏆 *Mejor día:* {best['date']}\n"
            response += f"   {best['calories']} kcal ({best['meals']} comidas)\n"
            response += f"😰 *Día más desafiante:* {worst['date']}\n"
            response += f"   {worst['calories']} kcal ({worst['meals']} comidas)\n"
        
        # Tendencia (últimos 7 días con datos)
        recent_days = stats['daily_breakdown'][-7:] if len(stats['daily_breakdown']) >= 7 else stats['daily_breakdown']
        if recent_days:
            response += f"\n📈 *Últimos días:*\n"
            for day in recent_days[-5:]:  # Solo últimos 5 días para no saturar
                date_obj = datetime.fromisoformat(day['date'])
                day_name = date_obj.strftime("%d/%m")
                
                # Indicador visual según meta
                if day.get('goal_percentage'):
                    percentage = day['goal_percentage']
                    if percentage < 90:
                        indicator = "🔵"
                    elif percentage <= 110:
                        indicator = "💚"
                    else:
                        indicator = "🔴"
                else:
                    indicator = "⚪"
                
                response += f"• {day_name}: {day['calories']} kcal {indicator}\n"
        
        # Consejos basados en los datos
        response += f"\n💡 *Análisis:*\n"
        
        if stats['days_tracked'] < stats['days_in_month'] / 2:
            response += "• Intenta registrar más días para un mejor seguimiento\n"
        
        if stats.get('daily_goal'):
            success_rate = stats.get('goal_performance', {}).get('success_rate', 0)
            if success_rate >= 70:
                response += "• ¡Excelente consistencia con tu meta! 👏\n"
            elif success_rate >= 50:
                response += "• Buen progreso, sigue mejorando la consistencia\n"
            else:
                response += "• Considera ajustar tu meta o mejorar la planificación\n"
        
        avg_meals = stats['total_meals'] / stats['days_tracked'] if stats['days_tracked'] > 0 else 0
        if avg_meals < 2.5:
            response += "• Considera registrar todas tus comidas del día\n"
        elif avg_meals > 4:
            response += "• ¡Buen registro de todas las comidas! 📸\n"
        
        response += f"\n🌐 Generado desde la nube"
        
        return response
    
    async def process_update(self, update_data):
        """Procesar update de Telegram"""
        try:
            # Asegurar que la aplicación esté inicializada
            await self.initialize()
            
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

    async def clear_user_data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /clear_my_data - Eliminar todos los datos del usuario"""
        user_id = update.effective_user.id
        logger.info(f"Comando /clear_my_data recibido de usuario: {user_id}")
        
        # Verificar autorización
        if not self.is_user_authorized(user_id):
            await self.send_unauthorized_message(update)
            return
        
        try:
            # Mostrar información antes de limpiar
            await update.message.reply_text(
                f"🆔 *Tu ID de usuario:* `{user_id}`\n\n"
                "🧹 Limpiando todos tus datos...",
                parse_mode='Markdown'
            )
            
            # Limpiar datos del usuario
            deleted_count = self.database.delete_user_data(user_id)
            
            await update.message.reply_text(
                f"✅ *Datos eliminados exitosamente*\n\n"
                f"📊 Registros eliminados: {deleted_count}\n"
                f"🆔 Usuario: {user_id}\n\n"
                "Ahora puedes empezar desde cero con fechas correctas de Chile 🇨🇱\n"
                "Envía una nueva foto de comida para empezar.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error en comando clear_my_data: {e}")
            await update.message.reply_text(
                f"❌ Error eliminando datos: {e}\n\n"
                f"Tu ID de usuario es: `{user_id}`",
                parse_mode='Markdown'
            )

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
            import asyncio
            
            # Crear y ejecutar el loop de manera segura
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Procesar el update
                loop.run_until_complete(diet_agent.process_update(update_data))
            except Exception as e:
                logger.error(f"Error procesando update: {e}")
        
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
        "allowed_users_set": bool(os.getenv('ALLOWED_USER_IDS')),
        "allowed_users_count": len(diet_agent.allowed_user_ids),
        "port": os.getenv('PORT', 'not_set')
    }), 200

@app.route('/database_stats', methods=['GET'])
def database_stats():
    """Endpoint para verificar estadísticas de la base de datos"""
    try:
        stats = diet_agent.database.get_database_stats()
        return jsonify({
            "status": "success",
            "database_stats": stats,
            "purge_info": {
                "retention_months": 2,
                "description": "Datos más antiguos de 2 meses son eliminados automáticamente"
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e)
        }), 500

@app.route('/purge_old_data', methods=['POST'])
def manual_purge():
    """Endpoint para ejecutar purga manual (solo para mantenimiento)"""
    try:
        purge_result = diet_agent.database.purge_old_data(months_to_keep=2)
        return jsonify({
            "status": "success",
            "purge_result": purge_result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/test_bot', methods=['GET'])
def test_bot():
    """Endpoint para probar que el bot funciona"""
    try:
        import asyncio
        
        async def get_bot_info():
            # Asegurar que el bot esté inicializado
            await diet_agent.initialize()
            bot_info = await diet_agent.bot.get_me()
            return {
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "bot_name": bot_info.first_name,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages
            }
        
        # Crear y ejecutar el loop de manera segura
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        bot_data = loop.run_until_complete(get_bot_info())
        
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
        
        async def get_webhook_info():
            # Asegurar que el bot esté inicializado
            await diet_agent.initialize()
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
        
        # Crear y ejecutar el loop de manera segura
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        webhook_data = loop.run_until_complete(get_webhook_info())
        
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
        
        import asyncio
        
        async def configure_webhook():
            # Asegurar que el bot esté inicializado
            await diet_agent.initialize()
            return await diet_agent.bot.set_webhook(url=f"{webhook_url}/webhook")
        
        # Crear y ejecutar el loop de manera segura
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        response = loop.run_until_complete(configure_webhook())
        
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