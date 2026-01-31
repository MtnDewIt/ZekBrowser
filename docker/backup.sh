#!/bin/sh
set -e

DB_PATH="/var/www/database/database.sqlite"
BACKUP_DIR="/var/www/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sqlite"
MAX_BACKUPS=30

mkdir -p "$BACKUP_DIR"

if command -v sqlite3 >/dev/null 2>&1; then
    echo "Starting backup of $DB_PATH to $BACKUP_FILE using sqlite3..."
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
else
    echo "sqlite3 not found, falling back to cp..."
    cp "$DB_PATH" "$BACKUP_FILE"
fi

if [ -f "$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_FILE"
else
    echo "Backup failed!"
    exit 1
fi

echo "Rotating backups (keeping last $MAX_BACKUPS)..."
ls -tp "$BACKUP_DIR"/backup_*.sqlite | grep -v '/$' | tail -n +$((MAX_BACKUPS + 1)) | xargs -I {} rm -- {}

echo "Backup process completed."
