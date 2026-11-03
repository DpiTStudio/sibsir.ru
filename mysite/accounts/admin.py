from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from shop.price_list_generator import (
    generate_wholesale_price_list_xlsx,
    send_wholesale_price_list_email,
)
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль покупателя / Реквизиты организации"
    fk_name = "user"
    fieldsets = (
        ("Тип клиента и контакты", {
            "fields": ("customer_type", "phone", "delivery_address")
        }),
        ("Реквизиты юридического лица / ИП (если применимо)", {
            "fields": (
                "company_name", 
                "inn", 
                "kpp", 
                "ogrn", 
                "legal_address",
                "bank_name",
                "bik",
                "account_number",
                "corr_account",
                "contact_person"
            ),
            "classes": ("collapse",)
        }),
    )


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username", 
        "email", 
        "first_name", 
        "last_name", 
        "get_customer_type", 
        "get_company", 
        "get_orders_count",
        "is_staff"
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "profile__customer_type")

    @admin.display(description="Тип клиента")
    def get_customer_type(self, obj):
        if hasattr(obj, "profile"):
            return "Юр. лицо / ИП" if obj.profile.is_legal else "Физ. лицо"
        return "—"

    @admin.display(description="Компания / Организация")
    def get_company(self, obj):
        if hasattr(obj, "profile") and obj.profile.company_name:
            return obj.profile.company_name
        return "—"

    @admin.display(description="Заказов")
    def get_orders_count(self, obj):
        cnt = obj.orders.count()
        if cnt > 0:
            url = reverse("admin:shop_order_changelist") + f"?user__id__exact={obj.id}"
            return format_html('<a href="{}" style="font-weight: bold; color: #2563eb;">{} зак.</a>', url, cnt)
        return "0"


# Перерегистрируем User с инлайном профиля
try:
    admin.site.unregister(User)
