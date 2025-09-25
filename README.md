# Diet Agent - Bot de Telegram para Análisis Nutricional

Un bot de Telegram inteligente que analiza fotos de comida, identifica alimentos y calcula calorías usando IA.

## 🌟 Características

- 📸 **Análisis de imágenes**: Identifica alimentos en fotos usando OpenAI Vision API
- 🔥 **Cálculo de calorías**: Estima calorías y macronutrientes
- 🤖 **Bot de Telegram**: Interfaz fácil de usar a través de Telegram
- 💡 **Consejos nutricionales**: Proporciona recomendaciones personalizadas
- 📊 **Desglose nutricional**: Proteínas, carbohidratos y grasas

## 🚀 Instalación

### Prerequisitos

- Python 3.8 o superior
- Cuenta de OpenAI con acceso a Vision API
- Bot de Telegram creado con BotFather

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd dietAgent
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Token del bot de Telegram (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN=tu_token_de_telegram

# API Key de OpenAI
OPENAI_API_KEY=tu_api_key_de_openai
```

### 4. Ejecutar el bot

```bash
python main.py
```

## 🔧 Configuración

### Crear bot de Telegram

1. Habla con [@BotFather](https://t.me/BotFather) en Telegram
2. Envía `/newbot` y sigue las instrucciones
3. Guarda el token que te proporcione
4. Agrega el token a tu archivo `.env`

### Obtener API Key de OpenAI

1. Ve a [OpenAI Platform](https://platform.openai.com/)
2. Crea una cuenta o inicia sesión
3. Ve a API Keys y genera una nueva clave
4. Agrega la clave a tu archivo `.env`

## 📱 Uso

1. **Iniciar conversación**: Envía `/start` al bot
2. **Enviar foto**: Toma una foto de tu comida y envíala
3. **Recibir análisis**: El bot te responderá con:
   - Alimentos identificados
   - Calorías estimadas
   - Desglose nutricional
   - Consejos personalizados

### Comandos disponibles

- `/start` - Iniciar el bot
- `/help` - Mostrar ayuda
- `/stats` - Ver estadísticas del día (próximamente)

## 🛠️ Estructura del proyecto

```
dietAgent/
├── main.py                 # Archivo principal del bot
├── food_analyzer.py        # Analizador de imágenes con IA
├── calorie_calculator.py   # Calculadora de calorías
├── requirements.txt        # Dependencias
├── .env                   # Variables de entorno (no incluir en git)
├── .env.example          # Ejemplo de variables de entorno
├── temp_photos/          # Directorio temporal para fotos
└── README.md            # Este archivo
```

## 🧠 Cómo funciona

1. **Recepción de imagen**: El bot recibe una foto de Telegram
2. **Análisis con IA**: OpenAI Vision API identifica los alimentos
3. **Cálculo nutricional**: Base de datos local calcula calorías y macros
4. **Respuesta inteligente**: Se formatea y envía el análisis completo

## 📊 Base de datos nutricional

El bot incluye una base de datos con información nutricional de alimentos comunes:
- Proteínas (pollo, carne, pescado, huevos, legumbres)
- Carbohidratos (arroz, pasta, pan, papas)
- Verduras y frutas
- Grasas saludables

## 🔮 Funcionalidades futuras

- [ ] Seguimiento de calorías diarias
- [ ] Base de datos de usuarios
- [ ] Objetivos nutricionales personalizados
- [ ] Exportar datos a CSV
- [ ] Integración con apps de fitness
- [ ] Reconocimiento de bebidas
- [ ] Análisis de restaurantes específicos

## 🐛 Solución de problemas

### El bot no responde
- Verifica que el token de Telegram sea correcto
- Asegúrate de que el bot esté ejecutándose

### Error de análisis de imagen
- Verifica tu API key de OpenAI
- Asegúrate de tener créditos en tu cuenta de OpenAI
- Intenta con una foto más clara

### Alimentos no identificados
- La base de datos es limitada, puedes expandirla en `calorie_calculator.py`
- Algunos alimentos pueden no ser reconocidos por la IA

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Disclaimer

Este bot proporciona estimaciones nutricionales para fines informativos. No reemplaza el consejo médico profesional. Consulta con un nutricionista para necesidades dietéticas específicas.

## 📞 Soporte

Si tienes problemas o sugerencias:
- Abre un issue en GitHub
- Contacta al desarrollador

---

¡Disfruta de una alimentación más consciente con Diet Agent! 🥗✨# Deploy test Thu Sep 25 13:32:17 -03 2025
