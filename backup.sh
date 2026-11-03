#!/usr/bin/env bash
# ==============================================================================
# Скрипт создания резервной копии ТМ «Сибсыр» (Linux / Timeweb / Cron)
# Использование:
#   ./backup.sh
#   ./backup.sh --catalog-only
#   ./backup.sh --no-media
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Поиск виртуального окружения Python
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

ARGS=()

for arg in "$@"; do
    case $arg in
        --catalog-only)
            ARGS+=("-i" "catalog")
            ;;
        --no-media)
            ARGS+=("--no-media")
            ;;
        --stats)
            ARGS+=("--stats")
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

echo "Запуск создания резервной копии..."
"$PYTHON_BIN" mysite/manage.py backup_data "${ARGS[@]}"

