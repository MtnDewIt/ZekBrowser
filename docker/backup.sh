#!/bin/sh
# Snapshot the SQLite database into /var/www/backups and keep the newest MAX_BACKUPS.
# Run by cron inside the container every 6 hours (see Dockerfile).
set -eu

DB_PATH="/var/www/database/database.sqlite"
BACKUP_DIR="/var/www/backups"
MAX_BACKUPS=30
BACKUP_FILE="$BACKUP_DIR/backup_$(date +"%Y%m%d_%H%M%S").sqlite"

mkdir -p "$BACKUP_DIR"

if command -v sqlite3 >/dev/null 2>&1; then
    echo "Backing up $DB_PATH to $BACKUP_FILE with sqlite3..."
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
else
    echo "sqlite3 not found, copying $DB_PATH to $BACKUP_FILE..."
    cp "$DB_PATH" "$BACKUP_FILE"
fi

if [ ! -s "$BACKUP_FILE" ]; then
    echo "Backup failed: $BACKUP_FILE is missing or empty"
    exit 1
fi

echo "Backup created: $BACKUP_FILE"

echo "Rotating backups (keeping the newest $MAX_BACKUPS)..."
ls -t "$BACKUP_DIR"/backup_*.sqlite 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f --

echo "Backup process completed."
