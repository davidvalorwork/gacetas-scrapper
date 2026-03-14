#!/bin/bash

# Definir variables
IMAGE_NAME="gacetas-api-test-image"
CONTAINER_NAME="gacetas-api-test-container"
PORT=5000

# Asegurarse de estar en el directorio raíz del proyecto
# asumiendo que se corre desde la raíz así: ./scripts/test_docker_api.sh
cd "$(dirname "$0")/.."

echo "========================================="
echo "🚀 1. Construyendo la imagen de Docker..."
echo "========================================="
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen de Docker."
    exit 1
fi

echo "✅ Imagen construida exitosamente."
echo ""

echo "========================================="
echo "🚀 2. Levantando el contenedor temporal..."
echo "========================================="
docker run -d --name $CONTAINER_NAME -p $PORT:5000 $IMAGE_NAME

echo "⏳ Esperando 5 segundos a que Gunicorn inicie..."
sleep 5

echo "========================================="
echo "🧪 3. Realizando prueba de conexión a la API..."
echo "========================================="

# Usar curl para revisar si devuelve código 200 OK
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/)

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ Prueba exitosa. La API responde correctamente con estado 200 OK."
else
    echo "❌ Prueba fallida. La API respondió con estado: $HTTP_STATUS (o no hay respuesta)."
    echo "Mostrando últimos logs del contenedor para diagnosticar:"
    docker logs $CONTAINER_NAME
fi

echo ""
echo "========================================="
echo "🧹 4. Limpiando el entorno por completo..."
echo "========================================="

echo "Deteniendo el contenedor..."
docker stop $CONTAINER_NAME > /dev/null

echo "Eliminando el contenedor..."
docker rm $CONTAINER_NAME > /dev/null

echo "Eliminando la imagen..."
docker rmi $IMAGE_NAME > /dev/null

echo "✨ Proceso terminado. El entorno ha quedado limpio."
