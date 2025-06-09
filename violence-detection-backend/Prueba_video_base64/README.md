# 🎬 Video Recorder con Base64 y PostgreSQL

Este es un proyecto completo que permite grabar videos desde la cámara web usando OpenCV, convertirlos automáticamente a formato web-compatible con FFmpeg, codificarlos en Base64 y almacenarlos en PostgreSQL para su posterior visualización en una interfaz web moderna.

## 🚀 Características Principales

- ✅ **Grabación de video** desde cámara web con control de FPS y resolución
- ✅ **Conversión automática** a formato web-compatible (H.264/MP4)
- ✅ **Codificación Base64** para almacenamiento en base de datos
- ✅ **Almacenamiento seguro** en PostgreSQL
- ✅ **Interfaz web moderna** con reproductor integrado
- ✅ **API REST completa** con FastAPI
- ✅ **Gestión de videos** (crear, listar, reproducir, eliminar)
- ✅ **Control de duración** y detección automática de parada
- ✅ **Optimización de archivos** para web

## 🛠️ Tecnologías Utilizadas

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno y rápido para APIs
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM para manejo de base de datos
- **[PostgreSQL](https://www.postgresql.org/)** - Base de datos relacional robusta
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Validación de datos y serialización
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI de alto rendimiento

### Procesamiento de Video
- **[OpenCV (cv2)](https://opencv.org/)** - Captura y procesamiento de video en tiempo real
- **[FFmpeg](https://ffmpeg.org/)** - Conversión y optimización de video para web
- **[NumPy](https://numpy.org/)** - Operaciones numéricas y manejo de arrays

### Base de Datos
- **[psycopg2-binary](https://pypi.org/project/psycopg2-binary/)** - Adaptador PostgreSQL para Python
- **PostgreSQL 15+** - Sistema de gestión de base de datos

### Frontend
- **HTML5** - Estructura de la interfaz
- **CSS3** - Estilos y diseño responsivo
- **JavaScript ES6+** - Interactividad y comunicación con API
- **[Jinja2](https://jinja.palletsprojects.com/)** - Motor de templates

## 📁 Estructura del Proyecto

```
📦 Video Recorder
├── 📁 app/                     # Aplicación principal
│   ├── 📄 __init__.py         # Inicialización del paquete
│   ├── 📄 main.py             # Aplicación FastAPI principal
│   ├── 📄 models.py           # Modelos SQLAlchemy
│   ├── 📄 schemas.py          # Esquemas Pydantic
│   ├── 📄 database.py         # Configuración de base de datos
│   ├── 📄 config.py           # Configuración de la aplicación
│   ├── 📄 video_recorder.py   # Lógica de grabación de video
│   └── 📄 run.py              # Script de ejecución
├── 📁 static/                 # Archivos estáticos
│   ├── 📄 style.css          # Estilos CSS
│   └── 📄 script.js          # JavaScript de la interfaz
├── 📁 templates/              # Templates HTML
│   └── 📄 index.html         # Página principal
├── 📁 temp_videos/           # Directorio temporal (auto-creado)
├── 📄 requirements.txt       # Dependencias Python
├── 📄 create_db.sql         # Script de creación de BD
├── 📄 test_db.py            # Script de prueba de BD
└── 📄 README.md             # Este archivo
```

## 🔧 Requisitos del Sistema

### Software Requerido
- **Python 3.8+** - Lenguaje de programación
- **PostgreSQL 12+** - Base de datos
- **FFmpeg** - Procesamiento de video
- **Cámara web** - Para captura de video

### Librerías Python
```txt
fastapi==0.104.1          # Framework web
uvicorn==0.24.0           # Servidor ASGI
sqlalchemy==2.0.23        # ORM
psycopg2-binary==2.9.9    # Driver PostgreSQL
python-multipart==0.0.6   # Manejo de formularios
jinja2==3.1.2             # Motor de templates
opencv-python==4.8.1.78   # Procesamiento de video
numpy==1.24.3             # Operaciones numéricas
pyaudio==0.2.11           # Audio (opcional)
ffmpeg-python==0.2.0      # Binding de FFmpeg
```

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd Video-Recorder
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar FFmpeg

#### Windows
```bash
# Opción 1: Chocolatey
choco install ffmpeg

# Opción 2: Winget
winget install FFmpeg

# Opción 3: Descargar desde https://ffmpeg.org/download.html
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### 5. Configurar PostgreSQL

#### Crear base de datos
```sql
-- Conectar a PostgreSQL como superusuario
psql -U postgres

-- Crear la base de datos
CREATE DATABASE video_recorder_db;

-- Crear las tablas
\c video_recorder_db
\i create_db.sql
```

#### Configurar credenciales
Editar `app/config.py`:
```python
class Settings:
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "video_recorder_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "tu_password"  # ← Cambiar aquí
```

### 6. Probar la instalación
```bash
# Probar conexión a la base de datos
python test_db.py

# Iniciar la aplicación
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Uso de la Aplicación

### 1. Acceder a la interfaz web
```
http://localhost:8000
```

### 2. Grabar un video
1. Hacer clic en **"📹 Grabar Video"**
2. Se abrirá la ventana de la cámara
3. Presionar **ESPACIO** para iniciar/detener grabación
4. Presionar **'q'** para salir sin grabar
5. El video se procesa automáticamente y se guarda en la BD

### 3. Reproducir videos
1. Los videos aparecen en la lista principal
2. Hacer clic en **"▶️ Reproducir"** para ver el video
3. El reproductor se abre automáticamente

### 4. Eliminar videos
1. Hacer clic en **"🗑️ Eliminar"** junto al video
2. Confirmar la eliminación

## 🔌 API Endpoints

### Videos
- `GET /` - Página principal
- `POST /record-video` - Grabar nuevo video
- `GET /videos` - Listar todos los videos
- `GET /videos/{id}` - Obtener video específico
- `DELETE /videos/{id}` - Eliminar video

### Utilidades
- `GET /test-db` - Probar conexión a BD
- `GET /debug/video/{id}` - Debug de video específico

## ⚙️ Configuración Avanzada

### Parámetros de video (app/config.py)
```python
VIDEO_FPS: int = 30           # Frames por segundo
VIDEO_WIDTH: int = 640        # Ancho en píxeles
VIDEO_HEIGHT: int = 480       # Alto en píxeles
MAX_DURATION: int = 10        # Duración máxima en segundos
```

### Configuración de FFmpeg
```python
# En video_recorder.py - función convert_video_to_web_format
command = [
    'ffmpeg',
    '-i', input_path,
    '-c:v', 'libx264',        # Codec H.264
    '-profile:v', 'baseline', # Perfil compatible
    '-crf', '23',            # Calidad (18-28)
    '-r', output_fps,        # FPS de salida
    # ... más parámetros
]
```

## 🐛 Solución de Problemas

### Error: No se puede abrir la cámara
```bash
# Verificar cámaras disponibles
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

### Error: FFmpeg no encontrado
```bash
# Verificar instalación
ffmpeg -version

# Agregar al PATH si es necesario
```

### Error de conexión a PostgreSQL
```bash
# Verificar servicio
sudo systemctl status postgresql  # Linux
net start postgresql-x64-15       # Windows

# Probar conexión
psql -U postgres -d video_recorder_db
```

### Videos no se reproducen
- Verificar que FFmpeg esté instalado
- Comprobar formato del video en logs
- Verificar permisos de archivos temporales

## 📊 Rendimiento y Límites

### Límites recomendados
- **Duración máxima**: 30 segundos
- **Resolución máxima**: 1280x720
- **Tamaño máximo Base64**: 10 MB
- **FPS recomendado**: 15-30

### Optimizaciones
- Los videos se convierten automáticamente a H.264
- Compresión optimizada para web
- Archivos temporales se eliminan automáticamente
- Base64 se valida antes de guardar

## 🔒 Seguridad

- ✅ Validación de tipos de archivo
- ✅ Límites de tamaño
- ✅ Sanitización de nombres de archivo
- ✅ Manejo seguro de Base64
- ✅ Transacciones de BD con rollback

## 🚀 Despliegue en Producción

### Variables de entorno
```bash
export DB_HOST=production-db-host
export DB_PASSWORD=secure-password
export VIDEO_MAX_DURATION=15
```

### Docker (opcional)
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
# ... resto de la configuración
```

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar problemas o solicitar funcionalidades:
- Crear un issue en GitHub
- Incluir logs de error y pasos para reproducir
- Especificar versión de Python y sistema operativo

---

**Desarrollado con ❤️ usando Python, FastAPI y OpenCV**