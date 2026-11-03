import json
from django.db import models
from django.http import JsonResponse
from django.urls import path
from tinymce.widgets import TinyMCE


class DragDropReorderMixin:
    """
    Миксин для drag-and-drop переупорядочивания строк в таблице админки Django.
    Автоматически регистрирует эндпоинт 'reorder/' и обрабатывает сохранение нового порядка.
    """
    reorder_field = "order"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reorder/",
                self.admin_site.admin_view(self.reorder_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_reorder",
            ),
        ]
        return custom_urls + urls

    def reorder_view(self, request):
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
        if not self.has_change_permission(request):
            return JsonResponse({"status": "error", "message": "Недостаточно прав для изменения объектов"}, status=403)
        try:
            body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body
            data = json.loads(body)
            ordered_ids = [int(x) for x in data.get("ordered_ids", [])]
            if not ordered_ids:
                return JsonResponse({"status": "error", "message": "Список идентификаторов пуст"}, status=400)

            objs = list(self.model.objects.filter(pk__in=ordered_ids))
            if len(objs) != len(ordered_ids):
                return JsonResponse({"status": "error", "message": "Часть объектов не найдена в базе данных"}, status=404)

            # Получаем существующие значения сортировки для данных объектов
            current_orders = sorted([getattr(obj, self.reorder_field) for obj in objs])
            if len(set(current_orders)) == len(objs):
                assigned_orders = current_orders
            else:
                min_val = current_orders[0] if current_orders else 10
                assigned_orders = [min_val + i * 10 for i in range(len(objs))]

            obj_map = {obj.pk: obj for obj in objs}
            updates = []
            for obj_id, new_order in zip(ordered_ids, assigned_orders):
                obj = obj_map[obj_id]
                if getattr(obj, self.reorder_field) != new_order:
                    setattr(obj, self.reorder_field, new_order)
                    updates.append(obj)

            if updates:
                self.model.objects.bulk_update(updates, [self.reorder_field])

            return JsonResponse({
                "status": "success",
                "message": "Порядок строк успешно сохранен",
                "orders": {obj_id: ord_val for obj_id, ord_val in zip(ordered_ids, assigned_orders)}
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class RichTextAdminMixin:
    """
    Миксин для автоматического подключения визуального редактора TinyMCE к текстовым полям (TextField)
    в панели администратора.

    Можно указать список полей в атрибуте `rich_text_fields = ('content', 'description')`.
    Если `rich_text_fields` не указан или равен "__all__", то визуальный редактор применяется
    ко всем полям типа models.TextField данной модели.
    """
    rich_text_fields = None

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.TextField):
            apply_rich = False
            if self.rich_text_fields is None or self.rich_text_fields == "__all__":
                apply_rich = True
            elif isinstance(self.rich_text_fields, (list, tuple, set)) and db_field.name in self.rich_text_fields:
                apply_rich = True

            if apply_rich:
                kwargs["widget"] = TinyMCE(attrs={"cols": 80, "rows": 20})

        return super().formfield_for_dbfield(db_field, request, **kwargs)
