#!/bin/bash

# Definir variables
IMAGE_TAG="sipconsulting/reposip:rg-dev-gacetas"

# Asegurarse de estar en el directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo "========================================="
echo "🛠️ 1. Construyendo la imagen de Docker..."
echo "========================================="
docker build --platform linux/amd64 -t $IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen de Docker."
    exit 1
fi

echo "✅ Imagen construida exitosamente: $IMAGE_TAG"
echo ""

echo "========================================="
echo "☁️ 2. Subiendo la imagen al repositorio..."
echo "========================================="
docker push $IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Error al subir la imagen. Asegúrate de haber iniciado sesión con 'docker login'."
    exit 1
fi

echo "✅ Imagen subida exitosamente: $IMAGE_TAG"
echo "✨ Proceso completado."
