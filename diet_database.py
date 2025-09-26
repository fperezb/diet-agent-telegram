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
                        total_protein REAL DEFAULT 0,
                        total_carbs REAL DEFAULT 0,
                        total_fat REAL DEFAULT 0,
                        photo_file_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Migración: agregar columnas de macronutrientes si no existen
                self._migrate_macronutrients_columns(cursor)
                
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
                
            # Ejecutar purga automática de datos antiguos
            purge_result = self.purge_old_data(months_to_keep=2)
            if purge_result['success'] and purge_result['meals_deleted'] > 0:
                logger.info(f"Purga automática: eliminadas {purge_result['meals_deleted']} "
                           f"comidas anteriores a {purge_result['cutoff_date']}")
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def _migrate_macronutrients_columns(self, cursor):
        """Migrar la base de datos para agregar columnas de macronutrientes"""
        try:
            # Verificar si ya existen las columnas
            cursor.execute("PRAGMA table_info(meals)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Agregar columnas de macronutrientes si no existen
            if 'total_protein' not in columns:
                cursor.execute('ALTER TABLE meals ADD COLUMN total_protein REAL DEFAULT 0')
                logger.info("Agregada columna total_protein")
            
            if 'total_carbs' not in columns:
                cursor.execute('ALTER TABLE meals ADD COLUMN total_carbs REAL DEFAULT 0')
                logger.info("Agregada columna total_carbs")
            
            if 'total_fat' not in columns:
                cursor.execute('ALTER TABLE meals ADD COLUMN total_fat REAL DEFAULT 0')
                logger.info("Agregada columna total_fat")
                
        except Exception as e:
            logger.error(f"Error en migración de macronutrientes: {e}")
    
    def save_meal(self, user_id: int, foods: List[Dict], total_calories: int, 
                 total_protein: float = 0, total_carbs: float = 0, total_fat: float = 0,
                 photo_file_id: str = None) -> int:
        """
        Guardar una comida en la base de datos
        
        Args:
            user_id: ID del usuario de Telegram
            foods: Lista de alimentos identificados con sus datos
            total_calories: Total de calorías de la comida
            total_protein: Total de proteínas en gramos
            total_carbs: Total de carbohidratos en gramos
            total_fat: Total de grasas en gramos
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
                    INSERT INTO meals (user_id, date, datetime, foods_identified, total_calories, 
                                     total_protein, total_carbs, total_fat, photo_file_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, today, now.isoformat(), foods_text, total_calories, 
                      total_protein, total_carbs, total_fat, photo_file_id))
                
                meal_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Comida guardada: Usuario {user_id}, {total_calories} cal, "
                           f"P:{total_protein}g C:{total_carbs}g F:{total_fat}g, ID {meal_id}")
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
                
                # Obtener todas las comidas del día con macronutrientes
                cursor.execute('''
                    SELECT datetime, foods_identified, total_calories, total_protein, total_carbs, total_fat
                    FROM meals 
                    WHERE user_id = ? AND date = ?
                    ORDER BY datetime
                ''', (user_id, date_str))
                
                meals = cursor.fetchall()
                
                # Calcular totales
                total_calories = sum(meal[2] for meal in meals)
                total_protein = sum(meal[3] or 0 for meal in meals)  # Handle None values
                total_carbs = sum(meal[4] or 0 for meal in meals)
                total_fat = sum(meal[5] or 0 for meal in meals)
                meal_count = len(meals)
                
                # Obtener la última comida
                last_meal_time = None
                if meals:
                    last_datetime = datetime.fromisoformat(meals[-1][0])
                    last_meal_time = last_datetime.strftime("%H:%M")
                
                return {
                    "date": date_str,
                    "total_calories": total_calories,
                    "total_protein": round(total_protein, 1),
                    "total_carbs": round(total_carbs, 1),
                    "total_fat": round(total_fat, 1),
                    "meal_count": meal_count,
                    "last_meal_time": last_meal_time,
                    "meals": [
                        {
                            "time": datetime.fromisoformat(meal[0]).strftime("%H:%M"),
                            "foods": meal[1],
                            "calories": meal[2],
                            "protein": round(meal[3] or 0, 1),
                            "carbs": round(meal[4] or 0, 1),
                            "fat": round(meal[5] or 0, 1)
                        }
                        for meal in meals
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo calorías diarias: {e}")
            return {
                "date": date_str,
                "total_calories": 0,
                "total_protein": 0,
                "total_carbs": 0,
                "total_fat": 0,
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
    
    def get_monthly_summary(self, user_id: int, target_month: date = None) -> Dict:
        """
        Obtener resumen mensual completo para un usuario
        
        Args:
            user_id: ID del usuario
            target_month: Mes objetivo (por defecto el mes actual)
            
        Returns:
            Dict con estadísticas mensuales completas
        """
        if target_month is None:
            target_month = date.today()
        
        # Primer día del mes y último día a considerar
        month_start = target_month.replace(day=1)
        
        # Si es el mes actual, solo hasta hoy. Si es mes pasado, todo el mes.
        today = date.today()
        if target_month.year == today.year and target_month.month == today.month:
            # Mes actual: hasta hoy
            month_end = today
            days_to_consider = today.day
        else:
            # Mes pasado: todo el mes
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)
            days_to_consider = (month_end - month_start).days
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener datos diarios del mes (hasta hoy si es mes actual)
                if target_month.year == today.year and target_month.month == today.month:
                    # Mes actual: incluir hasta hoy inclusive
                    cursor.execute('''
                        SELECT date, SUM(total_calories) as daily_calories, COUNT(*) as daily_meals
                        FROM meals 
                        WHERE user_id = ? AND date >= ? AND date <= ?
                        GROUP BY date
                        ORDER BY date
                    ''', (user_id, month_start.isoformat(), month_end.isoformat()))
                else:
                    # Mes pasado: todo el mes
                    cursor.execute('''
                        SELECT date, SUM(total_calories) as daily_calories, COUNT(*) as daily_meals
                        FROM meals 
                        WHERE user_id = ? AND date >= ? AND date < ?
                        GROUP BY date
                        ORDER BY date
                    ''', (user_id, month_start.isoformat(), month_end.isoformat()))
                
                daily_data = cursor.fetchall()
                
                # Calcular estadísticas generales
                total_calories = sum(day[1] for day in daily_data)
                total_meals = sum(day[2] for day in daily_data)
                days_with_data = len(daily_data)
                
                # Obtener meta del usuario
                user_goal = self.get_user_goal(user_id)
                daily_goal = user_goal['daily_calorie_goal'] if user_goal else None
                
                # Estadísticas avanzadas
                daily_calories = [day[1] for day in daily_data] if daily_data else []
                avg_daily_calories = total_calories / days_with_data if days_with_data > 0 else 0
                
                # Días sobre/bajo meta
                days_over_goal = 0
                days_under_goal = 0
                days_on_target = 0
                total_goal_calories = 0
                
                if daily_goal:
                    total_goal_calories = daily_goal * days_with_data
                    for day_calories in daily_calories:
                        if day_calories > daily_goal * 1.1:  # 10% margen
                            days_over_goal += 1
                        elif day_calories < daily_goal * 0.9:  # 10% margen
                            days_under_goal += 1
                        else:
                            days_on_target += 1
                
                # Encontrar mejor y peor día
                best_day = None
                worst_day = None
                if daily_data and daily_goal:
                    # Mejor día: más cercano a la meta sin excederla mucho
                    best_day = min(daily_data, key=lambda x: abs(x[1] - daily_goal))
                    # Peor día: más alejado de la meta
                    worst_day = max(daily_data, key=lambda x: abs(x[1] - daily_goal))
                
                # Nombres de meses en español
                month_names_es = {
                    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
                    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                }
                month_name_es = f"{month_names_es[month_start.month]} {month_start.year}"
                
                return {
                    "month": month_start.strftime("%Y-%m"),
                    "month_name": month_name_es,
                    "days_in_month": days_to_consider,
                    "days_tracked": days_with_data,
                    "total_calories": total_calories,
                    "total_meals": total_meals,
                    "avg_daily_calories": round(avg_daily_calories, 1),
                    "daily_goal": daily_goal,
                    "total_goal_calories": total_goal_calories,
                    "goal_performance": {
                        "days_over": days_over_goal,
                        "days_under": days_under_goal,
                        "days_on_target": days_on_target,
                        "success_rate": round((days_on_target / days_with_data * 100), 1) if days_with_data > 0 else 0
                    },
                    "best_day": {
                        "date": best_day[0],
                        "calories": best_day[1],
                        "meals": best_day[2]
                    } if best_day else None,
                    "worst_day": {
                        "date": worst_day[0],
                        "calories": worst_day[1], 
                        "meals": worst_day[2]
                    } if worst_day else None,
                    "daily_breakdown": [
                        {
                            "date": day[0],
                            "calories": day[1],
                            "meals": day[2],
                            "vs_goal": day[1] - daily_goal if daily_goal else None,
                            "goal_percentage": round((day[1] / daily_goal * 100), 1) if daily_goal else None
                        }
                        for day in daily_data
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen mensual: {e}")
            # Nombres de meses en español para el caso de error también
            month_names_es = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            month_name_es = f"{month_names_es[target_month.month]} {target_month.year}"
            
            return {
                "month": target_month.strftime("%Y-%m"),
                "month_name": month_name_es,
                "days_in_month": 0,
                "days_tracked": 0,
                "total_calories": 0,
                "total_meals": 0,
                "avg_daily_calories": 0,
                "daily_goal": None,
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

    def purge_old_data(self, months_to_keep: int = 2) -> Dict:
        """
        Purgar datos antiguos manteniendo solo los últimos N meses
        
        Args:
            months_to_keep: Número de meses hacia atrás a mantener (default: 2)
            
        Returns:
            Dict con información de la purga realizada
        """
        try:
            today = date.today()
            
            # Calcular fecha límite (hace N meses)
            if today.month > months_to_keep:
                cutoff_date = today.replace(month=today.month - months_to_keep, day=1)
            else:
                # Si estamos en enero o febrero y queremos mantener 2+ meses
                months_back = months_to_keep - today.month
                cutoff_date = today.replace(
                    year=today.year - 1, 
                    month=12 - months_back,
                    day=1
                )
            
            cutoff_str = cutoff_date.isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar registros a eliminar antes de borrarlos
                cursor.execute('''
                    SELECT COUNT(*) FROM meals WHERE date < ?
                ''', (cutoff_str,))
                meals_to_delete = cursor.fetchone()[0]
                
                # Obtener usuarios afectados para logging
                cursor.execute('''
                    SELECT DISTINCT user_id FROM meals WHERE date < ?
                ''', (cutoff_str,))
                affected_users = [row[0] for row in cursor.fetchall()]
                
                # Eliminar registros antiguos de meals
                cursor.execute('DELETE FROM meals WHERE date < ?', (cutoff_str,))
                meals_deleted = cursor.rowcount
                
                # También limpiar configuraciones de usuarios que ya no tienen datos
                cursor.execute('''
                    DELETE FROM user_config 
                    WHERE user_id NOT IN (SELECT DISTINCT user_id FROM meals)
                ''')
                configs_deleted = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Purga completada: {meals_deleted} comidas eliminadas, "
                           f"{configs_deleted} configuraciones huérfanas eliminadas. "
                           f"Fecha límite: {cutoff_str}")
                
                return {
                    "success": True,
                    "cutoff_date": cutoff_str,
                    "meals_deleted": meals_deleted,
                    "configs_deleted": configs_deleted,
                    "affected_users": len(affected_users),
                    "months_kept": months_to_keep
                }
                
        except Exception as e:
            logger.error(f"Error en purga de datos: {e}")
            return {
                "success": False,
                "error": str(e),
                "meals_deleted": 0,
                "configs_deleted": 0
            }
    
    def get_database_stats(self) -> Dict:
        """Obtener estadísticas generales de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar total de comidas
                cursor.execute('SELECT COUNT(*) FROM meals')
                total_meals = cursor.fetchone()[0]
                
                # Contar usuarios únicos
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM meals')
                total_users = cursor.fetchone()[0]
                
                # Obtener rango de fechas
                cursor.execute('SELECT MIN(date), MAX(date) FROM meals')
                date_range = cursor.fetchone()
                
                # Contar configuraciones
                cursor.execute('SELECT COUNT(*) FROM user_config')
                total_configs = cursor.fetchone()[0]
                
                # Tamaño de la BD (aproximado)
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                return {
                    "total_meals": total_meals,
                    "total_users": total_users,
                    "total_configs": total_configs,
                    "oldest_record": date_range[0] if date_range[0] else None,
                    "newest_record": date_range[1] if date_range[1] else None,
                    "database_size_bytes": db_size
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {
                "total_meals": 0,
                "total_users": 0,
                "total_configs": 0,
                "error": str(e)
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