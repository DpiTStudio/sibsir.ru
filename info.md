# Текущая статистика базы данных и фото
python manage.py backup_data --stats

# Полный бэкап (каталог + картинки + заказы + клиенты + статьи + настройки)
python manage.py backup_data

# Выгрузить только каталог товаров с картинками
python manage.py backup_data -i catalog

# Выгрузить только заказы и клиентов
python manage.py backup_data -i orders,users

# Легковесный бэкап базы данных без картинок
python manage.py backup_data --no-media

# Проверить архив перед восстановлением (Dry-run, без записи в БД)
python manage.py restore_data --dry-run

# Восстановить самый свежий бэкап
python manage.py restore_data --yes

# Чистый деплой (очистить таблицы и накатить свежие данные и фото из архива)
python manage.py restore_data <имя_архива>.zip --clear --yes