#!/usr/bin/env bash

# ============================================
# Script de backup para BD MongoDB "gacetas"
# ============================================

set -euo pipefail

# ===== CONFIGURACIÓN =====

# Nombre lógico del proyecto (para el nombre del archivo)
PROJECT_NAME="gacetas"

# Carpeta donde se guardarán los backups
BACKUP_DIR="./backups"

# Parámetros de conexión a MongoDB
MONGO_HOST="localhost"
MONGO_PORT="27017"
MONGO_USER=""          # si no usas auth, dejar vacío
MONGO_PASS=""          # si no usas auth, dejar vacío
MONGO_AUTH_DB="admin"  # BD para autenticación (típicamente "admin")
MONGO_DB_NAME="gacetas_db"  # nombre real de la base de datos usada por el proyecto

# ===== FIN CONFIGURACIÓN =====

USE_DOCKER=false
ensure_mongodump() {
  if ! command -v mongodump >/dev/null 2>&1; then
    echo "mongodump local no encontrado. Comprobando si el contenedor refactor-grafo-mongodb-dev está en ejecución..."
    if docker ps --format '{{.Names}}' | grep -q 'refactor-grafo-mongodb-dev'; then
      echo "Contenedor detectado. Se usará mongodump desde Docker."
      USE_DOCKER=true
    else
      echo "No se encontró mongodump ni el contenedor 'refactor-grafo-mongodb-dev'."
      echo "Asegúrate de tener Docker corriendo con la base de datos o instala mongodump."
      exit 1
    fi
  fi
}

timestamp() {
  date +"%Y%m%d_%H%M%S"
}

mkdir -p "$BACKUP_DIR"

TS="$(timestamp)"
OUT_DIR="${BACKUP_DIR}/${PROJECT_NAME}_mongo_${TS}"

ensure_mongodump

echo "Creando backup MongoDB de la BD '${MONGO_DB_NAME}' en: $OUT_DIR"

# Creamos el directorio local
mkdir -p "$OUT_DIR"

AUTH_ARGS=()
if [[ -n "$MONGO_USER" && -n "$MONGO_PASS" ]]; then
  AUTH_ARGS+=(--username="$MONGO_USER" --password="$MONGO_PASS" --authenticationDatabase="$MONGO_AUTH_DB")
fi

if [ "$USE_DOCKER" = "true" ]; then
  # La ruta dentro del contenedor /backups está mapeada a ../gacetas/backups
  # Por lo tanto, el OUT_DIR docker es /backups/${PROJECT_NAME}_mongo_${TS}
  DOCKER_OUT_DIR="/backups/${PROJECT_NAME}_mongo_${TS}"
  docker exec refactor-grafo-mongodb-dev mongodump \
    --uri="mongodb://localhost:27017" \
    --db="$MONGO_DB_NAME" \
    --out="$DOCKER_OUT_DIR" \
    "${AUTH_ARGS[@]}"
else
  mongodump \
    --host="$MONGO_HOST" \
    --port="$MONGO_PORT" \
    --db="$MONGO_DB_NAME" \
    --out="$OUT_DIR" \
    "${AUTH_ARGS[@]}"
fi

if [[ ! -d "$OUT_DIR" || -z "$(ls -A "$OUT_DIR" 2>/dev/null)" ]]; then
  echo "ERROR: El directorio de backup local '$OUT_DIR' está vacío o no se creó."
  echo "Revisa que la base de datos '$MONGO_DB_NAME' exista y que 'mongodump' no haya mostrado errores."
  exit 1
fi

echo "Backup MongoDB completado."
echo "Directorio generado (relativo local): $OUT_DIR"

