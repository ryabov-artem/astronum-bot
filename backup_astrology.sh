#!/bin/bash

DATE=$(date +%F_%H-%M-%S)
BACKUP_DIR="/opt/backups/astronum"

mkdir -p $BACKUP_DIR

sqlite3 /opt/bots/astrology_bot/data/database.db "PRAGMA wal_checkpoint(FULL);"

cp /opt/bots/astrology_bot/data/database.db $BACKUP_DIR/database_$DATE.db
cp /opt/bots/astrology_bot/.env $BACKUP_DIR/env_$DATE.bak

find $BACKUP_DIR -type f -mtime +30 -delete

rclone copy $BACKUP_DIR gdrive:TG_Bots/Astronum --create-empty-src-dirs

echo "$(date) backup completed"
