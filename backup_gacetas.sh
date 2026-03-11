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
MONGO_DB_NAME="gacetas"  # nombre de la base de datos de gacetas

# ===== FIN CONFIGURACIÓN =====

timestamp() {
  date +"%Y%m%d_%H%M%S"
}

mkdir -p "$BACKUP_DIR"

TS="$(timestamp)"
OUT_DIR="${BACKUP_DIR}/${PROJECT_NAME}_mongo_${TS}"

echo "Creando backup MongoDB de la BD '${MONGO_DB_NAME}' en: $OUT_DIR"

AUTH_ARGS=()
if [[ -n "$MONGO_USER" && -n "$MONGO_PASS" ]]; then
  AUTH_ARGS+=(--username="$MONGO_USER" --password="$MONGO_PASS" --authenticationDatabase="$MONGO_AUTH_DB")
fi

mongodump \
  --host="$MONGO_HOST" \
  --port="$MONGO_PORT" \
  --db="$MONGO_DB_NAME" \
  --out="$OUT_DIR" \
  "${AUTH_ARGS[@]}"

echo "Backup MongoDB completado."
echo "Directorio generado: $OUT_DIR"

