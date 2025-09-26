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
        
        # Prompt optimizado para análisis de alimentos con macronutrientes y referencias precisas
        self.system_prompt = """
        Eres un experto nutricionista especializado en identificar alimentos en imágenes y calcular su valor nutricional preciso.
        
        Tu tarea es analizar fotos de comida y proporcionar cálculos nutricionales exactos basándote en las siguientes referencias:
        
        REFERENCIAS NUTRICIONALES (por 100g):
        - Galletas Serranita: 480 kcal, 6.5g proteína, 70.2g carbohidratos, 19.8g grasa (1 galleta ≈ 7g)
        - Galletas María: 436 kcal, 6.8g proteína, 76.2g carbohidratos, 12.1g grasa (1 galleta ≈ 6g)
        - Galletas Oreo: 481 kcal, 4.6g proteína, 70.4g carbohidratos, 20.0g grasa (1 galleta ≈ 11g)
        - Arroz blanco: 130 kcal, 2.7g proteína, 28g carbohidratos, 0.3g grasa
        - Pollo (pechuga): 165 kcal, 31g proteína, 0g carbohidratos, 3.6g grasa
        - Pan blanco: 265 kcal, 9g proteína, 49g carbohidratos, 3.2g grasa
        - Huevo: 155 kcal, 13g proteína, 1.1g carbohidratos, 11g grasa (1 huevo ≈ 50g)
        - Pizza: 266 kcal, 11g proteína, 33g carbohidratos, 10g grasa
        
        INSTRUCCIONES ESPECÍFICAS:
        1. Identifica exactamente qué alimento y cuántas unidades/porciones ves
        2. Si el usuario menciona una cantidad específica (ej: "me comí 4 galletas"), úsala para el cálculo
        3. Calcula basándote en las referencias nutricionales exactas proporcionadas
        4. Para galletas: 4 Galletas Serranita = 4 × 7g × (480 kcal/100g) = ~134 kcal + packaging
        5. Sé preciso con porciones reales, no estimaciones genéricas
        6. Si no tienes la referencia exacta, usa valores nutricionales estándar conocidos
        
        IMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin bloques de código markdown, sin ```json ni ```.
        
        Usa exactamente esta estructura JSON:
        {
            "foods": [
                {
                    "name": "nombre del alimento específico",
                    "confidence": 0.95,
                    "portion_size": "descripción precisa de la porción",
                    "estimated_grams": 28,
                    "units_count": 4,
                    "category": "categoría del alimento",
                    "nutrition": {
                        "calories": 152,
                        "protein": 1.8,
                        "carbs": 19.7,
                        "fat": 5.5
                    }
                }
            ],
            "dish_description": "descripción general del plato",
            "preparation_method": "método de preparación si es identificable",
            "total_nutrition": {
                "calories": 152,
                "protein": 1.8,
                "carbs": 19.7,
                "fat": 5.5
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
            
            # Limpiar contenido si viene envuelto en markdown
            import json
            import re
            
            # Remover bloques de código markdown si existen
            if "```json" in content:
                # Extraer solo el contenido JSON del bloque markdown
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1).strip()
                    logger.info(f"JSON extraído del markdown: {content}")
                else:
                    # Si no encuentra el patrón, intentar remover las marcas manualmente
                    content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(content)
                
                # Verificar si hay error
                if "error" in result:
                    logger.warning(f"No se pudo analizar la imagen: {result['error']}")
                    return None
                
                # Validar estructura básica
                if "foods" not in result:
                    logger.error("Respuesta de OpenAI sin formato esperado")
                    return None
                
                logger.info(f"Análisis exitoso: {len(result['foods'])} alimentos identificados")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de OpenAI: {e}")
                logger.error(f"Contenido recibido después de limpieza: {content}")
                return None
            
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {e}")
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