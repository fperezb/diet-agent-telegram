"""
Analizador de alimentos usando OpenAI Vision API
Identifica alimentos en imágenes y proporciona información detallada
"""

import os
import base64
import logging
from typing import Dict, List, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class FoodAnalyzer:
    def __init__(self):
        """Inicializar el analizador de alimentos"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
        self.client = OpenAI(api_key=api_key)
        
        # Prompt optimizado para análisis de alimentos con JSON consistente
        self.system_prompt = """
        Eres un experto nutricionista. Analiza la imagen y responde SOLO con JSON válido.
        
        REFERENCIAS NUTRICIONALES (por 100g):
        - Pan: 265 kcal, 9g proteína, 49g carbohidratos, 3.2g grasa
        - Queso: 402 kcal, 25g proteína, 1.3g carbohidratos, 33g grasa  
        - Mantequilla: 717 kcal, 0.9g proteína, 0.1g carbohidratos, 81g grasa
        - Café: 2 kcal, 0.3g proteína, 0g carbohidratos, 0g grasa
        - Galletas Serranita: 480 kcal, 6.5g proteína, 70.2g carbohidratos, 19.8g grasa
        
        INSTRUCCIONES CRÍTICAS:
        1. Responde SOLO JSON válido, sin texto adicional
        2. No uses markdown (```json)
        3. No duplicar propiedades en el JSON
        4. Usa las referencias nutricionales para cálculos precisos
        5. Si el usuario especifica cantidades, úsalas
        
        FORMATO REQUERIDO (copia exactamente esta estructura):
        {
            "foods": [
                {
                    "name": "nombre_del_alimento",
                    "confidence": 0.95,
                    "portion_size": "descripción_porción",
                    "estimated_grams": 60,
                    "units_count": 1,
                    "category": "categoría",
                    "nutrition": {
                        "calories": 150,
                        "protein": 5.0,
                        "carbs": 20.0,
                        "fat": 8.0
                    }
                }
            ],
            "dish_description": "descripción del plato",
            "preparation_method": "método de preparación",
            "total_nutrition": {
                "calories": 150,
                "protein": 5.0,
                "carbs": 20.0,
                "fat": 8.0
            }
        }
        """
    
    async def analyze_image(self, image_path: str, user_text: str = "") -> Optional[Dict]:
        """
        Analizar imagen de comida usando OpenAI Vision API
        
        Args:
            image_path: Ruta a la imagen a analizar
            
        Returns:
            Diccionario con análisis de la comida o None si hay error
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                logger.error(f"Archivo no encontrado: {image_path}")
                return None
            
            # Leer y codificar imagen en base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Llamada a OpenAI Vision API con modelo actualizado
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Modelo actual que reemplaza gpt-4-vision-preview
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analiza esta imagen de comida e identifica todos los alimentos visibles.

INFORMACIÓN ADICIONAL DEL USUARIO: {user_text if user_text.strip() else "No se proporcionó información adicional"}

INSTRUCCIONES IMPORTANTES:
- Si el usuario menciona específicamente qué tipo de carne/alimento es (ej: "cerdo", "pollo", "pescado"), PRIORÍZALO sobre tu identificación visual
- Si el usuario dice cantidad específica, úsala para el cálculo (ej: "4 galletas", "2 huevos")
- Combina la información visual con lo que dice el usuario para el análisis más preciso"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Extraer respuesta
            content = response.choices[0].message.content.strip()
            logger.info(f"Respuesta cruda de OpenAI: {content}")
            
            # Parser robusto para JSON de OpenAI
            import json
            import re
            
            # Limpiar contenido de markdown
            if "```json" in content:
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1).strip()
                else:
                    content = content.replace("```json", "").replace("```", "").strip()
            
            # Intentar parsear JSON
            try:
                result = json.loads(content)
                
                # Verificar estructura
                if "error" in result:
                    logger.warning(f"Error en análisis: {result['error']}")
                    return None
                
                if "foods" not in result:
                    logger.error("Respuesta sin formato esperado")
                    return None
                
                logger.info(f"✅ Análisis exitoso: {len(result['foods'])} alimentos")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON inválido de OpenAI: {e}")
                logger.error(f"📋 Contenido problemático: {content[:500]}...")
                
                # Fallback: intentar extraer información básica
                return self._create_fallback_response(content)
            
            except Exception as e:
                logger.error(f"❌ Error inesperado parseando respuesta: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {e}")
            return None
    
    def _create_fallback_response(self, content: str) -> Optional[Dict]:
        """Crear respuesta básica cuando JSON está malformado"""
        try:
            # Buscar información básica en el texto
            import re
            
            # Buscar alimentos mencionados
            food_patterns = [
                r'"name"\s*:\s*"([^"]+)"',
                r"'name'\s*:\s*'([^']+)'"
            ]
            
            foods_found = []
            for pattern in food_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                foods_found.extend(matches)
            
            # Buscar calorías
            calorie_patterns = [
                r'"calories"\s*:\s*(\d+)',
                r"'calories'\s*:\s*(\d+)"
            ]
            
            total_calories = 0
            for pattern in calorie_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    total_calories = sum(int(cal) for cal in matches)
                    break
            
            if foods_found or total_calories > 0:
                logger.info(f"🔧 Fallback activado: {len(foods_found)} alimentos, {total_calories} kcal")
                
                return {
                    "foods": [
                        {
                            "name": food,
                            "confidence": 0.7,
                            "portion_size": "estimado",
                            "estimated_grams": 100,
                            "category": "desconocido",
                            "nutrition": {
                                "calories": max(50, total_calories // max(1, len(foods_found))),
                                "protein": 0,
                                "carbs": 0,
                                "fat": 0
                            }
                        } for food in foods_found[:3]  # Máximo 3 alimentos
                    ] or [{
                        "name": "alimento no identificado",
                        "confidence": 0.5,
                        "portion_size": "estimado",
                        "estimated_grams": 100,
                        "category": "desconocido",
                        "nutrition": {
                            "calories": max(100, total_calories),
                            "protein": 0,
                            "carbs": 0,
                            "fat": 0
                        }
                    }],
                    "dish_description": "Análisis recuperado de respuesta malformada",
                    "preparation_method": "No identificado",
                    "total_nutrition": {
                        "calories": max(100, total_calories),
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en fallback: {e}")
            return None
    
    def validate_food_analysis(self, analysis: Dict) -> bool:
        """
        Validar que el análisis tiene la estructura esperada
        
        Args:
            analysis: Diccionario con el análisis
            
        Returns:
            True si la estructura es válida
        """
        if not isinstance(analysis, dict):
            return False
        
        if "foods" not in analysis:
            return False
        
        if not isinstance(analysis["foods"], list):
            return False
        
        # Validar cada alimento
        for food in analysis["foods"]:
            required_fields = ["name", "confidence"]
            if not all(field in food for field in required_fields):
                return False
        
        return True
    
    def enhance_food_analysis(self, analysis: Dict) -> Dict:
        """
        Mejorar el análisis con información adicional
        
        Args:
            analysis: Análisis básico de la comida
            
        Returns:
            Análisis mejorado con información adicional
        """
        if not analysis or "foods" not in analysis:
            return analysis
        
        # Agregar categorías nutricionales
        nutrition_categories = {
            'proteína': ['pollo', 'carne', 'pescado', 'huevo', 'frijoles', 'lentejas'],
            'carbohidrato': ['arroz', 'pasta', 'pan', 'papa', 'quinoa'],
            'verdura': ['lechuga', 'tomate', 'cebolla', 'zanahoria', 'brócoli'],
            'fruta': ['manzana', 'plátano', 'naranja', 'fresa', 'uva'],
            'grasa saludable': ['aguacate', 'nuez', 'almendra', 'aceite de oliva']
        }
        
        for food in analysis["foods"]:
            food_name = food["name"].lower()
            
            # Asignar categoría nutricional
            for category, keywords in nutrition_categories.items():
                if any(keyword in food_name for keyword in keywords):
                    food["nutrition_category"] = category
                    break
            else:
                food["nutrition_category"] = "otro"
        
        return analysis