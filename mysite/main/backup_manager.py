"""
Менеджер резервного копирования и восстановления данных сайта ТМ «Сибсыр».
Поддерживает выгрузку и восстановление:
- Каталога товаров (категории, товары, акции, промокоды, отзывы) вместе с изображениями
- Заказов и позиций заказов
- Клиентов (аккаунты пользователей, расширенные профили физ. и юр. лиц, заявки)
- Статей блога вместе с иллюстрациями
- Настроек сайта и сопутствующего контента (страницы, брендинг, доставка, FAQ)
"""

import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management.color import color_style
from django.db import connection, transaction
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

logger = logging.getLogger(__name__)

# Конфигурация секций данных и входящих в них моделей
BACKUP_SECTIONS = {
    "catalog": {
        "title": "Каталог продукции и акции",
        "description": "Категории, товары, акции, промокоды и отзывы покупателей",
        "models": [
            "shop.Category",
            "shop.Product",
            "shop.Promotion",
            "shop.PromoCode",
            "shop.Review",
        ],
        "media_folders": ["products", "categories"],
    },
    "orders": {
        "title": "Заказы покупателей",
        "description": "Все заказы (физ. и юр. лица) и детальные позиции заказов",
        "models": [
            "shop.Order",
            "shop.OrderItem",
        ],
        "media_folders": [],
    },
    "users": {
        "title": "Клиенты и пользователи",
        "description": "Зарегистрированные клиенты, профили физ./юр. лиц с реквизитами, заявки на прайс и звонки",
        "models": [
            "auth.Group",
            "auth.User",
            "accounts.UserProfile",
            "main.CallbackRequest",
            "main.WholesalePriceRequest",
        ],
        "media_folders": [],
    },
    "articles": {
        "title": "Статьи и публикации блога",
        "description": "Статьи о сыроделии, рецепты и советы экспертов",
        "models": [
            "articles.Article",
        ],
        "media_folders": ["articles"],
    },
    "settings": {
        "title": "Настройки сайта и страницы",
        "description": "Глобальные настройки брендинга, SEO, контакты, способы доставки, сертификаты, FAQ",
        "models": [
            "main.SiteSettings",
            "main.ProductionFeature",
            "main.CompanyTimeline",
            "main.QualityCertificate",
            "main.DeliveryMethod",
            "main.PaymentMethod",
            "main.DeliveryFaq",
            "main.ContactDepartment",
            "main.FaqCategory",
            "main.FaqItem",
            "main.SocialLink",
            "main.Page",
        ],
        "media_folders": ["branding", "social_icons", "certificates"],
    },
}

# Строгий порядок восстановления моделей (для соблюдения Foreign Key зависимостей)
MODEL_RESTORE_ORDER = [
    # 1. Базовые сущности пользователей
    "auth.Group",
    "auth.User",
    "accounts.UserProfile",
    # 2. Настройки и статические элементы
    "main.SiteSettings",
    "main.ProductionFeature",
    "main.CompanyTimeline",
    "main.QualityCertificate",
    "main.DeliveryMethod",
    "main.PaymentMethod",
    "main.DeliveryFaq",
    "main.ContactDepartment",
    "main.FaqCategory",
    "main.FaqItem",
    "main.SocialLink",
    "main.Page",
    # 3. Лиды и заявки
    "main.CallbackRequest",
    "main.WholesalePriceRequest",
    # 4. Каталог товаров
    "shop.Category",
    "shop.Product",
    "shop.Promotion",
    "shop.PromoCode",
    # 5. Заказы
    "shop.Order",
    "shop.OrderItem",
    # 6. Отзывы к товарам
    "shop.Review",
    # 7. Статьи
    "articles.Article",
]


