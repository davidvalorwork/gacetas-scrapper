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

ensure_mongodump() {
  if ! command -v mongodump >/dev/null 2>&1; then
    echo "mongodump no encontrado. Intentando instalar mongodb-database-tools..."

    if command -v apt-get >/dev/null 2>&1; then
      echo "Detectado apt-get (Debian/Ubuntu). Ejecutando instalación con sudo."
      sudo apt-get update && sudo apt-get install -y mongodb-database-tools
    elif command -v yum >/dev/null 2>&1; then
      echo "Detectado yum (RHEL/CentOS/Fedora). Ejecutando instalación con sudo."
      sudo yum install -y mongodb-database-tools
    elif command -v brew >/dev/null 2>&1; then
      echo "Detectado Homebrew (macOS). Instalando mongodb-database-tools."
      brew tap mongodb/brew
      brew install mongodb-database-tools
    elif command -v choco >/dev/null 2>&1; then
      echo "Detectado Chocolatey (Windows). Instalando mongodb-database-tools."
      choco install -y mongodb-database-tools
    else
      echo "No se pudo detectar un gestor de paquetes compatible."
      echo "Instala manualmente las MongoDB Database Tools (mongodump)."
      echo "Ver: https://www.mongodb.com/try/download/database-tools"
      exit 1
    fi

    if ! command -v mongodump >/dev/null 2>&1; then
      echo "mongodump sigue sin estar disponible tras el intento de instalación."
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

mkdir -p "$OUT_DIR"

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

if [[ ! -d "$OUT_DIR" || -z "$(ls -A "$OUT_DIR" 2>/dev/null)" ]]; then
  echo "ERROR: El directorio de backup '$OUT_DIR' está vacío o no se creó."
  echo "Revisa que la base de datos '$MONGO_DB_NAME' exista y que 'mongodump' no haya mostrado errores."
  exit 1
fi

echo "Backup MongoDB completado."
echo "Directorio generado: $OUT_DIR"

