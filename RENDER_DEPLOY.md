# Render.com deployment configuration

## Variables de entorno necesarias:
# DEBUG=False
# SECRET_KEY=tu_secret_key_muy_segura_aqui
# DATABASE_URL=postgresql://user:password@host:port/dbname
# ALLOWED_HOSTS=tu-app.onrender.com,tu-app.onrender.com

## Comandos para Render:
# Build Command: ./build.sh
# Start Command: gunicorn miproyecto.wsgi:application

## Archivos importantes:
# - build.sh: Script de construcción
# - runtime.txt: Versión de Python
# - requirements-render.txt: Dependencias optimizadas para Render
# - requirements.txt: Dependencias completas para desarrollo local

## Notas:
# - Se usa requirements-render.txt para evitar problemas de compilación
# - Se precompilan archivos SCSS antes del deployment
# - Se usan dependencias precompiladas cuando es posible
