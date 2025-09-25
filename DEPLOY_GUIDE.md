# 🤖 Diet Agent - Guía de Deploy en Railway

## ✅ Checklist de Deploy

### 📋 Antes de empezar
- [ ] Cuenta de GitHub creada
- [ ] Repositorio `diet-agent-telegram` creado en GitHub
- [ ] Código subido a GitHub
- [ ] Cuenta de Railway.app creada

### 🔑 Tokens necesarios
- [ ] **Telegram Bot Token** (de @BotFather)
- [ ] **OpenAI API Key** (de platform.openai.com)

### 🚂 Configuración en Railway
- [ ] Proyecto conectado con GitHub
- [ ] Variables de entorno configuradas:
  - [ ] `TELEGRAM_BOT_TOKEN`
  - [ ] `OPENAI_API_KEY`  
  - [ ] `WEBHOOK_URL` (la URL de tu proyecto Railway)

### 🔗 Configuración del webhook
- [ ] App desplegada correctamente
- [ ] Health check funcionando: `/health`
- [ ] Webhook configurado: `/set_webhook`

### 📱 Testing
- [ ] Bot responde a `/start`
- [ ] Bot analiza fotos de comida
- [ ] Recibir análisis nutricional

## 🆘 Solución de problemas

### Si el bot no responde:
1. Verifica que las variables de entorno estén bien configuradas
2. Revisa los logs en Railway
3. Asegúrate de que el webhook esté configurado

### Si no analiza las fotos:
1. Verifica tu OpenAI API Key
2. Asegúrate de tener créditos en OpenAI
3. Revisa los logs para errores

### URLs importantes:
- **Health check**: `https://tu-proyecto.railway.app/health`
- **Configurar webhook**: `https://tu-proyecto.railway.app/set_webhook`
- **Railway dashboard**: `https://railway.app/dashboard`

## 💡 Próximos pasos
- Personalizar respuestas del bot
- Agregar más alimentos a la base de datos
- Implementar estadísticas de usuario
- Agregar soporte para bebidas

¡Disfruta tu Diet Agent Bot! 🥗✨