def get_backup_dir() -> Path:
    """Возвращает директорию для хранения резервных копий."""
    backup_dir = getattr(settings, "BACKUP_DIR", settings.BASE_DIR / "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return Path(backup_dir)


def get_system_stats() -> Dict[str, Any]:
    """Возвращает оперативную статистику по объектам базы данных и медиафайлам."""
    stats = {}
    try:
        from shop.models import Category, Product, Order, OrderItem, Review, Promotion
        from articles.models import Article
        from accounts.models import UserProfile
        from main.models import SiteSettings, CallbackRequest, WholesalePriceRequest

        User = get_user_model()

        stats["categories_count"] = Category.objects.count()
        stats["products_count"] = Product.objects.count()
        stats["promotions_count"] = Promotion.objects.count()
        stats["reviews_count"] = Review.objects.count()

        stats["orders_count"] = Order.objects.count()
        stats["order_items_count"] = OrderItem.objects.count()

        stats["users_count"] = User.objects.count()
        stats["profiles_count"] = UserProfile.objects.count()
        stats["legal_profiles_count"] = UserProfile.objects.filter(
            customer_type="legal"
        ).count()
        stats["callbacks_count"] = CallbackRequest.objects.count()
        stats["wholesale_requests_count"] = WholesalePriceRequest.objects.count()

        stats["articles_count"] = Article.objects.count()
        stats["site_settings_configured"] = SiteSettings.objects.exists()
    except Exception as e:
        logger.warning(f"Ошибка при получении статистики моделей: {e}")

    # Статистика по медиафайлам
    media_root = Path(settings.MEDIA_ROOT)
    media_count = 0
    media_bytes = 0
    if media_root.exists():
        for root, _, files in os.walk(media_root):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    media_bytes += os.path.getsize(fp)
                    media_count += 1
                except OSError:
                    pass

    stats["media_files_count"] = media_count
    stats["media_total_bytes"] = media_bytes
    stats["media_total_mb"] = round(media_bytes / (1024 * 1024), 2)
    return stats


def _serialize_model_queryset(model_str: str) -> Tuple[List[Dict[str, Any]], int]:
    """Сериализует объекты указанной модели в список словарей Django JSON."""
    try:
        model = apps.get_model(model_str)
    except LookupError:
        logger.warning(f"Модель {model_str} не найдена в установленных приложениях")
        return [], 0

    qs = model.objects.all().order_by("pk")
    count = qs.count()
    if count == 0:
        return [], 0

    data_json = serializers.serialize(
        "json",
        qs,
        indent=None,
        use_natural_foreign_keys=False,
        use_natural_primary_keys=False,
    )
    return json.loads(data_json), count


def create_backup(
    sections: Optional[List[str]] = None,
    include_media: bool = True,
    output_path: Optional[str] = None,
    description: str = "",
) -> Dict[str, Any]:
    """
    Создает архив резервной копии (.zip).

    :param sections: список секций ('catalog', 'orders', 'users', 'articles', 'settings') или None для всех.
    :param include_media: включать ли медиафайлы картинок в архив.
    :param output_path: путь к результирующему .zip файлу. Если не задан, создается в BACKUP_DIR.
    :param description: пояснительное описание архива.
    :return: словарь с результатами и метаданными резервной копии.
    """
    available_section_keys = list(BACKUP_SECTIONS.keys())
    if not sections or "all" in sections:
        chosen_sections = available_section_keys
    else:
        chosen_sections = [s for s in sections if s in available_section_keys]
        if not chosen_sections:
            raise ValueError(
                f"Не выбрана ни одна валидная секция. Доступно: {available_section_keys}"
            )

    timestamp_str = timezone.now().strftime("%Y%m%d_%H%M%S")
    sections_slug = (
        "all"
        if len(chosen_sections) == len(available_section_keys)
        else "-".join(chosen_sections)
    )

    if not output_path:
        filename = f"backup_sibsir_{sections_slug}_{timestamp_str}.zip"
        output_file_path = get_backup_dir() / filename
    else:
        output_file_path = Path(output_path)
        os.makedirs(output_file_path.parent, exist_ok=True)

    # 1. Собираем сериализованные данные по секциям
    all_objects = []
    models_count = {}
    section_stats = {}
    included_media_folders = set()

    for sec_key in chosen_sections:
        sec_cfg = BACKUP_SECTIONS[sec_key]
        sec_total_objects = 0
        if include_media and sec_cfg["media_folders"]:
            included_media_folders.update(sec_cfg["media_folders"])

        for model_str in sec_cfg["models"]:
            records, cnt = _serialize_model_queryset(model_str)
            models_count[model_str] = cnt
            sec_total_objects += cnt
            if records:
                all_objects.extend(records)

        section_stats[sec_key] = sec_total_objects

    # 2. Формируем манифест архива
    media_root = Path(settings.MEDIA_ROOT)
    media_files_to_pack: List[Tuple[Path, str]] = []
    media_total_bytes = 0

    if include_media and media_root.exists():
        # Если бэкап полный, забираем все папки медиа, иначе только целевые папки
        is_all_sections = len(chosen_sections) == len(available_section_keys)
        for root, _, files in os.walk(media_root):
            rel_dir = os.path.relpath(root, media_root)
            first_part = rel_dir.split(os.sep)[0] if rel_dir != "." else ""

            # Проверяем, нужно ли включать эту папку
            if (
                not is_all_sections
                and first_part
                and first_part not in included_media_folders
            ):
                continue

            for f in files:
                abs_fp = Path(root) / f
                # Относительный путь внутри media
                rel_media_path = os.path.relpath(abs_fp, media_root)
                archive_name = f"media/{rel_media_path.replace(os.sep, '/')}"
                try:
                    fsize = abs_fp.stat().st_size
                    media_total_bytes += fsize
                    media_files_to_pack.append((abs_fp, archive_name))
                except OSError:
                    pass

    manifest = {
        "version": "1.0",
        "created_at": timezone.now().isoformat(),
        "created_timestamp": timestamp_str,
        "django_version": getattr(settings, "DJANGO_VERSION", "5.2"),
        "description": description or f"Резервная копия ТМ «Сибсыр» ({sections_slug})",
        "sections": chosen_sections,
        "include_media": include_media,
        "total_db_records": len(all_objects),
        "models_count": models_count,
        "section_stats": section_stats,
        "media_files_count": len(media_files_to_pack),
        "media_total_bytes": media_total_bytes,
        "media_total_mb": round(media_total_bytes / (1024 * 1024), 2),
    }

    # 3. Записываем в Zip-архив с компрессией Deflate
    with zipfile.ZipFile(
        output_file_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as zip_out:
        # Записываем manifest.json
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode(
            "utf-8"
        )
        zip_out.writestr("manifest.json", manifest_bytes)

        # Записываем общий data.json (все объекты в правильном формате фикстуры)
        data_bytes = json.dumps(all_objects, ensure_ascii=False, indent=2).encode(
            "utf-8"
        )
        zip_out.writestr("data/all_data.json", data_bytes)

        # Записываем отдельные json для каждой секции для гибкости
        for sec_key in chosen_sections:
            sec_models = set(m.lower() for m in BACKUP_SECTIONS[sec_key]["models"])
            sec_objects = [
                obj
                for obj in all_objects
                if str(obj.get("model", "")).lower() in sec_models
            ]
            sec_bytes = json.dumps(sec_objects, ensure_ascii=False, indent=2).encode(
                "utf-8"
            )
            zip_out.writestr(f"data/{sec_key}.json", sec_bytes)

        # Добавляем медиафайлы
        for abs_fp, arc_name in media_files_to_pack:
            try:
                zip_out.write(abs_fp, arc_name)
            except Exception as e:
                logger.warning(f"Не удалось запаковать файл {abs_fp}: {e}")

    archive_size = output_file_path.stat().st_size
    manifest["archive_size_bytes"] = archive_size
    manifest["archive_size_mb"] = round(archive_size / (1024 * 1024), 2)
    manifest["archive_path"] = str(output_file_path)
    manifest["archive_filename"] = output_file_path.name

    logger.info(
        f"Резервная копия успешно создана: {output_file_path.name} "
        f"({manifest['archive_size_mb']} MB, {manifest['total_db_records']} записей, {manifest['media_files_count']} картинок)"
    )
    return manifest


def get_backup_manifest(archive_path: Path) -> Dict[str, Any]:
    """Извлекает и возвращает манифест из архива резервной копии."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Файл архива не найден: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zip_in:
        try:
            manifest_info = zip_in.getinfo("manifest.json")
            with zip_in.open(manifest_info) as f:
                data = json.loads(f.read().decode("utf-8"))
                data["archive_size_bytes"] = archive_path.stat().st_size
                data["archive_size_mb"] = round(
                    archive_path.stat().st_size / (1024 * 1024), 2
                )
                return data
        except KeyError:
            # Если архив без manifest.json (например, сторонний zip с json)
            files = zip_in.namelist()
            return {
                "version": "legacy",
                "created_at": datetime.fromtimestamp(
                    archive_path.stat().st_mtime
                ).isoformat(),
                "description": archive_path.name,
                "sections": ["unknown"],
                "include_media": any(f.startswith("media/") for f in files),
                "total_db_records": 0,
                "models_count": {},
                "media_files_count": len(
                    [f for f in files if f.startswith("media/") and not f.endswith("/")]
                ),
                "archive_size_bytes": archive_path.stat().st_size,
                "archive_size_mb": round(
                    archive_path.stat().st_size / (1024 * 1024), 2
                ),
            }


def list_existing_backups() -> List[Dict[str, Any]]:
    """Возвращает список всех существующих резервных копий в директории бэкапов."""
    backup_dir = get_backup_dir()
    results = []

    for file_name in sorted(os.listdir(backup_dir), reverse=True):
        if file_name.endswith(".zip"):
            file_path = backup_dir / file_name
            try:
                manifest = get_backup_manifest(file_path)
                manifest["filename"] = file_name
                manifest["filepath"] = str(file_path)
                manifest["archive_size_bytes"] = file_path.stat().st_size
                manifest["archive_size_mb"] = round(
                    file_path.stat().st_size / (1024 * 1024), 2
                )
                manifest["mtime"] = datetime.fromtimestamp(file_path.stat().st_mtime)
                results.append(manifest)
            except Exception as e:
                logger.warning(f"Ошибка чтения бэкапа {file_name}: {e}")
                results.append(
                    {
                        "filename": file_name,
                        "filepath": str(file_path),
                        "error": str(e),
                        "archive_size_mb": round(
                            file_path.stat().st_size / (1024 * 1024), 2
                        ),
                        "mtime": datetime.fromtimestamp(file_path.stat().st_mtime),
                    }
                )
    return results


def _clean_tables_for_models(
    models_to_clean: List[str], preserve_superusers: bool = True
):
    """
    Очищает таблицы указанных моделей в обратном топологическом порядке
    для предотвращения нарушений внешних ключей.
    """
    models_to_clean_lower = set(m.lower() for m in models_to_clean)
    ordered_to_clean = []
    # Обратный порядок от MODEL_RESTORE_ORDER
    for m_str in reversed(MODEL_RESTORE_ORDER):
        if m_str.lower() in models_to_clean_lower:
            ordered_to_clean.append(m_str)

    User = get_user_model()
    superuser_ids = (
        list(User.objects.filter(is_superuser=True).values_list("id", flat=True))
        if preserve_superusers
        else []
    )

    for m_str in ordered_to_clean:
        m_lower = m_str.lower()
        try:
            model = apps.get_model(m_str)
            if m_lower == "auth.user" and preserve_superusers and superuser_ids:
                model.objects.exclude(id__in=superuser_ids).delete()
            elif (
                m_lower == "accounts.userprofile"
                and preserve_superusers
                and superuser_ids
            ):
                model.objects.exclude(user_id__in=superuser_ids).delete()
            else:
                model.objects.all().delete()
        except LookupError:
            continue
        except Exception as e:
            logger.warning(f"Ошибка при очистке модели {m_str}: {e}")


def _reset_db_sequences(models_to_reset: List[str]):
    """Сбрасывает последовательности автоинкремента в СУБД (PostgreSQL / SQLite)."""
    if connection.vendor == "postgresql":
        try:
            model_classes = []
            for m_str in models_to_reset:
                try:
                    model_classes.append(apps.get_model(m_str))
                except LookupError:
                    pass
            statements = connection.ops.sequence_reset_sql(color_style(), model_classes)
            if statements:
                with connection.cursor() as cursor:
                    for sql in statements:
                        cursor.execute(sql)
        except Exception as e:
            logger.warning(f"Не удалось выполнить sequence_reset_sql: {e}")


def restore_backup(
    archive_path_or_file: Any,
    sections: Optional[List[str]] = None,
    clear_tables: bool = False,
    restore_media: bool = True,
    preserve_superusers: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Восстанавливает данные и медиафайлы из архива резервной копии.

    :param archive_path_or_file: путь к .zip файлу или файловый объект (UploadedFile).
    :param sections: секции для восстановления ('catalog', 'orders', 'users', 'articles', 'settings') или None для всех.
    :param clear_tables: очищать ли таблицы перед импортом.
    :param restore_media: восстанавливать ли картинки в MEDIA_ROOT.
    :param preserve_superusers: сохранять ли текущих администраторов при очистке таблиц.
    :param dry_run: режим проверки без сохранения изменений в БД.
    :return: словарь с результатами восстановления.
    """
    is_temp_file = False
    if isinstance(archive_path_or_file, (str, Path)):
        zip_path = Path(archive_path_or_file)
        if not zip_path.exists():
            raise FileNotFoundError(f"Файл резервной копии не найден: {zip_path}")
    else:
        # File-like object (например, загруженный через веб-форму)
        temp_fd, temp_name = tempfile.mkstemp(suffix=".zip")
        os.close(temp_fd)
        with open(temp_name, "wb") as f_out:
            for chunk in (
                archive_path_or_file.chunks()
                if hasattr(archive_path_or_file, "chunks")
                else [archive_path_or_file.read()]
            ):
                f_out.write(chunk)
        zip_path = Path(temp_name)
        is_temp_file = True

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_in:
            namelist = zip_in.namelist()

            # Читаем манифест (если есть)
            manifest = {}
            if "manifest.json" in namelist:
                with zip_in.open("manifest.json") as f:
                    manifest = json.loads(f.read().decode("utf-8"))

            available_sections = list(BACKUP_SECTIONS.keys())
            if not sections or "all" in sections:
                chosen_sections = available_sections
            else:
                chosen_sections = [s for s in sections if s in available_sections]

            # Собираем список разрешенных моделей для импорта (в нижнем регистре)
            allowed_models = set()
            allowed_media_folders = set()
            for sec_k in chosen_sections:
                allowed_models.update(
                    m.lower() for m in BACKUP_SECTIONS[sec_k]["models"]
                )
                if BACKUP_SECTIONS[sec_k]["media_folders"]:
                    allowed_media_folders.update(
                        BACKUP_SECTIONS[sec_k]["media_folders"]
                    )

            # Читаем объекты данных из архива
            raw_objects = []
            if "data/all_data.json" in namelist:
                with zip_in.open("data/all_data.json") as f:
                    raw_objects = json.loads(f.read().decode("utf-8"))
            else:
                # Пробуем по секциям data/<section>.json
                for item in namelist:
                    if item.startswith("data/") and item.endswith(".json"):
                        with zip_in.open(item) as f:
                            raw_objects.extend(json.loads(f.read().decode("utf-8")))

            # Фильтруем объекты по разрешенным моделям (lower-case)
            filtered_objects = [
                obj
                for obj in raw_objects
                if str(obj.get("model", "")).lower() in allowed_models
            ]

            # Группируем объекты по моделям (в lower-case)
            objects_by_model: Dict[str, List[Dict[str, Any]]] = {}
            for obj in filtered_objects:
                m_str = str(obj.get("model", "")).lower()
                if m_str:
                    objects_by_model.setdefault(m_str, []).append(obj)

            # Проверяем сухие цифры для dry_run
            summary_stats = {
                "archive_manifest": manifest,
                "chosen_sections": chosen_sections,
                "clear_tables": clear_tables,
                "restore_media": restore_media,
                "total_records_in_backup": len(filtered_objects),
                "records_by_model": {
                    m: len(objs) for m, objs in objects_by_model.items()
                },
                "dry_run": dry_run,
            }

            if dry_run:
                media_count = len(
                    [
                        f
                        for f in namelist
                        if f.startswith("media/") and not f.endswith("/")
                    ]
                )
                summary_stats["media_files_found"] = media_count
                return summary_stats

            # Выполняем восстановление в транзакции БД
            restored_counts = {}
            with transaction.atomic():
                if clear_tables:
                    _clean_tables_for_models(
                        list(allowed_models), preserve_superusers=preserve_superusers
                    )

                # Восстанавливаем модели строго в топологическом порядке MODEL_RESTORE_ORDER
                for m_str in MODEL_RESTORE_ORDER:
                    m_key = m_str.lower()
                    if m_key not in objects_by_model:
                        continue
                    model_records = objects_by_model[m_key]
                    if not model_records:
                        continue

                    # Сериализуем эту пачку обратно в JSON строку для стандартного Django deserializer
                    chunk_json = json.dumps(model_records)
                    deserialized_objects = serializers.deserialize(
                        "json",
                        chunk_json,
                        ignorenonexistent=True,
                        handle_forward_references=True,
                    )

                    saved_count = 0
                    for deserialized_obj in deserialized_objects:
                        try:
                            # Метод DeserializedObject.save() в Django по умолчанию сам вызывает save_base(raw=True)
                            deserialized_obj.save()
                            saved_count += 1
                        except Exception as e:
                            logger.error(
                                f"Ошибка сохранения объекта {m_str} pk={getattr(deserialized_obj.object, 'pk', None)}: {e}"
                            )

                    restored_counts[m_str] = saved_count

                # Сбрасываем автоинкременты
                _reset_db_sequences(list(objects_by_model.keys()))

            # Распаковка медиафайлов
            restored_media_count = 0
            restored_media_bytes = 0
            if restore_media:
                media_root = Path(settings.MEDIA_ROOT)
                os.makedirs(media_root, exist_ok=True)
                is_all_sections = len(chosen_sections) == len(available_sections)

                for member in namelist:
                    if not member.startswith("media/") or member.endswith("/"):
                        continue

                    rel_path = member[len("media/") :]
                    first_part = rel_path.split("/")[0]

                    if (
                        not is_all_sections
                        and first_part
                        and first_part not in allowed_media_folders
                    ):
                        continue

                    # Безопасная распаковка без Path Traversal
                    target_file = (media_root / rel_path).resolve()
                    if not str(target_file).startswith(str(media_root.resolve())):
                        logger.warning(
                            f"Предотвращена попытка Path Traversal: {member}"
                        )
                        continue

                    os.makedirs(target_file.parent, exist_ok=True)
                    with zip_in.open(member) as source, open(
                        target_file, "wb"
                    ) as target:
                        shutil.copyfileobj(source, target)
                        restored_media_count += 1
                        restored_media_bytes += target_file.stat().st_size

            summary_stats["restored_counts"] = restored_counts
            summary_stats["restored_total_records"] = sum(restored_counts.values())
            summary_stats["restored_media_count"] = restored_media_count
            summary_stats["restored_media_mb"] = round(
                restored_media_bytes / (1024 * 1024), 2
            )
            summary_stats["success"] = True

            logger.info(
                f"Восстановление успешно завершено: {summary_stats['restored_total_records']} записей, "
                f"{restored_media_count} медиафайлов"
            )
            return summary_stats

    finally:
        if is_temp_file and zip_path.exists():
            try:
                os.remove(zip_path)
            except OSError:
                pass
