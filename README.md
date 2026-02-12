# Gaceta Oficial Scraper & OCR Processor

Sistema completo para descargar, procesar con OCR y almacenar las Gacetas Oficiales de Venezuela en MongoDB.

## Características

- 🔍 **Scraper**: Descarga automática de todas las gacetas desde [gacetaoficial.gob.ve](http://www.gacetaoficial.gob.ve)
- 📄 **OCR**: Extracción de texto de PDFs usando Tesseract OCR
- 💾 **MongoDB**: Almacenamiento estructurado de gacetas y su contenido
- 📊 **Progreso**: Seguimiento detallado del proceso de descarga y OCR

## Requisitos Previos

### 1. Python 3.11+
Verifica tu versión:
```bash
python --version
```

### 2. Tesseract OCR
Tesseract es necesario para extraer texto de los PDFs.

**Windows:**
1. Descarga el instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instala Tesseract (recomendado: `C:\Program Files\Tesseract-OCR`)
3. Durante la instalación, asegúrate de seleccionar el paquete de idioma **Español (spa)**
4. Agrega Tesseract al PATH o configura la ruta en el archivo `.env`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa poppler-utils
```

**macOS:**
```bash
brew install tesseract tesseract-lang poppler
```

### 3. MongoDB
Necesitas una instancia de MongoDB corriendo.

**Opción A: MongoDB Local**
- Descarga e instala desde: https://www.mongodb.com/try/download/community
- Inicia el servicio: `mongod`

**Opción B: MongoDB Atlas (Cloud)**
- Crea una cuenta gratuita en: https://www.mongodb.com/cloud/atlas
- Crea un cluster y obtén la URI de conexión

**Opción C: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Instalación

### 1. Clonar o navegar al proyecto
```bash
cd c:/Users/davidvalorwork/projects/gruposip/gacetas
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# o
.venv\Scripts\activate  # Windows CMD
```

### 3. Instalar dependencias

**Para solo scraping:**
```bash
pip install -r requirements.txt
```

**Para scraping + OCR + MongoDB:**
```bash
pip install -r requirements.txt
pip install -r requirements_ocr.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=gacetas_db
MONGO_COLLECTION_NAME=gacetas

# Tesseract Configuration (solo si no está en PATH)
# Windows example:
# TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
```

**Configuraciones de MongoDB:**
- **Local**: `MONGO_URI=mongodb://localhost:27017/`
- **Atlas**: `MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/`
- **Docker**: `MONGO_URI=mongodb://localhost:27017/`

## Uso

### Paso 1: Descargar Gacetas

Ejecuta el scraper para descargar todos los PDFs:

```bash
python scraper.py
```

Esto descargará aproximadamente **2,260 gacetas** en la carpeta `downloads/`.

**Características del scraper:**
- ✅ Detecta archivos ya descargados (no los descarga de nuevo)
- ✅ Muestra progreso en tiempo real
- ✅ Maneja errores de red automáticamente
- ✅ Respeta límites de tasa (0.5s entre descargas)

### Paso 2: Procesar con OCR y Guardar en MongoDB

#### Opción A: Modo de Prueba (sin MongoDB)

Si quieres **probar el OCR primero** sin configurar MongoDB, simplemente ejecuta:

```bash
python ocr_processor.py
```

**Sin MongoDB configurado**, el script automáticamente:
- ✅ Detecta que MongoDB no está disponible
- 🧪 Activa el **modo de prueba**
- 📄 Toma el primer PDF de `downloads/`
- 🔍 Extrae el texto usando OCR
- 📝 Muestra los primeros 1000 caracteres del texto extraído
- 💡 Explica cómo configurar MongoDB para el modo completo

**Ejemplo de salida en modo de prueba:**
```
==================================================
⚠️  MongoDB no está configurado o no disponible
==================================================

Para usar MongoDB, configura las credenciales en el archivo .env:
  1. Copia .env.example a .env
  2. Edita .env y configura MONGO_URI

==================================================
🧪 Ejecutando modo de prueba (test mode)...
==================================================

📄 Archivo de prueba: 6978-2026-01-29-EXTRAORDINARIA.pdf

📋 Metadata:
  Número: 6978
  Fecha: 29/01/2026
  Tipo: EXTRAORDINARIA

🔄 Extrayendo texto con OCR...
  Converting PDF to images...
  Processing 16 pages with OCR...
  ✓ Extracted text from 16 pages

✅ Texto extraído exitosamente!
📝 CONTENIDO DE LA PRIMERA PÁGINA:
==================================================
[Texto extraído del PDF...]
```

Esto te permite **verificar que Tesseract OCR funciona correctamente** antes de configurar MongoDB.

#### Opción B: Modo Completo (con MongoDB)

Una vez que hayas verificado que el OCR funciona y tengas MongoDB configurado:

1. **Crea el archivo `.env`** (si no lo has hecho):
```bash
cp .env.example .env
```

2. **Edita `.env`** y configura tu URI de MongoDB:
```env
MONGO_URI=mongodb://localhost:27017/
```

3. **Ejecuta el procesador**:
```bash
python ocr_processor.py
```

**Este script:**
1. ✅ Conecta a MongoDB
2. ✅ Lee cada PDF de la carpeta `downloads/`
3. ✅ Convierte cada página del PDF a imagen
4. ✅ Extrae el texto usando Tesseract OCR (idioma español)
5. ✅ Guarda en MongoDB con la siguiente estructura:

```json
{
  "_id": "ObjectId(...)",
  "filename": "43287-2026-01-02-ORDINARIA.pdf",
  "numero_gaceta": "43287",
  "fecha": "02/01/2026",
  "tipo": "ORDINARIA",
  "year": 2026,
  "month": 1,
  "day": 2,
  "total_pages": 16,
  "pages": [
    {
      "page_number": 1,
      "text": "Texto extraído de la página 1..."
    },
    {
      "page_number": 2,
      "text": "Texto extraído de la página 2..."
    }
  ],
  "full_text": "Texto completo de todas las páginas...",
  "processed_at": "2026-02-11T23:45:00.000Z",
  "file_path": "downloads/43287-2026-01-02-ORDINARIA.pdf"
}
```

**Características del procesador OCR:**
- ✅ Detecta gacetas ya procesadas (no las procesa de nuevo)
- ✅ Muestra progreso página por página
- ✅ Maneja errores de OCR automáticamente
- ✅ Almacena texto por página y texto completo

## Estructura del Proyecto

```
gacetas/
├── .env                    # Configuración (crear desde .env.example)
├── .env.example           # Plantilla de configuración
├── scraper.py             # Script de descarga de PDFs
├── ocr_processor.py       # Script de OCR y MongoDB
├── requirements.txt       # Dependencias básicas
├── requirements_ocr.txt   # Dependencias OCR y MongoDB
├── README.md             # Este archivo
└── downloads/            # PDFs descargados (creado automáticamente)
```

## Consultas en MongoDB

### Conectar a MongoDB
```bash
mongosh  # o mongo en versiones antiguas
```

### Ejemplos de consultas

```javascript
// Usar la base de datos
use gacetas_db

// Contar total de gacetas procesadas
db.gacetas.countDocuments()

// Buscar gacetas por número
db.gacetas.find({ numero_gaceta: "43287" })

// Buscar gacetas por tipo
db.gacetas.find({ tipo: "EXTRAORDINARIA" })

// Buscar gacetas por año
db.gacetas.find({ year: 2026 })

// Buscar en el texto completo
db.gacetas.find({ 
  full_text: { $regex: "palabra clave", $options: "i" } 
})

// Obtener solo el texto de una gaceta específica
db.gacetas.findOne(
  { numero_gaceta: "43287" },
  { full_text: 1, numero_gaceta: 1, fecha: 1 }
)

// Gacetas procesadas recientemente
db.gacetas.find().sort({ processed_at: -1 }).limit(10)
```

## Solución de Problemas

### Error: "Tesseract not found"
- Verifica que Tesseract esté instalado: `tesseract --version`
- Si está instalado pero no en PATH, configura `TESSERACT_PATH` en `.env`

### Error: "Cannot connect to MongoDB"
- Verifica que MongoDB esté corriendo: `mongosh` o `mongo`
- Revisa la URI en `.env`
- Si usas Atlas, verifica que tu IP esté en la whitelist

### Error: "poppler not found" (Linux/Mac)
- Linux: `sudo apt-get install poppler-utils`
- Mac: `brew install poppler`
- Windows: Poppler viene incluido con pdf2image

### OCR muy lento
- El OCR es un proceso intensivo. Cada gaceta puede tomar varios minutos
- Considera procesar en lotes o usar un servidor más potente
- Puedes reducir el DPI en `ocr_processor.py` (línea con `dpi=300`) a 200 para mayor velocidad

### Falta de espacio en disco
- Cada PDF ocupa ~500KB-2MB
- 2,260 gacetas ≈ 2-5 GB
- MongoDB puede ocupar espacio adicional similar

## Notas

- ⚠️ El proceso de OCR es **muy lento** (varios minutos por gaceta)
- ⚠️ Procesamiento completo puede tomar **días** para 2,260 gacetas
- ✅ Ambos scripts son **resumibles** (puedes detenerlos y continuarán donde quedaron)
- ✅ Los archivos ya procesados se saltan automáticamente

## Licencia

Este proyecto es de código abierto para fines educativos.

