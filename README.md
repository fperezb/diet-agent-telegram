# Diet Agent - Bot de Telegram para Análisis Nutricional 🥗✨

Un bot de Telegram inteligente que analiza fotos de comida, identifica alimentos, calcula calorías y te ayuda a mantener un seguimiento completo de tu dieta diaria.

## 🌟 Características Principales

### 📸 **Análisis Inteligente de Imágenes**
- Identifica alimentos en fotos usando OpenAI Vision API
- Reconoce ingredientes individuales y platos complejos
- Análisis preciso de porciones y cantidades

### 🔥 **Sistema Completo de Calorías**
- Cálculo automático de calorías por alimento
- Desglose detallado de macronutrientes (proteínas, carbohidratos, grasas)
- Base de datos nutricional extensa con alimentos locales

### 🎯 **Gestión de Objetivos Diarios**
- Establecimiento de metas calóricas personalizadas
- Alertas automáticas cuando superas tu objetivo
- Seguimiento en tiempo real del progreso diario

### 📊 **Seguimiento y Estadísticas**
- Historial completo de todas las comidas
- Estadísticas diarias del consumo calórico
- Reportes mensuales automáticos con tendencias
- Base de datos SQLite local para privacidad

### 🔐 **Sistema de Autorización**
- Acceso controlado por IDs de usuario autorizados
- Protección de datos y uso responsable
- Configuración de usuarios múltiples

### 🧹 **Gestión Automática de Datos**
- Limpieza automática de registros antiguos (mantiene últimos 2 meses)
- Optimización automática de la base de datos
- Exportación de datos antes de purgar

### ☁️ **Deploy en la Nube**
- Configurado para Railway con webhook
- Deploy automático desde GitHub
- Escalabilidad y disponibilidad 24/7

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

### 4. Configurar usuarios autorizados

Agrega los IDs de los usuarios autorizados a usar el bot:

```env
# IDs de usuarios autorizados (separados por comas)
ALLOWED_USER_IDS=123456789,987654321
```

