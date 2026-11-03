#!/usr/bin/env bash
# ==============================================================================
# Скрипт восстановления данных ТМ «Сибсыр» (Linux / Timeweb)
# Использование:
#   ./restore.sh                           - восстановить последний архив
#   ./restore.sh mysite/backups/xxx.zip    - восстановить конкретный архив
#   ./restore.sh --clear --yes             - чистый накат с очисткой таблиц
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "Запуск восстановления данных..."
"$PYTHON_BIN" mysite/manage.py restore_data "$@"

