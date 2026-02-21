#!/bin/bash
# Script para descargar/respaldar la base de datos MongoDB local a un archivo.
# Esto creará un archivo 'gacetas_db_backup.archive' que puede ser llevado a otro servidor.

DB_NAME="gacetas_db"
ARCHIVE_NAME="gacetas_db_backup.archive"

echo "Iniciando respaldo de la base de datos '$DB_NAME'..."

# Ejecutar el dumpeo de la base de datos
mongodump --db "$DB_NAME" --archive="$ARCHIVE_NAME" --gzip

if [ $? -eq 0 ]; then
    echo "¡Respaldo exitoso! Base de datos guardada en: $ARCHIVE_NAME"
    echo "Para restaurar en el otro servidor, utiliza: mongorestore --gzip --archive=$ARCHIVE_NAME"
else
    echo "Error: Falló el respaldo de la base de datos."
    exit 1
fi
