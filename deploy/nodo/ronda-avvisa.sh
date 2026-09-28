#!/bin/bash
set -u
. /home/debian/nodo/telegram.env
testo=$(cat); [ -z "$testo" ] && exit 0
curl -sS --max-time 25 -o /dev/null -w '%{http_code}' \
  -d "chat_id=$TG_CHAT" --data-urlencode "text=$testo" \
  "https://api.telegram.org/bot$TG_TOKEN/sendMessage" | grep -q '^200$'
