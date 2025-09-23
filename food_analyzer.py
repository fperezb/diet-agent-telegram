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
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prompt optimizado para análisis de alimentos
        self.system_prompt = """
        Eres un experto nutricionista especializado en identificar alimentos en imágenes.
        
        Tu tarea es analizar fotos de comida y proporcionar:
        1. Lista de alimentos identificados con nivel de confianza
        2. Estimación de porciones/cantidades
        3. Descripción del plato si es una preparación específica
        
        Responde SIEMPRE en formato JSON con esta estructura:
        {
            "foods": [
                {
                    "name": "nombre del alimento",
                    "confidence": 0.95,
                    "portion_size": "descripción de la porción",
                    "category": "categoría del alimento"
                }
            ],
            "dish_description": "descripción general del plato",
            "preparation_method": "método de preparación si es identificable"
        }
        
        Si no puedes identificar comida claramente, responde:
        {"error": "No se puede identificar comida en la imagen"}
        
        Sé preciso pero también considera alimentos parcialmente visibles.
        """
    
    async def analyze_image(self, image_path: str) -> Optional[Dict]:
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
            
            # Llamada a OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
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
                                "text": "Analiza esta imagen de comida e identifica todos los alimentos visibles."
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
            
            # Intentar parsear JSON
            import json
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
                logger.error(f"Contenido recibido: {content}")
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