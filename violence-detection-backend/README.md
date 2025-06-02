# Para crear un entorno virtual
   python -m venv venv

     venv\Scripts\activate
     ```
   - En PowerShell:
     
```bash
     .\venv\Scripts\Activate
     ```
5. **Verifica que el entorno virtual esté activo**. Deberías ver `(venv)` al inicio de la línea de comandos.

5.1 **Actualizamos Python**  
    ```bash
       python -m pip install --upgrade pip

6. **Instala las dependencias del archivo `requirements.txt`**:
   
```bash
   pip install -r requirements.txt

Desactiva el entorno virtual cuando termines de trabajar:
   deactivate




📋 Instrucciones de Instalación y Ejecución
1. Requisitos Previos

Python 3.11+
PostgreSQL 15+
CUDA (opcional, para GPU)
Cámara USB Trust Taxon 2K QHD
Dispositivo Tuya WiFi configurado


2. Instalación
# Clonar o crear el proyecto
mkdir violence-detection-backend
cd violence-detection-backend

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus configuraciones

3. Configurar Base de Datos
# Crear base de datos en PostgreSQL
psql -U postgres
CREATE DATABASE sistema_deteccion_violencia;
\q

# Ejecutar script de configuración
python scripts/setup_db.py

4. Configurar Modelos
# Crear directorio de modelos
mkdir modelos

# Copiar tus modelos entrenados a:
# - modelos/yolov11_personas.pt
# - modelos/timesformer_violence_detector_best_ft.pt
# - modelos/processor/ (directorio con archivos del procesador)

# Verificar configuración
python scripts/init_models.py

5. Ejecutar el Servidor
# Desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

6. Verificar Funcionamiento

API Documentation: http://localhost:8000/docs
Health Check: http://localhost:8000/health
Login: POST a /api/v1/auth/login con credenciales

7. Configuraciones Importantes
GPU/CPU

Si no tienes GPU, el sistema automáticamente usará CPU
Ajusta USE_GPU=false en .env si prefieres forzar CPU

Cámara

La cámara USB se detecta automáticamente como índice 0
Para múltiples cámaras, ajusta el índice en la configuración

Alarma Tuya

Configura las credenciales en .env
Ejecuta python -m tinytuya wizard para obtener las claves

WebRTC

Por defecto usa STUN de Google
Para producción, considera agregar un servidor TURN

8. Solución de Problemas
Error: Modelo no encontrado

Verifica que los modelos estén en modelos/
Los nombres deben coincidir exactamente

Error: GPU no disponible

Instala CUDA y cuDNN
O configura USE_GPU=false

Error: Cámara no detectada

Verifica que la cámara esté conectada
Prueba con cv2.VideoCapture(0)

Error: Base de datos

Verifica que PostgreSQL esté ejecutándose
Confirma las credenciales en .env

9. Monitoreo

Logs en: sistema_violencia.log
Métricas en: /api/v1/incidents/estadisticas
WebSocket monitor: /ws/notifications/{user_id}

🎯 Resumen
Este backend completo incluye:

✅ Autenticación JWT
✅ WebRTC para streaming
✅ Procesamiento con YOLOv11 + DeepSort + TimesFormer
✅ Detección en tiempo real
✅ Sistema de alarmas Tuya
✅ Notificaciones WebSocket
✅ Base de datos PostgreSQL
✅ API RESTful completa
✅ Manejo de incidentes
✅ Generación de informes
✅ Gestión de usuarios y permisos

============================================================================
==============================================================================
# Generar una clave secreta segura en Python:
## SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Ejemplo resultado:
SECRET_KEY=6f0e3d5b9a4c7e2f1d8c9b7a5e3f2d1c9b8a7e6f5d4c3b2a1

## DATABASE_URL

cd violence-detection-backend
source venv/Scripts/activate  # Windows
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Ejecutar el Servidor
# Desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Principal a ajecutar
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# para detectar el dispositivo de alarma
- pip install tinytuya
- python -m tinytuya scan
- python -m tinytuya wizard

# Para generar las librerias en python
- pip freeze > requirements.txt
Mejor estructudado
- pip list --format=freeze > requirements.txt

- pip install -r requirements.txt