except Exception:
    pass
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "customer_type_badge",
        "company_name",
        "inn",
        "phone",
        "get_orders_badge",
        "price_list_send_btn",
        "created_at"
    )
    list_filter = ("customer_type", "created_at")
    search_fields = ("user__username", "user__email", "company_name", "inn", "phone", "contact_person")
    readonly_fields = ("created_at", "updated_at", "orders_summary", "wholesale_price_tools")

    fieldsets = (
        ("Основная информация", {
            "fields": ("user", "customer_type", "phone", "delivery_address")
        }),
        ("Реквизиты организации / ИП", {
            "fields": (
                "company_name",
                "inn",
                "kpp",
                "ogrn",
                "legal_address",
                "bank_name",
                "bik",
                "account_number",
                "corr_account",
                "contact_person"
            )
        }),
        ("Оптовый прайс-лист и коммерческое предложение", {
            "fields": ("wholesale_price_tools",),
        }),
        ("Статистика и история", {
            "fields": ("orders_summary", "created_at", "updated_at")
        }),
    )

    actions = ["send_price_list_selected", "send_price_list_all_wholesale"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:profile_id>/send-price-list/",
                self.admin_site.admin_view(self.send_price_list_view),
                name="accounts_userprofile_send_price_list",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Оптовый прайс")
    def price_list_send_btn(self, obj):
        send_url = reverse("admin:accounts_userprofile_send_price_list", args=[obj.id])
        email = obj.user.email if obj.user else ""
        if not email:
            return mark_safe('<span style="color: #94a3b8; font-size: 11px;">Нет email</span>')
        return format_html(
            '<a href="{}" class="sib-btn-action primary" style="padding: 3px 8px; font-size: 11px; white-space: nowrap;" onclick="return confirm(\'Сгенерировать и отправить актуальный оптовый прайс-лист на {}?\');">'
            '<i class="bi bi-file-earmark-spreadsheet"></i> Отправить'
            '</a>',
            send_url, email
        )

    @admin.display(description="Инструменты отправки прайс-листа")
    def wholesale_price_tools(self, obj):
        send_url = reverse("admin:accounts_userprofile_send_price_list", args=[obj.id])
        download_url = reverse("admin:main_wholesalepricerequest_download")
        email = obj.user.email if obj.user else ""
        return format_html(
            '<div style="background: rgba(255, 132, 0, 0.08); border: 1px solid rgba(255, 132, 0, 0.2); padding: 14px 18px; border-radius: 8px;">'
            '<p style="margin: 0 0 10px 0; font-size: 13px;">Получатель: <strong>{}</strong> &lt;<strong>{}</strong>&gt;</p>'
            '<div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">'
            '<a href="{}" class="sib-btn-action primary" style="padding: 6px 14px; font-size: 12px; font-weight: 700;" onclick="return confirm(\'Сгенерировать и отправить оптовый прайс на {}\');">'
            '<i class="bi bi-send-fill"></i> Отправить прайс-лист на Email клиента'
            '</a>'
            '<a href="{}" target="_blank" class="sib-btn-action" style="padding: 6px 14px; font-size: 12px;">'
            '<i class="bi bi-download"></i> Скачать файл прайса (.xlsx)'
            '</a>'
            '</div>'
            '</div>',
            obj.display_name, email or "не указан", send_url, email or "клиента", download_url
        )

    @admin.action(description="📧 Сгенерировать и отправить прайс-лист выбранным клиентам")
    def send_price_list_selected(self, request, queryset):
        cached_xlsx = generate_wholesale_price_list_xlsx()
        sent_count = 0
        skipped = 0

        for profile in queryset:
            email = profile.user.email if profile.user else ""
            if not email:
                skipped += 1
                continue
            res = send_wholesale_price_list_email(
                recipient_email=email,
                recipient_name=profile.display_name,
                company_name=profile.company_name,
                user_profile=profile,
                admin_user=request.user,
                cached_xlsx_data=cached_xlsx,
            )
            if res.get("success"):
                sent_count += 1

        msg = f"Успешно отправлено прайс-листов клиентам: {sent_count}."
        if skipped:
            msg += f" Пропущено (нет email в учетной записи): {skipped}."
        self.message_user(request, msg, level=messages.SUCCESS)

    @admin.action(description="🚀 Отправить актуальный прайс-лист ВСЕМ оптовым клиентам (Юр. лицам / ИП)")
    def send_price_list_all_wholesale(self, request, queryset):
        legal_qs = UserProfile.objects.filter(customer_type="legal").select_related("user")
        cached_xlsx = generate_wholesale_price_list_xlsx()
        sent_count = 0
        skipped = 0

        for profile in legal_qs:
            email = profile.user.email if profile.user else ""
            if not email:
                skipped += 1
                continue
            res = send_wholesale_price_list_email(
                recipient_email=email,
                recipient_name=profile.display_name,
                company_name=profile.company_name,
                user_profile=profile,
                admin_user=request.user,
                cached_xlsx_data=cached_xlsx,
            )
            if res.get("success"):
                sent_count += 1

        msg = f"Всего оптовых клиентов: {legal_qs.count()}. Успешно отправлено прайс-листов: {sent_count}."
        if skipped:
            msg += f" Без email: {skipped}."
        self.message_user(request, msg, level=messages.SUCCESS)

    def send_price_list_view(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            self.message_user(request, "Профиль не найден.", level=messages.ERROR)
            return redirect("admin:accounts_userprofile_changelist")

        email = profile.user.email if profile.user else ""
        if not email:
            self.message_user(
                request,
                f"У пользователя {profile.user.username} не указан E-mail в учетной записи.",
                level=messages.ERROR
            )
            return redirect("admin:accounts_userprofile_change", profile.id)

        res = send_wholesale_price_list_email(
            recipient_email=email,
            recipient_name=profile.display_name,
            company_name=profile.company_name,
            user_profile=profile,
            admin_user=request.user,
        )

        if res.get("success"):
            notice = " (отправка зафиксирована)" if res.get("simulated") else ""
            self.message_user(
                request,
                f"✅ Оптовый прайс-лист сформирован и успешно отправлен клиенту {profile.display_name} ({email}){notice}.",
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f"Ошибка отправки прайс-листа на {email}: {res.get('error')}",
                level=messages.ERROR
            )

        referer = request.META.get("HTTP_REFERER")
        if referer and ("change" in referer or "userprofile" in referer):
            return HttpResponseRedirect(referer)
        return redirect("admin:accounts_userprofile_changelist")

    @admin.display(description="Пользователь")
    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user_id])
        return format_html('<a href="{}" style="font-weight: 600;">{} ({})</a>', url, obj.user.username, obj.user.email)

    @admin.display(description="Тип")
    def customer_type_badge(self, obj):
        if obj.is_legal:
            return mark_safe('<span style="background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px;">ЮР. ЛИЦО</span>')
        return mark_safe('<span style="background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px;">ФИЗ. ЛИЦО</span>')

    @admin.display(description="Заказы")
    def get_orders_badge(self, obj):
        cnt = obj.get_orders_count()
        spent = obj.get_total_spent()
        url = reverse("admin:shop_order_changelist") + f"?user__id__exact={obj.user_id}"
        return format_html(
            '<a href="{}" style="text-decoration: none;"><span style="font-weight: bold; color: #059669;">{} шт.</span> <span style="color: #64748b; font-size: 11px;">({} ₽)</span></a>',
            url, cnt, spent
        )

    @admin.display(description="Сводка заказов")
    def orders_summary(self, obj):
        orders = obj.get_orders()[:10]
        if not orders:
            return "У данного пользователя пока нет заказов."
        
        html = '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
        html += '<tr style="border-bottom: 2px solid #e2e8f0; text-align: left;"><th style="padding: 6px;">№</th><th style="padding: 6px;">Дата</th><th style="padding: 6px;">Сумма</th><th style="padding: 6px;">Статус</th></tr>'
        for o in orders:
            url = reverse("admin:shop_order_change", args=[o.id])
            html += f'<tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px;"><a href="{url}" style="font-weight: bold;">Заказ #{o.id}</a></td><td style="padding: 6px;">{o.created_at.strftime("%d.%m.%Y %H:%M")}</td><td style="padding: 6px; font-weight: bold;">{o.total_price} ₽</td><td style="padding: 6px;">{o.get_status_display()}</td></tr>'
        html += '</table>'
        return mark_safe(html)