Para obtener tu ID de usuario, puedes usar [@userinfobot](https://t.me/userinfobot)

### 5. Ejecutar el bot

Para desarrollo local:
```bash
python main.py
```

Para producción con webhook:
```bash
python app_webhook.py
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

#### 🚀 **Comandos Básicos**
- `/start` - Iniciar el bot y configuración inicial
- `/help` - Mostrar todos los comandos disponibles

#### 📊 **Seguimiento y Estadísticas**
- `/stats` - Ver resumen del consumo diario actual
- `/history` - Ver historial de comidas del día
- `/monthly_report` - Generar reporte mensual completo

#### 🎯 **Gestión de Objetivos**
- `/set_goal <calorías>` - Establecer objetivo calórico diario (ej: `/set_goal 2000`)
- `/get_goal` - Ver tu objetivo calórico actual
- `/clear_goal` - Eliminar objetivo actual

#### 🔧 **Administración**
- `/database_stats` - Ver estadísticas de la base de datos
- `/clear_today` - Limpiar registros del día actual

### 🍽️ **Uso Principal**

1. **Análisis de Comidas**: 
   - Envía una foto de tu comida
   - El bot analizará automáticamente los alimentos
   - Recibirás calorías, macronutrientes y consejos

2. **Seguimiento Diario**:
   - Todas las comidas se guardan automáticamente
   - Usa `/stats` para ver tu progreso del día
   - Recibe alertas si superas tu objetivo

3. **Reportes Mensuales**:
   - Usa `/monthly_report` para ver tendencias
   - Incluye promedios, días más altos/bajos
   - Análisis completo de patrones alimentarios

## 🛠️ Estructura del proyecto

```
dietAgent/
├── app_webhook.py          # Aplicación principal con webhook (producción)
├── main.py                 # Bot para desarrollo local
├── food_analyzer.py        # Analizador de imágenes con OpenAI Vision API
├── calorie_calculator.py   # Base de datos nutricional y cálculos
├── diet_database.py        # Gestión completa de base de datos SQLite
├── requirements.txt        # Dependencias del proyecto
├── runtime.txt            # Versión de Python para Railway
├── Procfile               # Configuración de proceso para Railway
├── start.sh               # Script de inicio para producción
├── DEPLOY_GUIDE.md        # Guía completa de deployment
├── .env                   # Variables de entorno (no incluir en git)
├── .env.example          # Ejemplo de variables de entorno
└── README.md             # Este archivo
```

## 🗃️ **Base de Datos**

El bot utiliza SQLite para almacenar:

### 📝 **Tabla: meals**
- Registro completo de todas las comidas analizadas
- Timestamp, usuario, alimentos identificados, calorías totales
- Desglose de macronutrientes por comida

### ⚙️ **Tabla: user_settings**
- Objetivos calóricos personalizados por usuario
- Configuraciones individuales y preferencias

### 🧹 **Gestión Automática**
- Purga automática de registros mayores a 2 meses
- Optimización periódica de la base de datos
- Estadísticas de uso y rendimiento

## 🧠 Cómo funciona

### 🔄 **Flujo de Análisis de Comidas**

1. **📸 Recepción de imagen**: El usuario envía una foto de su comida
2. **🔐 Verificación de autorización**: El sistema valida que el usuario tenga permisos
3. **🤖 Análisis con IA**: OpenAI Vision API identifica alimentos, ingredientes y porciones
4. **📊 Cálculo nutricional**: Base de datos local calcula calorías y macronutrientes precisos
5. **💾 Almacenamiento**: Se guarda el registro completo en la base de datos SQLite
6. **🎯 Verificación de objetivos**: Se compara con la meta diaria del usuario
7. **⚠️ Alertas inteligentes**: Si supera el objetivo, se envía una advertencia automática
8. **📱 Respuesta completa**: Se formatea y envía el análisis detallado

### 📈 **Sistema de Seguimiento**

1. **Acumulación diaria**: Todas las comidas se suman para el total del día
2. **Cálculo de progresos**: Comparación continua con objetivos establecidos
3. **Generación de estadísticas**: Promedios, tendencias y patrones alimentarios
4. **Reportes automáticos**: Análisis mensuales con insights personalizados

### 🔧 **Gestión de Datos**

1. **Almacenamiento local**: Todos los datos se mantienen en SQLite local
2. **Purga automática**: Sistema elimina registros antiguos (>2 meses)
3. **Optimización continua**: La base de datos se optimiza automáticamente
4. **Backup inteligente**: Los datos se exportan antes de cualquier purga

## 📊 Base de datos nutricional

### 🥘 **Alimentos Incluidos**

**Proteínas (por 100g)**
- Pollo, carne de res, cerdo, pescados variados
- Huevos, lácteos (queso, yogur, leche)
- Legumbres (frijoles, lentejas, garbanzos)
- Frutos secos y semillas

**Carbohidratos (por 100g)**
- Cereales (arroz, avena, quinoa)
- Pastas y panes variados
- Tubérculos (papa, camote, yuca)
- Frutas frescas y secas

**Verduras y Vegetales (por 100g)**
- Vegetales de hoja verde
- Verduras crucíferas (brócoli, coliflor)
- Verduras de colores variados
- Hongos y setas

**Grasas Saludables**
- Aceites vegetales (oliva, aguacate)
- Frutos secos y semillas
- Aguacate y aceitunas

**Bebidas y Otros**
- Bebidas alcohólicas y no alcohólicas
- Salsas y condimentos
- Dulces y postres
- Snacks y alimentos procesados

### 📈 **Precisión Nutricional**

- **+150 alimentos** en la base de datos
- Valores nutricionales por 100g estándar
- Cálculos automáticos basados en porciones estimadas por IA
- Macronutrientes detallados (proteínas, carbohidratos, grasas)
- Actualización continua con nuevos alimentos

## ☁️ Deployment en Railway

### � **Deploy Automático**

El proyecto está configurado para deployment automático en Railway:

1. **Configuración automática**: `Procfile` y `runtime.txt` incluidos
2. **Variables de entorno**: Se configuran directamente en Railway
3. **Webhook URL**: Railway proporciona URL automática para webhook
4. **Deploy desde GitHub**: Cada push activa un nuevo deployment
5. **Logs en tiempo real**: Monitoreo completo desde Railway dashboard

### 📋 **Variables de Entorno Requeridas**

```env
TELEGRAM_BOT_TOKEN=tu_token_del_bot
OPENAI_API_KEY=tu_api_key_openai
ALLOWED_USER_IDS=id1,id2,id3
WEBHOOK_URL=https://tu-app.railway.app
```

Ver `DEPLOY_GUIDE.md` para instrucciones completas de deployment.

## 🆕 Funcionalidades Implementadas

### ✅ **Completado**
- [x] Seguimiento completo de calorías diarias
- [x] Base de datos SQLite con gestión completa
- [x] Objetivos nutricionales personalizados con alertas
- [x] Sistema de autorización por usuario
- [x] Reportes mensuales automáticos
- [x] Purga automática de datos antiguos
- [x] Deploy en Railway con webhook
- [x] Análisis avanzado con OpenAI Vision
- [x] Historial completo de comidas
- [x] Estadísticas diarias y mensuales

### 🔮 **Funcionalidades Futuras**

- [ ] Exportar datos a CSV/Excel
- [ ] Integración con apps de fitness (Apple Health, Google Fit)
- [ ] Análisis de restaurantes y cadenas específicas
- [ ] Reconocimiento de códigos de barras
- [ ] Planificación de comidas semanales
- [ ] Análisis de tendencias nutricionales
- [ ] Integración con bases de datos nutricionales externas
- [ ] Sistema de recordatorios de comidas
- [ ] Análisis de patrones alimentarios con IA
- [ ] Recomendaciones personalizadas de mejora

## 🐛 Solución de problemas

### 🤖 **El bot no responde**
- Verifica que `TELEGRAM_BOT_TOKEN` esté correctamente configurado
- Asegúrate de que tu ID esté en `ALLOWED_USER_IDS`
- Revisa que el bot esté ejecutándose sin errores
- En Railway, verifica los logs del deployment

### 🔑 **Error de autorización**
- Usa [@userinfobot](https://t.me/userinfobot) para obtener tu ID de usuario
- Agrega tu ID a la variable `ALLOWED_USER_IDS`
- Reinicia el bot después de cambiar usuarios autorizados

### 📸 **Error de análisis de imagen**
- Verifica tu `OPENAI_API_KEY`
- Asegúrate de tener créditos suficientes en OpenAI
- Intenta con una foto más clara y bien iluminada
- Verifica que la imagen no esté corrupta

### 🍽️ **Alimentos no identificados**
- La IA puede no reconocer algunos alimentos poco comunes
- Intenta con una foto más clara que muestre bien los alimentos
- Puedes expandir la base de datos en `calorie_calculator.py`
- Reporta alimentos faltantes para futuras actualizaciones

### 💾 **Problemas de base de datos**
- Usa `/database_stats` para verificar el estado
- Los datos se purgan automáticamente cada 2 meses
- Si hay errores persistentes, reinicia la aplicación
- Los registros se respaldan antes de cualquier purga

### ☁️ **Problemas de deployment**
- Verifica todas las variables de entorno en Railway
- Asegúrate de que `WEBHOOK_URL` esté correctamente configurado
- Revisa los logs de Railway para errores específicos
- El webhook debe ser HTTPS y accesible públicamente

### 📊 **Comandos no funcionan**
- Verifica que estés usando la sintaxis correcta
- Algunos comandos requieren parámetros (ej: `/set_goal 2000`)
- Asegúrate de estar autorizado para usar el bot
- Reinicia la conversación con `/start` si hay problemas

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📈 **Estadísticas del Sistema**

### 📊 **Métricas Disponibles**
- Total de comidas analizadas
- Usuarios activos registrados  
- Promedio de calorías por comida
- Tendencias mensuales completas
- Eficiencia del sistema de purga

### 🔍 **Monitoreo**
- Usa `/database_stats` para ver estadísticas en tiempo real
- Logs detallados en Railway para debugging
- Sistema de alertas automáticas para objetivos
- Reportes mensuales con insights personalizados

## ⚠️ **Privacidad y Disclaimer**

### 🔐 **Privacidad**
- Todos los datos se almacenan localmente en SQLite
- No se comparten datos con terceros
- Sistema de autorización controla el acceso
- Purga automática de datos antiguos (>2 meses)

### 📋 **Disclaimer Médico**
Este bot proporciona **estimaciones nutricionales para fines informativos únicamente**. 

- No reemplaza el consejo médico profesional
- Las calorías son aproximaciones basadas en análisis de IA
- Consulta con un nutricionista para necesidades dietéticas específicas
- No debe usarse como única fuente para dietas restrictivas
- Los cálculos pueden variar según preparación y porciones reales

## 🤝 **Contribuir**

### � **Desarrollo**
1. Fork el proyecto desde GitHub
2. Crea una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Desarrolla y prueba tus cambios localmente
4. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
5. Push a la branch (`git push origin feature/nueva-funcionalidad`)
6. Abre un Pull Request con descripción detallada

### 💡 **Ideas y Sugerencias**
- Abre issues en GitHub para nuevas funcionalidades
- Reporta bugs con información detallada
- Sugiere mejoras en la base de datos nutricional
- Comparte casos de uso interesantes

## 📞 **Soporte y Contacto**

### 🆘 **Ayuda Técnica**
- 📝 **Issues de GitHub**: Para bugs y problemas técnicos
- 📖 **Documentación**: Ver `DEPLOY_GUIDE.md` para deployment
- 💬 **Discusiones**: Para ideas y mejoras generales

### 📧 **Contacto Directo**
- Desarrollador principal: [@tu_usuario_telegram]
- Email: tu_email@ejemplo.com
- GitHub: [@tu_usuario_github]

---

## 🎉 **¡Disfruta del Diet Agent!**

### 🌟 **Empieza Ahora**
1. 🤖 Inicia conversación con `/start`
2. 📸 Envía una foto de tu comida
3. 🎯 Establece tu objetivo con `/set_goal`
4. 📊 Revisa tu progreso con `/stats`
5. 📈 Genera reportes con `/monthly_report`

### 💪 **Alimentación Consciente**
Con Diet Agent, mantener un registro nutricional nunca fue tan fácil. 
¡Toma fotos, recibe análisis instantáneos y alcanza tus objetivos de salud!

**🥗✨ ¡Una vida más saludable está a una foto de distancia! ✨🥗**

---

*Última actualización: Septiembre 2025 - Versión 2.0 con seguimiento completo y deployment automático*
