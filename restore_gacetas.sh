#!/usr/bin/env bash

# ============================================
# Script de restauración para BD MongoDB "gacetas_db"
# Restaura un backup generado por backup_gacetas.sh
# ============================================

set -euo pipefail

# ===== CONFIGURACIÓN =====

# Nombre lógico del proyecto (para buscar backups)
PROJECT_NAME="gacetas"

# Carpeta donde se guardan los backups
BACKUP_DIR="./backups"

# Parámetros de conexión a MongoDB
MONGO_HOST="localhost"
MONGO_PORT="27017"
MONGO_USER=""          # si no usas auth, dejar vacío
MONGO_PASS=""          # si no usas auth, dejar vacío
MONGO_AUTH_DB="admin"  # BD para autenticación (típicamente "admin")
MONGO_DB_NAME="gacetas_db"  # nombre real de la base de datos usada por el proyecto

# ===== FIN CONFIGURACIÓN =====

ensure_mongorestore() {
  if ! command -v mongorestore >/dev/null 2>&1; then
    echo "mongorestore no encontrado. Intentando instalar mongodb-database-tools..."

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
      echo "Instala manualmente las MongoDB Database Tools (mongorestore)."
      echo "Ver: https://www.mongodb.com/try/download/database-tools"
      exit 1
    fi

    if ! command -v mongorestore >/dev/null 2>&1; then
      echo "mongorestore sigue sin estar disponible tras el intento de instalación."
      exit 1
    fi
  fi
}

find_latest_backup_dir() {
  if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "No existe el directorio de backups: $BACKUP_DIR"
    return 1
  fi

  # Busca el último directorio que coincida con el patrón del script de backup
  local latest
  latest="$(ls -1dt "${BACKUP_DIR}/${PROJECT_NAME}_mongo_"* 2>/dev/null | head -n 1 || true)"

  if [[ -z "$latest" ]]; then
    echo "No se encontraron directorios de backup en $BACKUP_DIR"
    return 1
  fi

  echo "$latest"
}

main() {
  local backup_path="${1-}"

  ensure_mongorestore

  if [[ -z "$backup_path" ]]; then
    echo "No se proporcionó ruta de backup. Buscando el backup más reciente en '$BACKUP_DIR'..."
    backup_path="$(find_latest_backup_dir)" || exit 1
  fi

  if [[ ! -d "$backup_path" ]]; then
    echo "El directorio de backup especificado no existe: $backup_path"
    exit 1
  fi

  # La estructura generada por backup_gacetas.sh es:
  #   <backup_path>/
  #       gacetas_db/
  #           <colecciones>.bson
  local db_dump_path="${backup_path}/${MONGO_DB_NAME}"

  if [[ ! -d "$db_dump_path" ]]; then
    echo "No se encontró el directorio de dump para la base '$MONGO_DB_NAME' en: $db_dump_path"
    echo "Revisa que el backup provenga de backup_gacetas.sh y que MONGO_DB_NAME coincida."
    exit 1
  fi

  echo "Se restaurará la base de datos '$MONGO_DB_NAME' desde:"
  echo "  $db_dump_path"
  echo
  read -rp "Esto BORRARÁ los datos actuales de '$MONGO_DB_NAME'. ¿Continuar? [y/N]: " confirm
  if [[ "${confirm,,}" != "y" && "${confirm,,}" != "yes" ]]; then
    echo "Restauración cancelada."
    exit 0
  fi

  AUTH_ARGS=()
  if [[ -n "$MONGO_USER" && -n "$MONGO_PASS" ]]; then
    AUTH_ARGS+=(--username="$MONGO_USER" --password="$MONGO_PASS" --authenticationDatabase="$MONGO_AUTH_DB")
  fi

  echo "Restaurando MongoDB en '${MONGO_HOST}:${MONGO_PORT}', base '${MONGO_DB_NAME}'..."

  mongorestore \
    --host="$MONGO_HOST" \
    --port="$MONGO_PORT" \
    --db="$MONGO_DB_NAME" \
    --drop \
    "${AUTH_ARGS[@]}" \
    "$db_dump_path"

  echo "Restauración completada con éxito."
}

main "$@"

