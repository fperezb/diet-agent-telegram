"""
Sistema de base de datos para el Diet Agent
Maneja el almacenamiento de comidas y cálculo de calorías diarias
"""

import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DietDatabase:
    def __init__(self, db_path: str = "diet_agent.db"):
        """
        Inicializar la base de datos SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crear las tablas necesarias si no existen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla para almacenar las comidas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        datetime TEXT NOT NULL,
                        foods_identified TEXT NOT NULL,
                        total_calories INTEGER NOT NULL,
                        photo_file_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla para configuración de usuarios (metas, preferencias)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_config (
                        user_id INTEGER PRIMARY KEY,
                        daily_calorie_goal INTEGER,
                        weight_goal TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Índices para mejor performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_date 
                    ON meals (user_id, date)
                ''')
                
                conn.commit()
                logger.info("Base de datos inicializada correctamente")
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def save_meal(self, user_id: int, foods: List[Dict], total_calories: int, photo_file_id: str = None) -> int:
        """
        Guardar una comida en la base de datos
        
        Args:
            user_id: ID del usuario de Telegram
            foods: Lista de alimentos identificados con sus datos
            total_calories: Total de calorías de la comida
            photo_file_id: ID del archivo de foto en Telegram
            
        Returns:
            ID de la comida guardada
        """
        try:
            now = datetime.now()
            today = date.today().isoformat()
            
            # Convertir la lista de alimentos a texto
            foods_text = ", ".join([f"{food['name']} ({food.get('confidence', 0):.0%})" for food in foods])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meals (user_id, date, datetime, foods_identified, total_calories, photo_file_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, today, now.isoformat(), foods_text, total_calories, photo_file_id))
                
                meal_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Comida guardada: Usuario {user_id}, {total_calories} cal, ID {meal_id}")
                return meal_id
                
        except Exception as e:
            logger.error(f"Error guardando comida: {e}")
            raise
    
    def get_daily_calories(self, user_id: int, target_date: date = None) -> Dict:
        """
        Obtener el total de calorías de un usuario para un día específico
        
        Args:
            user_id: ID del usuario
            target_date: Fecha objetivo (por defecto hoy)
            
        Returns:
            Dict con información del día
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener todas las comidas del día
                cursor.execute('''
                    SELECT datetime, foods_identified, total_calories
                    FROM meals 
                    WHERE user_id = ? AND date = ?
                    ORDER BY datetime
                ''', (user_id, date_str))
                
                meals = cursor.fetchall()
                
                # Calcular totales
                total_calories = sum(meal[2] for meal in meals)
                meal_count = len(meals)
                
                # Obtener la última comida
                last_meal_time = None
                if meals:
                    last_datetime = datetime.fromisoformat(meals[-1][0])
                    last_meal_time = last_datetime.strftime("%H:%M")
                
                return {
                    "date": date_str,
                    "total_calories": total_calories,
                    "meal_count": meal_count,
                    "last_meal_time": last_meal_time,
                    "meals": [
                        {
                            "time": datetime.fromisoformat(meal[0]).strftime("%H:%M"),
                            "foods": meal[1],
                            "calories": meal[2]
                        }
                        for meal in meals
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo calorías diarias: {e}")
            return {
                "date": date_str,
                "total_calories": 0,
                "meal_count": 0,
                "last_meal_time": None,
                "meals": []
            }
    
    def get_weekly_summary(self, user_id: int) -> Dict:
        """Obtener resumen de la semana para un usuario"""
        try:
            today = date.today()
            week_start = today.replace(day=today.day - today.weekday())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT date, SUM(total_calories) as daily_calories, COUNT(*) as daily_meals
                    FROM meals 
                    WHERE user_id = ? AND date >= ?
                    GROUP BY date
                    ORDER BY date
                ''', (user_id, week_start.isoformat()))
                
                daily_data = cursor.fetchall()
                
                total_week_calories = sum(day[1] for day in daily_data)
                total_week_meals = sum(day[2] for day in daily_data)
                
                return {
                    "week_start": week_start.isoformat(),
                    "total_calories": total_week_calories,
                    "total_meals": total_week_meals,
                    "daily_breakdown": [
                        {
                            "date": day[0],
                            "calories": day[1],
                            "meals": day[2]
                        }
                        for day in daily_data
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen semanal: {e}")
            return {
                "week_start": date.today().isoformat(),
                "total_calories": 0,
                "total_meals": 0,
                "daily_breakdown": []
            }
    
    def set_daily_goal(self, user_id: int, calorie_goal: int, weight_goal: str = None) -> bool:
        """
        Establecer la meta diaria de calorías para un usuario
        
        Args:
            user_id: ID del usuario
            calorie_goal: Meta diaria de calorías
            weight_goal: Objetivo de peso ('maintain', 'lose', 'gain')
            
        Returns:
            True si se guardó correctamente
        """
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Usar INSERT OR REPLACE para actualizar si existe
                cursor.execute('''
                    INSERT OR REPLACE INTO user_config 
                    (user_id, daily_calorie_goal, weight_goal, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, calorie_goal, weight_goal, now))
                
                conn.commit()
                logger.info(f"Meta establecida para usuario {user_id}: {calorie_goal} kcal/día")
                return True
                
        except Exception as e:
            logger.error(f"Error estableciendo meta: {e}")
            return False
    
    def get_user_goal(self, user_id: int) -> Optional[Dict]:
        """
        Obtener la configuración de meta del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con la configuración o None si no existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT daily_calorie_goal, weight_goal, created_at, updated_at
                    FROM user_config 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "daily_calorie_goal": result[0],
                        "weight_goal": result[1],
                        "created_at": result[2],
                        "updated_at": result[3]
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo meta del usuario: {e}")
            return None
    
    def check_calorie_limit(self, user_id: int, new_calories: int) -> Dict:
        """
        Verificar si agregar nuevas calorías excedería la meta diaria
        
        Args:
            user_id: ID del usuario
            new_calories: Calorías de la nueva comida
            
        Returns:
            Dict con información del estado respecto a la meta
        """
        try:
            # Obtener meta del usuario
            user_goal = self.get_user_goal(user_id)
            if not user_goal:
                return {
                    "has_goal": False,
                    "message": "No tienes una meta calórica configurada. Usa /setmeta para establecerla."
                }
            
            # Obtener calorías actuales del día
            daily_stats = self.get_daily_calories(user_id)
            current_calories = daily_stats['total_calories']
            
            # Calcular proyección
            projected_calories = current_calories + new_calories
            daily_goal = user_goal['daily_calorie_goal']
            
            # Calcular porcentajes
            current_percentage = (current_calories / daily_goal) * 100
            projected_percentage = (projected_calories / daily_goal) * 100
            
            # Determinar estado
            if projected_calories <= daily_goal:
                status = "safe"
                message = f"✅ ¡Perfecto! Mantendrás tu meta diaria."
            elif projected_calories <= daily_goal * 1.1:  # 10% de margen
                status = "warning"
                message = f"⚠️ Te acercarás al límite, pero aún dentro del rango aceptable."
            else:
                status = "exceed"
                excess = projected_calories - daily_goal
                message = f"🚨 ¡ADVERTENCIA! Excederás tu meta por {excess} kcal. Esto puede afectar tus objetivos de peso."
            
            return {
                "has_goal": True,
                "status": status,
                "message": message,
                "daily_goal": daily_goal,
                "current_calories": current_calories,
                "new_calories": new_calories,
                "projected_calories": projected_calories,
                "current_percentage": round(current_percentage, 1),
                "projected_percentage": round(projected_percentage, 1),
                "remaining_calories": max(0, daily_goal - current_calories)
            }
            
        except Exception as e:
            logger.error(f"Error verificando límite calórico: {e}")
            return {
                "has_goal": False,
                "message": "Error al verificar tu meta. Intenta nuevamente."
            }

    def delete_user_data(self, user_id: int):
        """Eliminar todos los datos de un usuario (GDPR compliance)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM meals WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM user_config WHERE user_id = ?', (user_id,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Eliminados {deleted_count} registros del usuario {user_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error eliminando datos del usuario: {e}")
            raise