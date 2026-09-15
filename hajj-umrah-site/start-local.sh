#!/bin/bash
# تشغيل موقع الحج والعمرة على السيرفر المحلي
# الاستخدام: bash start-local.sh أو bash start-local.sh 8080
set -e

SITE="/home/eltokhey/hajj-umrah-site"
PHP="/home/eltokhey/.local/php/php"
PORT="${1:-8080}"
LOG="/tmp/opencode/php-server.log"

if ! lsof -iTCP:"$PORT" -sTCP:LISTEN &>/dev/null 2>&1 && ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  cd "$SITE"
  nohup "$PHP" -S 127.0.0.1:"$PORT" "$SITE/router.php" > "$LOG" 2>&1 &
  sleep 2
  echo "تم تشغيل الموقع على:"
else
  echo "الموقع يعمل بالفعل على:"
fi

echo "  http://localhost:$PORT/"
echo "لوحة التحكم: http://localhost:$PORT/wp-admin/"