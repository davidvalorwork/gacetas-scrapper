#!/bin/bash
# Script de instalación y ejecución para Ubuntu 24.
# Instala las dependencias (MongoDB, Python, OCR, etc) y levanta la aplicación.

set -e

echo "=== Actualizando repositorios y paquetes ==="
sudo apt-get update

echo "=== Instalando dependencias del sistema y de procesamiento (Poppler, Tesseract) ==="
sudo apt-get install -y python3 python3-pip python3-venv gnupg curl poppler-utils tesseract-ocr tesseract-ocr-spa libpoppler-cpp-dev

echo "=== Configurando e Instalando MongoDB ==="
# Llave GPG para MongoDB 7.x
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor --yes
# Agregar el repositorio (utilizando jammy que es la distro de 22.04 LTS más cercana soportada para 24.04 actualmente en repos oficiales)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Iniciar MongoDB
echo "Iniciando servicio de MongoDB..."
sudo systemctl enable mongod
sudo systemctl start mongod

echo "=== Configurando Entorno de Python ==="
# Asume que nos encontramos en la raíz del proyecto
python3 -m venv venv
source venv/bin/activate

echo "Actualizando pip..."
pip install --upgrade pip

echo "Instalando dependencias de los requisitos del proyecto..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
if [ -f "requirements_ocr.txt" ]; then
    pip install -r requirements_ocr.txt
fi

# Instalar waitress explícitamente, asumiendo que el audio se refería a "Waitress" en vez de "bototres" para correr el server en puerto 8080.
pip install waitress flask pymongo python-dotenv

echo "=== Iniciando Servicio en puerto 8080 ==="
echo "La aplicación quedará corriendo con Waitress..."
# Para la aplicación, 'app:app' asume que el archivo app.py tiene un objeto app configurado con Flask.
waitress-serve --port=8080 app:app
