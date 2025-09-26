"""
Calculadora de calorías basada en análisis de alimentos
Estima calorías y información nutricional de los alimentos identificados
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CalorieCalculator:
    def __init__(self):
        """Inicializar calculadora de calorías"""
        # Base de datos básica de calorías por 100g
        self.calorie_database = {
            # Proteínas
            'pollo': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
            'carne': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17},
            'pescado': {'calories': 150, 'protein': 30, 'carbs': 0, 'fat': 3},
            'huevo': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11},
            'frijoles': {'calories': 127, 'protein': 9, 'carbs': 23, 'fat': 0.5},
            'lentejas': {'calories': 116, 'protein': 9, 'carbs': 20, 'fat': 0.4},
            
            # Carbohidratos
            'arroz': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1},
            'pan': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2},
            'papa': {'calories': 77, 'protein': 2, 'carbs': 17, 'fat': 0.1},
            'quinoa': {'calories': 120, 'protein': 4.4, 'carbs': 22, 'fat': 1.9},
            
            # Verduras
            'lechuga': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2},
            'tomate': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
            'cebolla': {'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1},
            'zanahoria': {'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2},
            'brócoli': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4},
            
            # Frutas
            'manzana': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2},
            'plátano': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3},
            'naranja': {'calories': 47, 'protein': 0.9, 'carbs': 12, 'fat': 0.1},
            'fresa': {'calories': 32, 'protein': 0.7, 'carbs': 7.7, 'fat': 0.3},
            
            # Grasas saludables
            'aguacate': {'calories': 160, 'protein': 2, 'carbs': 9, 'fat': 15},
            'nuez': {'calories': 654, 'protein': 15, 'carbs': 14, 'fat': 65},
            'almendra': {'calories': 579, 'protein': 21, 'carbs': 22, 'fat': 50},
            
            # Galletas y snacks (valores más precisos basados en información nutricional real)
            'galletas': {'calories': 502, 'protein': 6.9, 'carbs': 68.8, 'fat': 22.9},
            'galletas serranita': {'calories': 433, 'protein': 3.6, 'carbs': 62.5, 'fat': 17.9},  # Ajustado para ~38 kcal por galleta
            'galletas maria': {'calories': 428, 'protein': 7.2, 'carbs': 74.3, 'fat': 11.4},     # Ajustado para ~30 kcal por galleta
            'galletas oreo': {'calories': 477, 'protein': 4.4, 'carbs': 68.8, 'fat': 20.6},     # Ajustado para ~53 kcal por galleta
            'chips': {'calories': 536, 'protein': 6.6, 'carbs': 53.0, 'fat': 34.6},
            'papas fritas': {'calories': 365, 'protein': 4.0, 'carbs': 63.2, 'fat': 12.8},
            'chocolate': {'calories': 546, 'protein': 4.9, 'carbs': 61.2, 'fat': 31.3},
            'dulces': {'calories': 394, 'protein': 0.0, 'carbs': 98.0, 'fat': 0.2},
            
            # Lácteos
            'leche': {'calories': 42, 'protein': 3.4, 'carbs': 5.0, 'fat': 1.0},
            'yogur': {'calories': 59, 'protein': 10.0, 'carbs': 3.6, 'fat': 0.4},
            'queso': {'calories': 402, 'protein': 25.0, 'carbs': 1.3, 'fat': 33.0},
            'queso fresco': {'calories': 264, 'protein': 11.1, 'carbs': 4.1, 'fat': 23.0},
            
            # Cereales y desayuno
            'avena': {'calories': 389, 'protein': 16.9, 'carbs': 66.3, 'fat': 6.9},
            'cereal': {'calories': 379, 'protein': 7.5, 'carbs': 84.0, 'fat': 2.7},
            'granola': {'calories': 471, 'protein': 10.1, 'carbs': 64.3, 'fat': 20.3},
            
            # Bebidas
            'jugo': {'calories': 45, 'protein': 0.7, 'carbs': 11.2, 'fat': 0.2},
            'refresco': {'calories': 42, 'protein': 0.0, 'carbs': 10.6, 'fat': 0.0},
            'café': {'calories': 2, 'protein': 0.3, 'carbs': 0.0, 'fat': 0.0},
            
            # Comidas preparadas
            'pizza': {'calories': 266, 'protein': 11.0, 'carbs': 33.0, 'fat': 10.0},
            'hamburguesa': {'calories': 295, 'protein': 17.0, 'carbs': 31.0, 'fat': 12.0},
            'sandwich': {'calories': 304, 'protein': 12.8, 'carbs': 41.8, 'fat': 10.7},
            'empanada': {'calories': 245, 'protein': 8.5, 'carbs': 24.0, 'fat': 13.2},
            
            # Otros
            'aceite': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100},
            'mantequilla': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81},
        }
        
        # Estimaciones de porciones típicas en gramos
        self.typical_portions = {
            # Proteínas
            'pollo': 150,        # pechuga pequeña
            'carne': 120,        # porción estándar
            'pescado': 140,      # filete
            'huevo': 50,         # un huevo
            
            # Carbohidratos
            'arroz': 80,         # porción cocida
            'pasta': 100,        # porción cocida
            'pan': 30,           # una rebanada
            'papa': 150,         # papa mediana
            
            # Verduras
            'lechuga': 50,       # ensalada pequeña
            'tomate': 100,       # tomate mediano
            
            # Frutas
            'manzana': 150,      # manzana mediana
            'plátano': 120,      # plátano mediano
            'aguacate': 100,     # medio aguacate
            
            # Galletas y snacks (pesos por unidad más precisos)
            'galletas': 25,      # 2-3 galletas promedio
            'galletas serranita': 8.8,  # 1 galleta = ~8.8g (4 galletas = 35g aprox)
            'galletas maria': 7.0,      # 1 galleta = ~7g  
            'galletas oreo': 11.0,      # 1 galleta = ~11g
            'chips': 30,         # puñado pequeño
            'papas fritas': 50,  # porción pequeña
            'chocolate': 25,     # onza/cuadrito
            
            # Lácteos
            'leche': 250,        # vaso
            'yogur': 125,        # envase individual
            'queso': 30,         # rebanada
            
            # Bebidas
            'jugo': 200,         # vaso pequeño
            'refresco': 350,     # lata
            'café': 240,         # taza
        }
    
    def calculate_calories(self, food_analysis: Dict) -> Dict:
        """
        Procesar análisis nutricional de OpenAI (sin cálculos propios)
        
        Args:
            food_analysis: Análisis completo de alimentos de OpenAI
            
        Returns:
            Diccionario con información nutricional de OpenAI
        """
        if not food_analysis or 'foods' not in food_analysis:
            return self._empty_result()
        
        # USAR SOLO INFORMACIÓN DE OPENAI - Sin cálculos propios
        if 'total_nutrition' in food_analysis:
            openai_nutrition = food_analysis['total_nutrition']
            logger.info("✅ Usando SOLO información nutricional de OpenAI (sin cálculos propios)")
            return {
                'total_calories': round(openai_nutrition.get('calories', 0)),
                'breakdown': {
                    'Proteína': f"{round(openai_nutrition.get('protein', 0), 1)}g",
                    'Carbohidratos': f"{round(openai_nutrition.get('carbs', 0), 1)}g",
                    'Grasas': f"{round(openai_nutrition.get('fat', 0), 1)}g"
                },
                'identified_foods': [
                    {
                        'name': f['name'], 
                        'calories': f.get('nutrition', {}).get('calories', 0),
                        'portion_grams': f.get('estimated_grams', 0),
                        'units_count': f.get('units_count', 0),
                        'confidence': f.get('confidence', 1.0)
                    } for f in food_analysis['foods']
                ],
                'unidentified_foods': [],
                'tips': self._generate_tips(
                    openai_nutrition.get('calories', 0),
                    openai_nutrition.get('protein', 0),
                    openai_nutrition.get('carbs', 0),
                    openai_nutrition.get('fat', 0)
                ),
                'source': 'OpenAI'
            }
        
        # Fallback básico solo si OpenAI no proporciona total_nutrition
        logger.warning("❌ OpenAI no proporcionó total_nutrition, usando datos básicos de la respuesta")
        
        # Extraer información básica de los alimentos identificados
        identified_foods = []
        total_calories = 0
        
        for food in food_analysis.get('foods', []):
            food_calories = food.get('nutrition', {}).get('calories', 0) if 'nutrition' in food else 0
            total_calories += food_calories
            
            identified_foods.append({
                'name': food['name'],
                'calories': food_calories,
                'confidence': food.get('confidence', 1.0)
            })
        
        # Resultado mínimo si no hay información completa
        result = {
            'total_calories': round(total_calories) if total_calories > 0 else 100,  # Estimación mínima
            'breakdown': {
                'Proteína': '0g',
                'Carbohidratos': '0g', 
                'Grasas': '0g'
            },
            'identified_foods': identified_foods,
            'unidentified_foods': [],
            'source': 'OpenAI (parcial)',
            'tips': self._generate_tips(total_calories, 0, 0, 0)  # Sin macronutrientes en fallback
        }
        
        logger.info(f"Cálculo de calorías completado: {total_calories} kcal")
        return result
    
    def _find_nutrition_info(self, food_name: str) -> Optional[Dict]:
        """Buscar información nutricional en la base de datos"""
        # Búsqueda exacta
        if food_name in self.calorie_database:
            return self.calorie_database[food_name]
        
        # Búsqueda por palabras clave
        for key, value in self.calorie_database.items():
            if key in food_name or food_name in key:
                return value
        
        return None
    
    def _estimate_portion_size(self, food_name: str, portion_description: str) -> float:
        """Estimar el tamaño de la porción en gramos"""
        # Porción típica por defecto (peso de 1 unidad para galletas, peso típico para otros)
        default_portion = self.typical_portions.get(food_name, 100)
        
        # Ajustar basado en descripción
        if not portion_description:
            return default_portion
        
        portion_lower = portion_description.lower()
        
        # Detectar números específicos de unidades
        import re
        numbers = re.findall(r'\d+', portion_lower)
        if numbers:
            quantity = int(numbers[0])
            # Para galletas y alimentos por unidad, multiplicar por la cantidad
            if 'galleta' in food_name or 'cookie' in food_name:
                return default_portion * quantity
            # Para otros alimentos, aplicar multiplicador más conservador
            else:
                return default_portion * min(quantity, 3)  # Máximo 3x la porción normal
        
        # Detectar palabras que indican cantidad
        if any(word in portion_lower for word in ['dos', 'dos', '2', 'par', 'pareja']):
            return default_portion * 2
        elif any(word in portion_lower for word in ['tres', 'tres', '3']):
            return default_portion * 3
        elif any(word in portion_lower for word in ['cuatro', '4']):
            return default_portion * 4
        elif any(word in portion_lower for word in ['cinco', '5']):
            return default_portion * 5
        
        # Modificadores de tamaño
        if any(word in portion_lower for word in ['pequeño', 'pequeña', 'mini']):
            return default_portion * 0.7
        elif any(word in portion_lower for word in ['grande', 'gran', 'jumbo']):
            return default_portion * 1.5
        elif any(word in portion_lower for word in ['muy grande', 'enorme', 'gigante']):
            return default_portion * 2.0
        elif any(word in portion_lower for word in ['mediano', 'mediana', 'medio']):
            return default_portion
        
        return default_portion
    
    def _generate_tips(self, calories: float, protein: float, carbs: float, fat: float) -> str:
        """Generar consejos nutricionales basados en el análisis"""
        tips = []
        
        if calories > 800:
            tips.append("Esta es una comida alta en calorías. Considera porciones más pequeñas.")
        elif calories < 200:
            tips.append("Esta comida es baja en calorías. Asegúrate de obtener energía suficiente.")
        
        if protein < 10:
            tips.append("Considera agregar más proteína a tu comida.")
        elif protein > 40:
            tips.append("Excelente contenido de proteína para la recuperación muscular.")
        
        if carbs > 60:
            tips.append("Alto contenido de carbohidratos. Ideal después del ejercicio.")
        
        if fat > 30:
            tips.append("Moderado-alto en grasas. Asegúrate de que sean grasas saludables.")
        
        if not tips:
            tips.append("Comida bien balanceada. ¡Sigue así!")
        
        return " ".join(tips)
    
    def _empty_result(self) -> Dict:
        """Resultado vacío cuando no hay análisis"""
        return {
            'total_calories': 0,
            'breakdown': {
                'Proteína': "0g",
                'Carbohidratos': "0g",
                'Grasas': "0g"
            },
            'identified_foods': [],
            'unidentified_foods': [],
            'tips': "No se pudo analizar la comida. Intenta con una foto más clara."
        }
    
    def add_food_to_database(self, name: str, nutrition_info: Dict):
        """Agregar nuevo alimento a la base de datos"""
        self.calorie_database[name.lower()] = nutrition_info
        logger.info(f"Alimento agregado a la base de datos: {name}")
    
    def get_food_info(self, food_name: str) -> Optional[Dict]:
        """Obtener información nutricional de un alimento específico"""
        return self._find_nutrition_info(food_name.lower())