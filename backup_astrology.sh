#!/bin/bash
set -e

SRC="/opt/bots/astrology_bot"
DST="/opt/backups/astrology"
REMOTE="gdrive:TG_Bots/Astronum"

DATE=$(date +%F_%H-%M-%S)

mkdir -p "$DST"

DB_BACKUP="$DST/astrology_database_$DATE.db"
ENV_BACKUP="$DST/astrology_env_$DATE.bak"

sqlite3 "$SRC/data/database.db" ".backup '$DB_BACKUP'"
cp "$SRC/.env" "$ENV_BACKUP"

rclone copy "$DB_BACKUP" "$REMOTE/database" --create-empty-src-dirs
rclone copy "$ENV_BACKUP" "$REMOTE/env" --create-empty-src-dirs

find "$DST" -type f -mtime +30 -delete

echo "Astronum backup created and uploaded to Google Drive: $DATE"
