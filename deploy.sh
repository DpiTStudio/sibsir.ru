#!/usr/bin/env bash
# ==============================================================================
# Скрипт развертывания (Deploy) ТМ «Сибсыр» на хостинг (Timeweb / Passenger WSGI)
# Использование:
#   ./deploy.sh                  - стандартный деплой (pull, pip, migrate, collectstatic, touch)
#   ./deploy.sh --restore        - деплой с восстановлением последнего бэкапа (каталог, фото, заказы, статьи)
#   ./deploy.sh --clean-restore  - чистый деплой с очисткой таблиц и накатом бэкапа
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== НАЧАЛО ДЕПЛОЯ ТМ «СИБСЫР» ==="

# 1. Поиск виртуального окружения
if [ -d "$SCRIPT_DIR/venv" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/venv/bin/pip"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/.venv/bin/pip"
else
    echo "Виртуальное окружение не найдено! Создание venv..."
    python3 -m venv venv
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/venv/bin/pip"
fi

# 2. Обновление зависимостей (при наличии requirements.txt)
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Проверка и установка зависимостей..."
    "$PIP_BIN" install -r requirements.txt --quiet
fi

# 3. Применение миграций базы данных
echo "Применение миграций базы данных..."
"$PYTHON_BIN" mysite/manage.py migrate --no-input

# 4. Сборка статических файлов
echo "Сбор статики (collectstatic)..."
"$PYTHON_BIN" mysite/manage.py collectstatic --no-input

# 5. Опциональное восстановление данных из бэкапа
if [ "$1" == "--clean-restore" ]; then
    echo "ВНИМАНИЕ: Выполняется чистый накат данных из бэкапа с очисткой таблиц..."
    "$PYTHON_BIN" mysite/manage.py restore_data --clear --yes
elif [ "$1" == "--restore" ]; then
    echo "Восстановление каталога, картинок, заказов и статей из бэкапа..."
    "$PYTHON_BIN" mysite/manage.py restore_data --yes
fi

# 6. Перезапуск веб-сервера Passenger WSGI
echo "Перезапуск приложения (touch passenger_wsgi.py)..."
if [ -f "$SCRIPT_DIR/mysite/passenger_wsgi.py" ]; then
    touch "$SCRIPT_DIR/mysite/passenger_wsgi.py"
elif [ -f "$SCRIPT_DIR/mysite/mysite/passenger_wsgi.py" ]; then
    touch "$SCRIPT_DIR/mysite/mysite/passenger_wsgi.py"
elif [ -f "$SCRIPT_DIR/tmp/restart.txt" ]; then
    touch "$SCRIPT_DIR/tmp/restart.txt"
fi

echo "=== ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН ==="

