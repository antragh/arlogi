#!/bin/bash
set -e

# Настройки
DOCS_SOURCE="./site"           # относительно текущей директории
REMOTE_USER="root"
REMOTE_HOST="192.168.168.5"
REMOTE_PATH="/opt/c/nginx/html/arlogi"
SSH_KEY="$HOME/.ssh/il-ed25519"

# Проверка наличия site/
if [ ! -d "$DOCS_SOURCE" ]; then
  echo "❌ Папка '$DOCS_SOURCE' не найдена. Запустите сначала 'mkdocs build'."
  exit 1
fi

echo "📤 Публикация документации на $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH..."

# Создаём удалённую папку, если её нет
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" \
  "mkdir -p '$REMOTE_PATH'"

# Синхронизируем содержимое (удаляем старые файлы!)
rsync -avz \
  --delete \
  --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
  -e "ssh -i '$SSH_KEY' -o StrictHostKeyChecking=no" \
  "$DOCS_SOURCE/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"

echo "✅ Готово! Документация доступна по: http://192.168.168.5/cpaiops/"
