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
    
    def delete_user_data(self, user_id: int):
        """Eliminar todos los datos de un usuario (GDPR compliance)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM meals WHERE user_id = ?', (user_id,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Eliminados {deleted_count} registros del usuario {user_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error eliminando datos del usuario: {e}")
            raise