import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from main.backup_manager import (
    restore_backup,
    get_backup_manifest,
    get_backup_dir,
    BACKUP_SECTIONS,
    list_existing_backups,
)


class Command(BaseCommand):
    help = "Восстанавливает данные и медиафайлы (товары, картинки, заказы, клиенты, статьи) из архива резервной копии"

    def add_arguments(self, parser):
        parser.add_argument(
            "archive",
            nargs="?",
            type=str,
            default="",
            help="Путь к .zip файлу бэкапа (если не указан, используется самый свежий из папки backups)",
        )
        parser.add_argument(
            "-i", "--include",
            type=str,
            default="all",
            help="Секции для восстановления: catalog, orders, users, articles, settings (или 'all', или через запятую)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Очистить таблицы выбранных моделей перед импортом (рекомендуется для чистого деплоя)",
        )
        parser.add_argument(
            "--no-media",
            action="store_true",
            default=False,
            help="Не распаковывать картинки в media/ (только восстановление базы данных)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Проверить архив и вывести состав объектов без внесения изменений в БД",
        )
        parser.add_argument(
            "-y", "--yes",
            action="store_true",
            default=False,
            help="Пропустить интерактивный запрос подтверждения (для скриптов автоматизации и деплоя)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Показать список всех доступных архивов резервных копий и выйти",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== ВОССТАНОВЛЕНИЕ ДАННЫХ ТМ «СИБСЫР» ==="))

        if options["list"]:
            backups = list_existing_backups()
            if not backups:
                self.stdout.write(self.style.WARNING("Резервные копии не найдены в папке backups/"))
                return
            self.stdout.write(self.style.SUCCESS(f"Найдено {len(backups)} резервных копий в {get_backup_dir()}:"))
            for b in backups:
                date_str = b.get("mtime", "").strftime("%Y-%m-%d %H:%M:%S") if hasattr(b.get("mtime"), "strftime") else str(b.get("created_at", ""))
                self.stdout.write(
                    f"  • {b['filename']} [{b.get('archive_size_mb', 0)} MB] - "
                    f"Дата: {date_str}, Записей: {b.get('total_db_records', '?')}, Медиа: {b.get('media_files_count', '?')}"
                )
            return

        archive_input = options["archive"].strip()
        if archive_input:
            archive_path = Path(archive_input)
            if not archive_path.is_absolute() and not archive_path.exists():
                # Пробуем внутри папки backups
                alt_path = get_backup_dir() / archive_input
                if alt_path.exists():
                    archive_path = alt_path
        else:
            # Ищем самый свежий бэкап
            backups = list_existing_backups()
            if not backups:
                self.stderr.write(self.style.ERROR("[ОШИБКА] Архив не указан, а в папке backups/ нет резервных копий!"))
                self.stderr.write("Сначала создайте бэкап: python manage.py backup_data")
                sys.exit(1)
            archive_path = Path(backups[0]["filepath"])
            self.stdout.write(f"Автоматически выбран самый свежий архив: {archive_path.name}")

        if not archive_path.exists():
            self.stderr.write(self.style.ERROR(f"[ОШИБКА] Файл архива не найден: {archive_path}"))
            sys.exit(1)

        include_raw = options["include"].strip()
        if include_raw == "all":
            sections = list(BACKUP_SECTIONS.keys())
        else:
            sections = [s.strip().lower() for s in include_raw.split(",") if s.strip()]

        clear_tables = options["clear"]
        restore_media = not options["no_media"]
        dry_run = options["dry_run"]
        auto_yes = options["yes"]

        # Читаем манифест
        try:
            manifest = get_backup_manifest(archive_path)
            self.stdout.write(self.style.SUCCESS(f"Манифест архива: {archive_path.name}"))
            self.stdout.write(f"  • Дата создания:     {manifest.get('created_at', 'неизвестно')}")
            self.stdout.write(f"  • Описание:          {manifest.get('description', '')}")
            self.stdout.write(f"  • Записей в архиве:  {manifest.get('total_db_records', 0)}")
            self.stdout.write(f"  • Медиафайлов:       {manifest.get('media_files_count', 0)} ({manifest.get('media_total_mb', 0)} MB)")
            self.stdout.write(f"  • Секции в архиве:   {', '.join(manifest.get('sections', []))}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Предупреждение при чтении манифеста: {e}"))

        self.stdout.write(f"\nПараметры восстановления:")
        self.stdout.write(f"  • Выбранные секции:    {', '.join(sections)}")
        self.stdout.write(f"  • Очистка таблиц:      {'ВКЛЮЧЕНА (существующие данные будут удалены)' if clear_tables else 'ВЫКЛЮЧЕНА (обновление / дополнение)'}")
        self.stdout.write(f"  • Восстановление фото: {'Да' if restore_media else 'Нет (только БД)'}")
        self.stdout.write(f"  • Режим:               {'Dry-run (тестовая проверка)' if dry_run else 'Реальное восстановление'}")

        if dry_run:
            res = restore_backup(
                archive_path_or_file=archive_path,
                sections=sections,
                clear_tables=clear_tables,
                restore_media=restore_media,
                dry_run=True,
            )
            self.stdout.write(self.style.SUCCESS("\n[DRY RUN] Проверка завершена успешно!"))
            self.stdout.write(f"  • Найдено подходящих записей: {res['total_records_in_backup']}")
            self.stdout.write(f"  • Найдено медиафайлов:        {res.get('media_files_found', 0)}")
            self.stdout.write("\nЗаписи по моделям:")
            for m, cnt in res.get("records_by_model", {}).items():
                self.stdout.write(f"  - {m}: {cnt}")
            return

        if not auto_yes:
            prompt_msg = (
                "\nВНИМАНИЕ: Восстановление данных с очисткой таблиц может привести к перезаписи данных.\n"
                if clear_tables else "\nПродолжить восстановление данных? "
            )
            confirm = input(f"{prompt_msg} Введите 'yes' для подтверждения: ").strip().lower()
            if confirm not in ("yes", "y", "да"):
                self.stdout.write(self.style.WARNING("Операция отменена пользователем."))
                return

        self.stdout.write("\nВыполняется восстановление...")
        try:
            res = restore_backup(
                archive_path_or_file=archive_path,
                sections=sections,
                clear_tables=clear_tables,
                restore_media=restore_media,
                preserve_superusers=True,
                dry_run=False,
            )

            self.stdout.write(self.style.SUCCESS("\n[OK] Восстановление данных успешно завершено!"))
            self.stdout.write(f"  • Восстановлено объектов БД: {res['restored_total_records']}")
            self.stdout.write(f"  • Восстановлено картинок:    {res['restored_media_count']} ({res['restored_media_mb']} MB)")
            
            self.stdout.write("\nДетализация восстановленных моделей:")
            for m, cnt in res.get("restored_counts", {}).items():
                self.stdout.write(f"  - {m}: {cnt} записей")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\n[ОШИБКА] Сбой при восстановлении данных: {e}"))
            sys.exit(1)

