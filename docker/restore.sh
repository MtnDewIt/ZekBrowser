#!/bin/sh
set -e

if [ -d "/var/www/backups" ]; then
    BACKUP_DIR="/var/www/backups"
    DB_PATH="/var/www/database/database.sqlite"
else
    BACKUP_DIR="./backups"
    DB_PATH="./database/database.sqlite"
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory '$BACKUP_DIR' does not exist."
    exit 1
fi

echo "Available Backups:"
i=0
for backup in $(ls -t "$BACKUP_DIR"/backup_*.sqlite); do
    echo "[$i] $(basename "$backup")"
    backups="$backups $backup"
    i=$((i+1))
done

if [ "$i" -eq 0 ]; then
    echo "No backups found."
    exit 1
fi

printf "Select a backup to restore (0-$((i-1))): "
read selection

if echo "$selection" | grep -q '^[0-9]\+$' && [ "$selection" -ge 0 ] && [ "$selection" -lt "$i" ]; then

    chosen_backup=""
    j=0
    for backup in $backups; do
        if [ "$j" -eq "$selection" ]; then
            chosen_backup=$backup
            break
        fi
        j=$((j+1))
    done
    
    echo "Restoring '$(basename "$chosen_backup")' to '$DB_PATH'..."
    printf "Are you sure? This will overwrite the current database. (y/n): "
    read confirm
    
    if [ "$confirm" != "y" ]; then
        echo "Restore cancelled."
        exit 0
    fi
    
    cp "$chosen_backup" "$DB_PATH"
    chown www-data:www-data "$DB_PATH"
    echo "Restore complete."
    echo "It is recommended to restart the container."
else
    echo "Invalid selection."
    exit 1
fi
