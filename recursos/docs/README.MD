<div align="center">

# 🚨 Software Integral de Detección de Violencia Escolar
## Powered by Artificial Intelligence

![Estado del Proyecto](https://img.shields.io/badge/Estado-Activo-brightgreen?style=for-the-badge)
![Versión](https://img.shields.io/badge/Versión-1.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18.2+-61dafb?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![AI](https://img.shields.io/badge/AI-Computer_Vision-ff6b35?style=for-the-badge&logo=tensorflow&logoColor=white)

*Solución innovadora basada en Inteligencia Artificial para la prevención y detección temprana de violencia en instituciones educativas*

---

</div>

## 📋 Información del Proyecto

<table>
<tr>
<td><strong>🎓 Universidad</strong></td>
<td>San Francisco Xavier de Chuquisaca</td>
</tr>
<tr>
<td><strong>📚 Carrera</strong></td>
<td>Ingeniería en Ciencias de la Computación</td>
</tr>
<tr>
<td><strong>📖 Curso</strong></td>
<td>Inteligencia Artificial - IA3</td>
</tr>
<tr>
<td><strong>👨‍💻 Desarrollador</strong></td>
<td><strong>Gonzales Suyo Franz Reinaldo</strong></td>
</tr>
<tr>
<td><strong>👨‍🏫 Docente</strong></td>
<td>Carlos Walter Pacheco Lora</td>
</tr>
<tr>
<td><strong>📅 Periodo Académico</strong></td>
<td>2025 - 7mo Semestre</td>
</tr>
</table>

---

## 📜 Declaratoria de Autoría

> **IMPORTANTE**: Este proyecto es de autoría exclusiva del desarrollador mencionado anteriormente, creado como trabajo académico para el curso de Inteligencia Artificial. Todo el código fuente, modelos de IA, documentación y recursos han sido desarrollados por el autor, con excepción de las librerías y frameworks de terceros debidamente citados y licenciados.

---

## 🎯 Descripción General

<div align="center">

### *"Transformando la seguridad escolar con el poder de la Inteligencia Artificial"*

</div>

El **Software Integral de Detección de Violencia Escolar** es una solución completa y avanzada que utiliza técnicas de **Computer Vision** y **Deep Learning** para detectar automáticamente situaciones de violencia en entornos educativos. 

🔹 **Procesamiento en tiempo real** de video desde cámaras de seguridad  
🔹 **Identificación inteligente** de comportamientos violentos  
🔹 **Generación automática** de alertas inmediatas  
🔹 **Intervención rápida** para garantizar la seguridad estudiantil  

---

## 🌟 Características Principales

<div align="center">

| Característica | Descripción | Estado |
|:-------------:|:------------|:------:|
| 🤖 **Detección IA** | Análisis en tiempo real mediante modelos neurales | ✅ |
| 🚨 **Alertas Automáticas** | Notificaciones visuales, sonoras y de voz | ✅ |
| 📹 **Grabación Inteligente** | Captura automática de evidencia | ✅ |
| 📊 **Dashboard Web** | Interfaz moderna para monitoreo | ✅ |
| 🔄 **Multi-Cámara** | Arquitectura escalable | ✅ |
| 📈 **Reportes Avanzados** | Estadísticas y análisis detallados | ✅ |
| 💾 **Base de Datos** | Almacenamiento seguro de incidentes | ✅ |

</div>

---

## 🏗️ Arquitectura del Software

<div align="center">

```mermaid
graph TB
    subgraph "🖥️ Frontend Layer"
        A[🎛️ Dashboard Web] --> B[📺 Monitoreo Tiempo Real]
        A --> C[📋 Gestión de Incidentes]
        A --> D[📊 Reportes y Analytics]
    end
    
    subgraph "🚀 Backend Layer"
        E[🌐 API REST] --> F[🔌 WebSocket Server]
        E --> G[🔐 Sistema Autenticación]
        E --> H[💾 Gestión Base Datos]
    end
    
    subgraph "🧠 AI Engine"
        I[🎯 YOLOv11 Detector] --> K[⚡ TimesFormer Analyzer]
        J[👥 DeepSort Tracker] --> K
        K --> L[🔄 AI Pipeline]
    end
    
    subgraph "🔧 Services Layer"
        M[📢 Alarma Tuya WiFi] --> N[🗣️ Alertas de Voz]
        O[🎬 Grabación Evidencia] --> P[💿 Storage Base64]
    end
    
    subgraph "🗄️ Database Layer"
        Q[(🐘 PostgreSQL)]
        R[📝 Incidentes]
        S[👤 Usuarios]
        T[📷 Cámaras]
        U[🎞️ Evidencias]
    end
    
    A --> E
    E --> I
    L --> M
    L --> O
    H --> Q
    Q --> R
    Q --> S
    Q --> T
    Q --> U
```

</div>

---

## 🤖 Modelos de Inteligencia Artificial

<div align="center">

### 🧬 *Powered by State-of-the-Art Deep Learning*

</div>

<details>
<summary><h3>🎯 1. YOLOv11 - Detector de Personas</h3></summary>

**📊 Especificaciones Técnicas:**
- 🏗️ **Arquitectura**: Convolutional Neural Network optimizada
- 🎯 **Propósito**: Detección y localización de personas en tiempo real  
- 🎖️ **Precisión**: > 95% en detección de personas
- ⚡ **Velocidad**: ~30 FPS (GPU) / ~15 FPS (CPU)
- 🖼️ **Resolución**: 416x416 píxeles optimizada
- ⚙️ **Umbral**: 0.58 de confianza mínima

</details>

<details>
<summary><h3>🧠 2. TimesFormer - Análisis de Violencia</h3></summary>

**📊 Especificaciones Técnicas:**
- 🏗️ **Arquitectura**: Vision Transformer para análisis espacio-temporal
- 🎯 **Propósito**: Clasificación de secuencias de video para detectar violencia
- 🎓 **Entrenamiento**: Transfer Learning + Fine-Tuning especializado
- 📊 **Métricas**: F1-Score: 0.96, Accuracy: 0.93
- 🖼️ **Entrada**: Secuencias de 8 frames de 224x224 píxeles
- ⚙️ **Umbral**: 70% de probabilidad para activar alertas

</details>

<details>
<summary><h3>👥 3. DeepSort - Sistema de Seguimiento</h3></summary>

**📊 Especificaciones Técnicas:**
- 🎯 **Propósito**: Seguimiento continuo de personas
- ⚙️ **Funcionalidad**: Identificadores únicos por persona
- 🔄 **Integración**: Combinado con YOLO para tracking temporal
- 📈 **Capacidad**: Hasta 20 personas simultáneas

</details>

---

## 💻 Stack Tecnológico

<div align="center">

### 🛠️ *Tecnologías de Vanguardia*

</div>

<table>
<tr>
<td width="50%">

#### 🐍 **Backend Stack**
```python
FastAPI 0.115.12          # 🚀 Framework web asíncrono
PostgreSQL 15+            # 🐘 Base de datos robusta
SQLAlchemy 2.0.41         # 🔗 ORM avanzado
PyTorch 2.7.0             # 🧠 Deep Learning framework
OpenCV 4.11.0             # 👁️ Computer Vision
ONNX Runtime 1.22.0       # ⚡ Optimización de modelos
Transformers 4.52.3       # 🤗 Hugging Face models
Ultralytics 8.3.144       # 🎯 YOLOv11 oficial
```

</td>
<td width="50%">

#### ⚛️ **Frontend Stack**
```javascript
React 18.2.0              // ⚛️ UI Framework moderno
Vite 5.0.0                // ⚡ Build tool ultrarrápido
Tailwind CSS 3.4.17       // 🎨 Utility-first CSS
Axios 1.4.0               // 🌐 HTTP client
React Router DOM 6.14.2   // 🛣️ Enrutamiento SPA
WebRTC API                // 📺 Streaming tiempo real
Heroicons 2.2.0           // 🎨 Iconos elegantes
```

</td>
</tr>
</table>

<div align="center">

#### 🧠 **Artificial Intelligence Stack**
```python
TimesFormer      # 🎬 Video analysis transformer
YOLOv11         # 🎯 Real-time object detection  
ONNX 1.22.0     # 📦 Optimized model format
NumPy 2.2.6     # 🔢 Numerical computing
OpenCV          # 👁️ Computer vision library
```

</div>

---

## 📂 Estructura del Proyecto

<div align="center">

### 🗂️ *Organización Modular y Escalable*

</div>

```
📦 school-violence-prevention/
├── 🚀 violence-detection-backend/           # Backend FastAPI
│   ├── 📁 app/
│   │   ├── 🧠 ai/                           # Módulos de IA
│   │   │   ├── 🎯 yolo_detector.py          # Detector YOLOv11
│   │   │   ├── 🧬 violence_detector.py      # Detector TimesFormer
│   │   │   ├── ⚡ timesformer_processor.py   # Procesador de frames
│   │   │   ├── 🔄 pipeline.py               # Pipeline principal
│   │   │   └── 📦 model_loader.py           # Cargador de modelos
│   │   ├── 🌐 api/                          # Endpoints API
│   │   │   ├── 📋 v1/                       # API versión 1
│   │   │   │   ├── 🔐 auth.py               # Autenticación JWT
│   │   │   │   ├── 📷 cameras.py            # Gestión de cámaras
│   │   │   │   ├── 📝 incidents.py          # Gestión de incidentes
│   │   │   │   └── 🗣️ voice_alerts.py       # Alertas inteligentes
│   │   │   └── 🔌 websocket/                # WebSocket y WebRTC
│   │   │       ├── 📺 stream_handler.py     # Manejo de streams
│   │   │       └── 📡 rtc_signaling.py      # Señalización WebRTC
│   │   ├── ⚙️ core/                         # Configuración central
│   │   │   ├── 🔧 config.py                 # Configuraciones
│   │   │   ├── 🗄️ database.py              # Conexión BD
│   │   │   └── 🔒 security.py               # Seguridad JWT
│   │   ├── 📊 models/                       # Modelos de datos
│   │   │   ├── 📝 incident.py               # Modelo de incidentes
│   │   │   ├── 📷 camera.py                 # Modelo de cámaras
│   │   │   └── 👤 user.py                   # Modelo de usuarios
│   │   ├── 🛠️ services/                     # Servicios de negocio
│   │   │   ├── 🧠 ai_service.py             # Servicio principal IA
│   │   │   ├── 📝 incident_service.py       # Lógica de incidentes
│   │   │   ├── 📷 camera_service.py         # Gestión de cámaras
│   │   │   ├── 🚨 alarm_service.py          # Control alarmas IoT
│   │   │   └── 🗣️ voice_alert_service.py    # Alertas con IA
│   │   ├── 🔧 utils/                        # Utilidades
│   │   │   ├── 📋 logger.py                 # Sistema de logs
│   │   │   └── 🎬 video_base64_utils.py     # Conversión video
│   │   └── 🚀 main.py                       # Aplicación principal
│   ├── 🧠 models_weights/                   # Pesos modelos IA
│   │   ├── 🎯 yolo/                         # Modelos YOLO
│   │   └── 🧬 timesformer/                  # Modelos TimesFormer
│   ├── 📓 notebooks/                        # Jupyter Notebooks
│   ├── 🔧 scripts/                          # Scripts utilidad
│   ├── 📄 requirements.txt                  # Dependencias Python
│   └── ⚙️ .env                             # Variables entorno
└── ⚛️ app-violence-prevention/              # Frontend React
    ├── 📁 src/
    │   ├── 🧩 components/                   # Componentes React
    │   │   ├── 🎨 Layout.jsx                # Layout principal
    │   │   ├── 🔐 Auth.jsx                  # Autenticación
    │   │   ├── 🛡️ ProtectedRoute.jsx        # Rutas protegidas
    │   │   └── 🔔 NotificationSystem.jsx    # Sistema notificaciones
    │   ├── 📄 pages/                        # Páginas principales
    │   │   ├── 📊 DashboardContent.jsx      # Dashboard
    │   │   ├── 📷 Cameras.jsx               # Gestión cámaras
    │   │   ├── 🔍 CameraDetail.jsx          # Detalle cámara
    │   │   ├── 📋 Incidents.jsx             # Lista incidentes
    │   │   └── 📝 IncidentDetail.jsx        # Detalle incidente
    │   ├── 🛠️ utils/                        # Utilidades
    │   │   ├── 🌐 api.js                    # Cliente API
    │   │   └── 📺 webrtc.js                 # Cliente WebRTC
    │   └── ⚛️ App.jsx                       # Componente raíz
    ├── 📦 package.json                      # Dependencias Node.js
    └── ⚙️ vite.config.js                   # Configuración Vite
```

---

## 🚀 Guía de Instalación

<div align="center">

### ⚡ *Configuración Rápida y Sencilla*

</div>

### 📋 Prerrequisitos del Sistema

<table>
<tr>
<td align="center"><strong>🐍 Python</strong><br/>3.11+</td>
<td align="center"><strong>🟢 Node.js</strong><br/>18+</td>
<td align="center"><strong>🐘 PostgreSQL</strong><br/>15+</td>
<td align="center"><strong>🎬 FFmpeg</strong><br/>Latest</td>
<td align="center"><strong>🚀 CUDA</strong><br/>12.0+ (Opcional)</td>
</tr>
</table>

---

### 🐍 Configuración del Backend

<details>
<summary><strong>🔽 Clic aquí para ver los pasos detallados</strong></summary>

#### **1️⃣ Clonar el Repositorio**
```bash
git clone https://github.com/Franz-Gonzales/school-violence-prevention-IA3.git
cd school-violence-prevention/violence-detection-backend
```

#### **2️⃣ Crear Entorno Virtual**
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate
```

#### **3️⃣ Instalar Dependencias**
```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

#### **4️⃣ Configurar Base de Datos**
```sql
-- Crear base de datos en PostgreSQL
psql -U postgres
CREATE DATABASE deteccion_violencia;
\q
```

```bash
# Ejecutar script de configuración
python scripts/setup_db.py
```

#### **5️⃣ Configurar Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones personalizadas
```

#### **6️⃣ Configurar Modelos de IA**
```bash
# Crear estructura de directorios
mkdir -p models_weights

# Ejecutar script de inicialización
python scripts/init_models.py
```

#### **7️⃣ Ejecutar el Backend**
```bash
# Modo desarrollo (con recarga automática)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Modo producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

</details>

---

### ⚛️ Configuración del Frontend

<details>
<summary><strong>🔽 Clic aquí para ver los pasos detallados</strong></summary>

#### **1️⃣ Navegar al Directorio**
```bash
cd ../app-violence-prevention
```

#### **2️⃣ Instalar Dependencias**
```bash
# Con npm
npm install

# O con yarn (si prefieres)
yarn install
```

#### **3️⃣ Configurar Variables de Entorno**
```bash
# Crear archivo .env
echo "VITE_API_URL=http://localhost:8000" > .env
```

#### **4️⃣ Ejecutar el Frontend**
```bash
# Modo desarrollo
npm run dev

# Construir para producción
npm run build
```

</details>

---

### 🔧 Configuración Adicional

<details>
<summary><strong>🔽 Configuraciones Opcionales</strong></summary>

#### **📢 Alarma Tuya WiFi (Opcional)**
```bash
# Instalar herramientas Tuya
pip install tinytuya

# Configurar dispositivo
python -m tinytuya wizard
```

#### **📷 Verificar Cámara USB**
```bash
# Verificar cámaras disponibles
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

</details>

---

## 🎮 Guía de Uso

<div align="center">

### 🖥️ *Interfaz Intuitiva y Poderosa*

</div>

### 🔐 **1. Acceso al Sistema**

<div align="center">

**🌐 URL**: `http://localhost:3000`

| Campo | Valor |
|:-----:|:-----:|
| 📧 **Email** | `admin@ejemplo.com` |
| 🔑 **Password** | `admin123` |

</div>

### 📊 **2. Dashboard Principal**

<table>
<tr>
<td width="50%">
<h4>📈 Estadísticas en Tiempo Real</h4>
<ul>
<li>🔢 Incidentes detectados hoy</li>
<li>📷 Cámaras activas en el sistema</li>
<li>✅ Tasa de resolución de incidentes</li>
<li>💚 Estado operativo del sistema</li>
</ul>
</td>
<td width="50%">
<h4>🚨 Panel de Control</h4>
<ul>
<li>⚠️ Incidentes en curso</li>
<li>🔔 Alertas prioritarias</li>
<li>📋 Incidentes recientes</li>
<li>⚙️ Configuración rápida</li>
</ul>
</td>
</tr>
</table>

### 📹 **3. Gestión de Cámaras**

- **📋 Lista Completa**: Ver todas las cámaras configuradas
- **🎥 Streaming Live**: Visualización en tiempo real
- **🤖 Control IA**: Activar/desactivar análisis inteligente
- **⚙️ Configuración**: Ajustar parámetros personalizados

### 🚨 **4. Sistema de Detección Automática**

1. **📹 Captura**: Video a 15 FPS desde cámaras
2. **🔍 Detección**: YOLOv11 identifica personas (>58% confianza)
3. **🧠 Análisis**: TimesFormer analiza secuencias temporales
4. **⚡ Decisión**: Si probabilidad >70% → Activar alerta
5. **🚨 Respuesta**: Acciones automáticas inmediatas

---

## 🧠 Funcionamiento del Motor de IA

<div align="center">

### 🔄 *Pipeline de Procesamiento Inteligente*

</div>

```mermaid
sequenceDiagram
    participant 📷 as Cámara
    participant 🎯 as YOLOv11
    participant 🧠 as TimesFormer
    participant 🚨 as Sistema Alertas
    participant 💾 as Base Datos
    
    📷->>🎯: Frame de video (15 FPS)
    🎯->>🎯: Detectar personas (conf > 58%)
    🎯->>🧠: Enviar detecciones + frame
    🧠->>🧠: Analizar secuencia temporal (8 frames)
    🧠->>🧠: Calcular probabilidad violencia
    
    alt 🚨 Violencia detectada (>70%)
        🧠->>🚨: ⚠️ ACTIVAR ALERTA CRÍTICA
        🚨->>🚨: 📹 Iniciar grabación evidencia
        🚨->>🚨: 🔊 Reproducir alerta sonora
        🚨->>🚨: 🗣️ Generar alerta de voz
        🚨->>💾: 💾 Crear registro incidente
    else ✅ No violencia detectada
        🧠->>📷: ✅ Continuar monitoreo normal
    end
```

### ⚙️ **Parámetros de Configuración Optimizados**

<div align="center">

| Componente | Parámetro | Valor | Descripción |
|:----------:|:----------|:-----:|:------------|
| 🎯 **YOLOv11** | Confianza | `0.58` | Umbral mínimo detección |
| 🎯 **YOLOv11** | Resolución | `416x416` | Tamaño entrada optimizado |
| 🧠 **TimesFormer** | Frames | `8` | Secuencia análisis temporal |
| 🧠 **TimesFormer** | Umbral | `0.70` | Probabilidad activación |
| 📷 **Cámara** | FPS | `15` | Velocidad captura |
| 🎬 **Evidencia** | Duración | `10s` | Tiempo grabación |

</div>

---

## 📊 Métricas y Rendimiento

<div align="center">

### 🎯 *Resultados del Modelo TimesFormer*

</div>

<table align="center">
<tr>
<th>Métrica</th>
<th>Transfer Learning</th>
<th>Fine-Tuning</th>
<th>🏆 Test Final</th>
</tr>
<tr>
<td><strong>Accuracy</strong></td>
<td>89.45%</td>
<td>96.13%</td>
<td><strong>95.80%</strong></td>
</tr>
<tr>
<td><strong>Precision</strong></td>
<td>88.23%</td>
<td>96.01%</td>
<td><strong>95.45%</strong></td>
</tr>
<tr>
<td><strong>Recall</strong></td>
<td>90.12%</td>
<td>96.20%</td>
<td><strong>95.98%</strong></td>
</tr>
<tr>
<td><strong>F1-Score</strong></td>
<td>89.17%</td>
<td>96.10%</td>
<td><strong>95.71%</strong></td>
</tr>
<tr>
<td><strong>Specificity</strong></td>
<td>88.76%</td>
<td>99.33%</td>
<td><strong>99.12%</strong></td>
</tr>
<tr>
<td><strong>ROC AUC</strong></td>
<td>94.56%</td>
<td>98.83%</td>
<td><strong>98.64%</strong></td>
</tr>
</table>

### ⚡ **Rendimiento del Sistema**

<div align="center">

| Categoría | Especificación | Rendimiento |
|:---------:|:---------------|:------------|
| 🖥️ **Hardware Mínimo** | Intel i5, 8GB RAM, SSD 256GB | ✅ Funcional |
| 🔥 **Hardware Recomendado** | Intel i7, 16GB RAM, SSD 512GB, GTX 1660 | ⚡ Óptimo |
| 🚀 **Hardware Premium** | Intel i9, 32GB RAM, SSD 1TB, RTX 3070+ | 🔥 Máximo |
| ⚡ **Latencia** | < 200ms para detección completa | 🎯 Tiempo Real |
| 📺 **FPS** | 15 FPS estables por cámara | 🎬 Fluido |
| 🎯 **Precisión** | 96% accuracy en detección | 🏆 Excelente |
| 📈 **Escalabilidad** | Hasta 8 cámaras simultáneas | 🔄 Escalable |

</div>

---

## 🔧 Configuración Avanzada

<details>
<summary><h3>🎛️ Variables de Entorno Completas</h3></summary>

```bash
# ==================== CONFIGURACIÓN PRINCIPAL ====================
APP_NAME="Software de Detección de Violencia Escolar"
APP_VERSION="1.0.0"
DEBUG=True
SECRET_KEY="tu_clave_secreta_super_segura_aqui"

# ==================== BASE DE DATOS ====================
DATABASE_URL="postgresql+asyncpg://usuario:password@localhost:5432/deteccion_violencia"
DB_ECHO=False
DB_POOL_SIZE=5

# ==================== MODELOS IA ====================
MODELOS_PATH="./models_weights"
YOLO_MODEL="yolo/exported_v3/best.pt"
TIMESFORMER_MODEL="timesformer/exported_models2/timesformer_violence_detector_half.onnx"
USE_GPU=True

# ==================== CONFIGURACIÓN CÁMARA ====================
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15

# ==================== UMBRALES IA ====================
YOLO_CONF_THRESHOLD=0.58
VIOLENCE_THRESHOLD=0.60
TIMESFORMER_FRAMES=8

# ==================== ALARMA TUYA ====================
TUYA_DEVICE_ID="tu_device_id_aqui"
TUYA_IP_ADDRESS="192.168.1.100"
TUYA_LOCAL_KEY="tu_local_key_aqui"
TUYA_DEVICE_VERSION="3.5"

# ==================== ALERTAS DE VOZ ====================
ELEVENLABS_API_KEY="tu_api_key_elevenlabs"
ELEVENLABS_VOICE_ID="onwK4e9ZLuTAKqWW03F9"
VOICE_ALERTS_ENABLED=True
```

</details>

<details>
<summary><h3>🐳 Despliegue con Docker</h3></summary>

#### **Dockerfile para Backend**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: deteccion_violencia
      POSTGRES_USER: usuario
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./violence-detection-backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql+asyncpg://usuario:password@postgres:5432/deteccion_violencia
    volumes:
      - ./models_weights:/app/models_weights

  frontend:
    build: ./app-violence-prevention
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

</details>

---

## 🛠️ Desarrollo y Contribución

<div align="center">

### 🤝 *Contribuye al Futuro de la Seguridad Escolar*

</div>

### 🧪 **Testing**

```bash
# 🐍 Tests del Backend
cd violence-detection-backend
python -m pytest tests/ -v --cov=app

# ⚛️ Tests del Frontend  
cd app-violence-prevention
npm test
```

### 📝 **Estándares de Código**

<table>
<tr>
<td width="50%">

**🐍 Python (Backend)**
```bash
black .                 # 🎨 Formateo código
flake8 .               # 🔍 Linting
mypy .                 # 🏷️ Type checking
```

</td>
<td width="50%">

**⚛️ JavaScript (Frontend)**
```bash
npm run lint           # 🔍 ESLint
npm run format         # 🎨 Prettier
npm run type-check     # 🏷️ Type checking
```

</td>
</tr>
</table>

### 🔄 **Flujo de Contribución**

1. 🍴 **Fork** del repositorio
2. 🌿 **Crear rama**: `git checkout -b feature/nueva-funcionalidad`  
3. 💻 **Desarrollar** funcionalidad con tests
4. 📝 **Commit**: `git commit -m 'feat: agregar nueva funcionalidad'`
5. 🚀 **Push**: `git push origin feature/nueva-funcionalidad`
6. 📋 **Pull Request** con descripción detallada

---

## 📚 Documentación y Recursos

<div align="center">

### 📖 *Recursos de Aprendizaje Avanzado*

</div>

#### **📄 Papers y Referencias Académicas**
- 📚 [TimesFormer: Is Space-Time Attention All You Need for Video Understanding?](https://arxiv.org/abs/2102.05095)
- 📚 [YOLOv11: Real-Time Object Detection](https://github.com/ultralytics/ultralytics)
- 📚 [DeepSORT: Simple Online and Realtime Tracking](https://arxiv.org/abs/1703.07402)

#### **🔗 Documentación Técnica**
- 🌐 [FastAPI Documentation](https://fastapi.tiangolo.com/)
- ⚛️ [React Documentation](https://reactjs.org/docs/)
- 🐘 [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- 🤗 [Transformers Library](https://huggingface.co/docs/transformers/)

#### **🎓 Conceptos Clave**

<div align="center">

```mermaid
mindmap
  root((🧠 Computer Vision))
    🎯 Detección Objetos
      YOLO
      R-CNN  
      SSD
    🎬 Análisis Video
      TimesFormer
      Video Transformer
      3D CNN
    👥 Tracking
      DeepSORT
      ByteTrack
      FairMOT
    🛠️ Procesamiento
      OpenCV
      FFmpeg
      PIL
```

</div>

---

## 🐛 Solución de Problemas

<div align="center">

### 🔧 *Guía de Troubleshooting*

</div>

<details>
<summary><h3>❓ Problemas Comunes y Soluciones</h3></summary>

#### **1️⃣ Error: Modelo no encontrado**
```bash
# 🔧 Solución
python scripts/init_models.py
# O descargar modelos manualmente a models_weights/
```

#### **2️⃣ Error: GPU no disponible**
```bash
# 🔍 Verificar CUDA
nvidia-smi

# ⚙️ Configurar para CPU
# En .env: USE_GPU=False
```

#### **3️⃣ Error: Cámara no detectada**
```bash
# 🔍 Verificar cámaras disponibles
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# ⚙️ Cambiar índice en .env
# CAMERA_INDEX=1  # Probar diferentes índices
```

#### **4️⃣ Error: Base de datos**
```bash
# 🔍 Verificar PostgreSQL
sudo systemctl status postgresql  # Linux
net start postgresql-x64-15       # Windows

# 🔧 Recrear base de datos
python scripts/setup_db.py
```

#### **5️⃣ Frontend no carga**
```bash
# 🧹 Limpiar caché
rm -rf node_modules package-lock.json
npm install

# 🔍 Verificar puertos
netstat -tulpn | grep :3000
```

</details>

---

## 🙏 Agradecimientos

<div align="center">

### 💖 *Reconocimientos Especiales*

</div>

<table>
<tr>
<td align="center" width="50%">

#### 👨‍🏫 **Agradecimientos Académicos**
- 🏛️ **Universidad**: San Francisco Xavier de Chuquisaca
- 👨‍🏫 **Docente**: Carlos Walter Pacheco Lora
- 📚 **Programa**: Ingeniería en Ciencias de la Computación

</td>
<td align="center" width="50%">

#### 🛠️ **Tecnologías y Herramientas**
- 🤗 **Hugging Face**: Por los modelos pre-entrenados
- 🎯 **Ultralytics**: Por la implementación YOLOv11
- 🧠 **Facebook Research**: Por TimesFormer original
- 🚀 **FastAPI Team**: Por el framework excepcional
- ⚛️ **React Team**: Por la librería UI moderna

</td>
</tr>
</table>

<div align="center">

#### 📊 **Comunidad Open Source**
*Gracias a toda la comunidad de desarrolladores que hacen posible la innovación*

</div>

---

## 📞 Contacto y Soporte

<div align="center">

### 🤝 *Conecta Conmigo*

</div>

<table align="center">
<tr>
<td align="center">
<img src="https://img.shields.io/badge/Desarrollador-Franz_Reinaldo_Gonzales_Suyo-blue?style=for-the-badge&logo=github&logoColor=white"/>
</td>
</tr>
<tr>
<td align="center">
<a href="mailto:gonzalesfranzreinaldo@gmail.com">
<img src="https://img.shields.io/badge/Email-gonzalesfranzreinaldo@gmail.com-red?style=for-the-badge&logo=gmail&logoColor=white"/>
</a>
</td>
</tr>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/WhatsApp-+591_72863820-green?style=for-the-badge&logo=whatsapp&logoColor=white"/>
</td>
</tr>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/Rol-Full_Stack_AI_Developer-purple?style=for-the-badge&logo=code&logoColor=white"/>
</td>
</tr>
</table>

### 🆘 **Canales de Soporte**

<div align="center">

[![Issues](https://img.shields.io/badge/🐛_Issues-GitHub-orange?style=for-the-badge)](https://github.com/Franz-Gonzales/school-violence-prevention-IA3/issues)
[![Docs](https://img.shields.io/badge/📖_Documentación-Wiki-blue?style=for-the-badge)](https://github.com/Franz-Gonzales/school-violence-prevention-IA3/wiki)
[![Email](https://img.shields.io/badge/📧_Contacto_Directo-Email-red?style=for-the-badge)](mailto:gonzalesfranzreinaldo@gmail.com)

</div>

---

<div align="center">

## 🔗 Recursos del Proyecto

[![Dataset](https://img.shields.io/badge/📊_Dataset-Contactar_Autor-yellow?style=for-the-badge)](mailto:gonzalesfranzreinaldo@gmail.com)
[![Modelos](https://img.shields.io/badge/🧠_Modelos_IA-Disponibles-green?style=for-the-badge)](mailto:gonzalesfranzreinaldo@gmail.com)
[![Demo](https://img.shields.io/badge/🎥_Demo_Video-Ver_Aquí-red?style=for-the-badge)](#)

---

### 🏆 *Proyecto Desarrollado con Pasión para la Seguridad Escolar*

**🎓 Universidad San Francisco Xavier de Chuquisaca**  
**👨‍💻 Desarrollado por Franz Reinaldo Gonzales Suyo**  
**📅 2025 - Semestre 7**

---

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=Franz-Gonzales.school-violence-prevention-IA3)
![GitHub last commit](https://img.shields.io/github/last-commit/Franz-Gonzales/school-violence-prevention-IA3)
![GitHub repo size](https://img.shields.io/github/repo-size/Franz-Gonzales/school-violence-prevention-IA3)

</div>

---

<div align="center">

*"La tecnología al servicio de la educación segura"* 🎓✨

**⭐ Si este proyecto te resulta útil, ¡no olvides darle una estrella! ⭐**

</div>