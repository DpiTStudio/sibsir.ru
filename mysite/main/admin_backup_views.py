import os
from pathlib import Path
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .backup_manager import (
    create_backup,
    restore_backup,
    list_existing_backups,
    get_system_stats,
    get_backup_dir,
    get_backup_manifest,
    BACKUP_SECTIONS,
)


def _check_superuser_permission(request):
    """Проверяет права суперпользователя для критических операций с бэкапами."""
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "Доступ к резервному копированию и восстановлению разрешен только суперпользователям.")
        return False
    return True


@staff_member_required
def admin_backup_dashboard(request):
    """Главная страница управления резервными копиями в админ-панели."""
    if not _check_superuser_permission(request):
        return redirect("admin:index")

    stats = get_system_stats()
    backups = list_existing_backups()

    context = {
        "title": "Резервное копирование и деплой",
        "system_stats": stats,
        "backups": backups,
        "sections": BACKUP_SECTIONS,
        "backup_dir": str(get_backup_dir()),
        "has_permission": True,
    }
    return render(request, "admin/main/backup_dashboard.html", context)


@staff_member_required
@require_POST
def admin_backup_create(request):
    """Создание резервной копии через админку."""
    if not _check_superuser_permission(request):
        return redirect("admin:index")

    sections = request.POST.getlist("sections")
    if not sections:
        sections = list(BACKUP_SECTIONS.keys())

    include_media = request.POST.get("include_media") == "1"
    description = request.POST.get("description", "").strip()
    download_immediately = request.POST.get("download_now") == "1"

    try:
        res = create_backup(
            sections=sections,
            include_media=include_media,
            description=description,
        )

        archive_path = Path(res["archive_path"])

        if download_immediately and archive_path.exists():
            return FileResponse(
                open(archive_path, "rb"),
                as_attachment=True,
                filename=res["archive_filename"],
            )

        messages.success(
            request,
            f"Резервная копия «{res['archive_filename']}» успешно создана! "
            f"Размер: {res['archive_size_mb']} MB, записей в БД: {res['total_db_records']}, "
            f"медиафайлов: {res['media_files_count']} ({res['media_total_mb']} MB)."
        )
    except Exception as e:
        messages.error(request, f"Ошибка при создании резервной копии: {e}")

    return redirect("main:admin_backup_dashboard")


@staff_member_required
def admin_backup_download(request, filename):
    """Скачивание архива резервной копии."""
    if not _check_superuser_permission(request):
        return redirect("admin:index")

    # Защита от Path Traversal
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".zip"):
        raise Http404("Недопустимый формат файла")

    file_path = get_backup_dir() / safe_filename
    if not file_path.exists():
        raise Http404("Файл резервной копии не найден")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=safe_filename,
    )


@staff_member_required
@require_POST
def admin_backup_restore(request):
    """Восстановление данных и картинок из архива."""
    if not _check_superuser_permission(request):
        return redirect("admin:index")

    server_filename = request.POST.get("server_filename", "").strip()
    uploaded_file = request.FILES.get("backup_file")
    clear_tables = request.POST.get("clear_tables") == "1"
    restore_media = request.POST.get("restore_media") == "1"
    sections = request.POST.getlist("sections") or None

    target_source = None
    source_name = ""

    if uploaded_file:
        target_source = uploaded_file
        source_name = uploaded_file.name
    elif server_filename:
        safe_filename = os.path.basename(server_filename)
        fp = get_backup_dir() / safe_filename
        if not fp.exists():
            messages.error(request, f"Выбранный файл архива не найден на сервере: {safe_filename}")
            return redirect("main:admin_backup_dashboard")
        target_source = fp
        source_name = safe_filename
    else:
        messages.error(request, "Не указан источник для восстановления: выберите файл на сервере или загрузите архив.")
        return redirect("main:admin_backup_dashboard")

    try:
        res = restore_backup(
            archive_path_or_file=target_source,
            sections=sections,
            clear_tables=clear_tables,
            restore_media=restore_media,
            preserve_superusers=True,
            dry_run=False,
        )

        messages.success(
            request,
            f"Восстановление из «{source_name}» успешно завершено! "
            f"Восстановлено объектов БД: {res['restored_total_records']}, "
            f"картинок: {res['restored_media_count']} ({res['restored_media_mb']} MB)."
        )
    except Exception as e:
        messages.error(request, f"Ошибка при восстановлении данных из {source_name}: {e}")

    return redirect("main:admin_backup_dashboard")


@staff_member_required
@require_POST
def admin_backup_delete(request, filename):
    """Удаление старой резервной копии."""
    if not _check_superuser_permission(request):
        return redirect("admin:index")

    safe_filename = os.path.basename(filename)
    file_path = get_backup_dir() / safe_filename

    if file_path.exists() and safe_filename.endswith(".zip"):
        try:
            file_path.unlink()
            messages.success(request, f"Резервная копия «{safe_filename}» удалена.")
        except Exception as e:
            messages.error(request, f"Не удалось удалить файл: {e}")
    else:
        messages.error(request, "Файл не найден.")

    return redirect("main:admin_backup_dashboard")

