from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from .models import (
    SiteSettings, ProductionFeature, CallbackRequest,
    CompanyTimeline, QualityCertificate, DeliveryMethod,
    PaymentMethod, DeliveryFaq, ContactDepartment,
    FaqCategory, FaqItem, SocialLink, WholesalePriceRequest,
    Page
)
from shop.price_list_generator import (
    generate_wholesale_price_list_xlsx,
    generate_wholesale_price_list_html,
    send_wholesale_price_list_email,
)
from .admin_dashboard import patch_admin_site

from .forms import AdminCaptchaAuthenticationForm
from .admin_mixins import RichTextAdminMixin, DragDropReorderMixin

# Настройка заголовков панели администратора Django
admin.site.site_header = "ТМ «Сибсыр» — Панель управления"
admin.site.site_title = "Администрирование Сибсыр"
admin.site.index_title = "Управление магазином, каталогом и контентом"

# Подключение формы авторизации с защитой капчей
admin.site.login_form = AdminCaptchaAuthenticationForm

# Подключение аналитического дашборда на главной странице админки
patch_admin_site()



@admin.register(SiteSettings)
class SiteSettingsAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = (
        "about_text", "about_tech_text_1", "about_tech_text_2",
        "about_safety_text", "delivery_text", "delivery_cold_chain_text",
        "pickup_instructions_truck", "pickup_instructions_car"
    )
    change_form_template = "admin/main/sitesettings/change_form.html"
    list_display = ("brand_short_name", "logo_preview", "favicon_preview", "captcha_status_badge", "brand_name", "phone", "hero_image_preview")
    readonly_fields = ("logo_preview", "favicon_preview", "hero_image_preview")
    fieldsets = (
        ("Брендинг сайта (Логотип, Фавикон и Названия)", {
            "classes": ("tab-pane-branding", "sib-settings-card"),
            "description": "Загрузите официальный логотип, иконку сайта для вкладки браузера (фавикон) и укажите название бренда для отображения в шапке, подвале и документах.",
            "fields": (
                ("brand_short_name", "brand_name"),
                ("logo", "logo_preview"),
                ("favicon", "favicon_preview"),
            )
        }),
        ("Главный экран сайта (Hero-баннер)", {
            "classes": ("tab-pane-hero", "sib-settings-card"),
            "description": "Настройка первого экрана на главной странице витрины: промо-заголовок, краткий текст о сыроварне, бейдж и кнопка призыва к действию.",
            "fields": (
                "hero_title",
                "hero_subtitle",
                ("hero_badge_text", "cta_button_text"),
                ("hero_image", "hero_image_preview"),
            )
        }),
        ("Преимущества и стандарты фабрики", {
            "classes": ("tab-pane-hero", "sib-settings-card"),
            "description": "Заголовки секции преимуществ на главной странице сайта (сами преимущества настраиваются в разделе «Преимущества и особенности»).",
            "fields": (
                ("features_badge", "features_title"),
            )
        }),
        ("Каталог продукции (Заголовки и поиск)", {
            "classes": ("tab-pane-catalog", "sib-settings-card"),
            "description": "Управление оформлением шапки отдельной страницы каталога продукции, бейджем, описанием и плейсхолдером быстрого поиска.",
            "fields": (
                "catalog_badge_text",
                "catalog_title",
                "catalog_subtitle",
                ("catalog_search_placeholder", "catalog_banner_image"),
            )
        }),
        ("О компании (Тексты, статистика, технологии и фото)", {
            "classes": ("tab-pane-about", "sib-settings-card"),
            "description": "Полное управление текстами, статистическими показателями, технологиями и фото на отдельной странице «О компании».",
            "fields": (
                "about_hero_badge",
                "about_heading",
                "about_text",
                "about_image",
                ("about_stat_1_val", "about_stat_1_label"),
                ("about_stat_2_val", "about_stat_2_label"),
                ("about_stat_3_val", "about_stat_3_label"),
                ("about_stat_4_val", "about_stat_4_label"),
                "about_tech_heading",
                "about_tech_text_1",
                "about_tech_text_2",
                "about_safety_heading",
                "about_safety_text",
            )
        }),
        ("Доставка и логистика (Условия, холодовая цепь и прайс-лист)", {
            "classes": ("tab-pane-delivery", "sib-settings-card"),
            "description": "Информационные тексты об условиях перевозки спецтранспортом, сохранении холодовой цепи и файл оптового прайс-листа.",
            "fields": (
                "delivery_hero_badge",
                "delivery_hero_title",
                "delivery_text",
                "delivery_cold_chain_title",
                "delivery_cold_chain_text",
                ("delivery_cold_chain_image", "price_list_file"),
            )
        }),
        ("Оптовый прайс-лист и рассылка клиентам", {
            "classes": ("tab-pane-wholesale", "sib-settings-card"),
            "description": "Настройки темы и сопроводительного текста при автоматической генерации и отправке оптового прайс-листа клиентам.",
            "fields": (
                "wholesale_email_subject",
                "wholesale_email_body",
            )
        }),
        ("Контакты завода, карта и режим работы", {
            "classes": ("tab-pane-contacts", "sib-settings-card"),
            "description": "Контактные данные завода, график работы, координаты проезда и ссылки на карту Яндекс.",
            "fields": (
                "contacts_hero_badge",
                "contacts_hero_title",
                "contacts_hero_subtitle",
                ("phone", "email"),
                "address",
                ("working_hours", "inn_kpp"),
                ("pickup_coordinates", "yandex_map_iframe_url"),
                "pickup_instructions_truck",
                "pickup_instructions_car",
            )
        }),
        ("Юридические и банковские реквизиты продавца", {
            "classes": ("tab-pane-requisites", "sib-settings-card"),
            "description": "Официальные банковские и налоговые данные ИП/организации продавца. Они автоматически подставляются в счета на оплату, накладные ТОРГ-12 и акты приема-передачи.",
            "fields": (
                ("seller_inn", "seller_ogrn", "seller_okpo"),
                ("seller_bank", "seller_bik"),
                ("seller_account", "seller_corr_account"),
                ("seller_director", "seller_accountant"),
            )
        }),
        ("Отзывы покупателей (Заголовки и статистика)", {
            "classes": ("tab-pane-reviews", "sib-settings-card"),
            "description": "Оформление страницы отзывов и процент рекомендаций (сами отзывы модерируются в разделе «Отзывы клиентов»).",
            "fields": (
                "reviews_hero_badge",
                "reviews_hero_title",
                "reviews_hero_subtitle",
                "reviews_recommend_percent",
            )
        }),
        ("Защита от спама и ботов (Настройки капчи)", {
            "classes": ("tab-pane-security", "sib-settings-card"),
            "description": "Комплексная защита публичных форм сайта от автоматических спам-рассылок, парсеров и брутфорс-атак подбора паролей.",
            "fields": (
                ("captcha_enabled", "captcha_type"),
                ("captcha_on_register", "captcha_on_login"),
                ("captcha_on_admin_login", "captcha_on_guest_order"),
                ("captcha_on_callback",),
            )
        }),
        ("Поисковая оптимизация (SEO) и индексация сайта", {
            "classes": ("tab-pane-seo", "sib-settings-card"),
            "description": "Глобальные параметры поискового продвижения: базовый адрес сайта, шаблон заголовка Title, описания по умолчанию, Open Graph и управление индексацией.",
            "fields": (
                ("is_indexing_enabled", "site_base_url"),
                "seo_title_template",
                "seo_default_description",
                "seo_default_keywords",
                "seo_og_image",
            )
        }),
        ("SEO-теги ключевых разделов (Главная, Каталог, Категории, Статьи)", {
            "classes": ("tab-pane-seo", "sib-settings-card"),
            "description": "Индивидуальные мета-теги Title, Description и Keywords для коммерческих разделов сайта. При пустых значениях применяются автоматически сгенерированные теги.",
            "fields": (
                ("seo_home_title", "seo_home_keywords"),
                "seo_home_description",
                ("seo_catalog_title", "seo_catalog_keywords"),
                "seo_catalog_description",
                ("seo_categories_title", "seo_categories_keywords"),
                "seo_categories_description",
                ("seo_articles_title", "seo_articles_keywords"),
                "seo_articles_description",
            )
        }),
        ("SEO-теги инфо-страниц (О компании, Доставка, Контакты, Отзывы)", {
            "classes": ("tab-pane-seo", "sib-settings-card"),
            "description": "Поисковые мета-теги для служебных и доверительных разделов сайта фабрики.",
            "fields": (
                ("seo_about_title", "seo_about_keywords"),
                "seo_about_description",
                ("seo_delivery_title", "seo_delivery_keywords"),
                "seo_delivery_description",
                ("seo_contacts_title", "seo_contacts_keywords"),
                "seo_contacts_description",
                ("seo_reviews_title", "seo_reviews_keywords"),
                "seo_reviews_description",
                ("seo_faq_title", "seo_faq_keywords"),
                "seo_faq_description",
            )
        }),
        ("Вебмастер, Аналитика и Счетчики (Яндекс / Google)", {
            "classes": ("tab-pane-seo", "sib-settings-card"),
            "description": "Подтверждение прав владения сайтом в Яндекс.Вебмастере и Google Search Console, интеграция Яндекс.Метрики и вставка произвольных скриптов.",
            "fields": (
                ("yandex_verification_code", "google_verification_code"),
                "yandex_metrika_id",
                "custom_head_scripts",
                "custom_body_scripts",
            )
        }),
        ("Файл поисковых роботов (robots.txt) и карта сайта", {
            "classes": ("tab-pane-seo", "sib-settings-card"),
            "description": "Управление файлом robots.txt. Карта сайта sitemap.xml формируется динамически и автоматически включает все товары, категории, статьи и изображения.",
            "fields": (
                "robots_txt_content",
            )
        }),
    )

    def captcha_status_badge(self, obj):
        if not obj.captcha_enabled:
            return format_html(
                '<span style="background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 11px;">'
                '<i class="bi bi-x-circle me-1"></i>Отключена</span>'
            )
        items = []
        if obj.captcha_on_register: items.append("Регистрация")
        if obj.captcha_on_login: items.append("Вход")
        if obj.captcha_on_admin_login: items.append("Админка")
        if obj.captcha_on_callback: items.append("Заявки/Письма")
        if obj.captcha_on_guest_order: items.append("Заказ гостей")
        
        type_label = "Математика" if obj.captcha_type == "math" else "Картинка"
        details = ", ".join(items) if items else "Нигде"
        return format_html(
            '<div style="line-height: 1.3;">'
            '<span style="background: #dcfce7; color: #166534; padding: 3px 6px; border-radius: 4px; font-weight: 600; font-size: 11px;">'
            '✓ Активна ({})</span>'
            '<div style="font-size: 10px; color: #64748b; margin-top: 3px;">{}</div>'
            '</div>',
            type_label,
            details
        )
    captcha_status_badge.short_description = "Статус капчи"

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<div class="sib-brand-preview-wrap">'
                '<div class="sib-logo-trans-box">'
                '<img src="{}" alt="Логотип" class="sib-logo-img-tag" />'
                '</div>'
                '<div class="sib-preview-meta">'
                '<span class="sib-badge sib-badge-green"><i class="bi bi-check-circle-fill"></i> Загружен</span>'
                '<a href="{}" target="_blank" class="sib-preview-link"><i class="bi bi-eye"></i> Открыть</a>'
                '</div>'
                '</div>',
                obj.logo.url,
                obj.logo.url
            )
        return format_html(
            '<div class="sib-preview-empty">'
            '<div class="brand-icon-box" style="width: 38px; height: 38px; font-size: 1.1rem; border-radius: 8px;">'
            '<i class="bi bi-award-fill"></i>'
            '</div>'
            '<div>'
            '<div style="font-weight: 600; font-size: 12px; color: var(--admin-text-main);">Стандартная эмблема</div>'
            '<div style="font-size: 11px; color: var(--admin-text-muted);">Логотип не загружен</div>'
            '</div>'
            '</div>'
        )
    logo_preview.short_description = "Вид логотипа"

    def favicon_preview(self, obj):
        fav_url = obj.favicon.url if obj.favicon else "/static/images/favicon.svg"
        status_label = "Пользовательский фавикон" if obj.favicon else "Стандартный значок"
        return format_html(
            '<div class="sib-browser-tab-preview">'
            '<div class="sib-tab-frame">'
            '<img src="{}" class="sib-tab-fav-icon" alt="Favicon" />'
            '<span class="sib-tab-title-text">{} — Производство сыров</span>'
            '<span class="sib-tab-x">×</span>'
            '</div>'
            '<div class="sib-tab-status-note"><i class="bi bi-info-circle"></i> {}</div>'
            '</div>',
            fav_url,
            obj.brand_short_name or "Сибсыр",
            status_label
        )
    favicon_preview.short_description = "Вид фавикона во вкладке"

    def hero_image_preview(self, obj):
        img_url = obj.hero_image.url if obj.hero_image else "/static/images/hero_cheese.jpg"
        status_label = "Пользовательское фото" if obj.hero_image else "Стандартное фото каталога"
        return format_html(
            '<div class="sib-hero-preview-container">'
            '<div class="sib-hero-preview-box" style="background-image: url(\'{}\');">'
            '<div class="sib-hero-preview-shade">'
            '<span class="sib-hero-pill-badge">{}</span>'
            '<div class="sib-hero-title-mock">{}</div>'
            '</div>'
            '</div>'
            '<div class="sib-hero-status-note"><i class="bi bi-image"></i> {}</div>'
            '</div>',
            img_url,
            obj.hero_badge_text or "Собственное производство",
            obj.hero_title or "Здесь делают сыр",
            status_label
        )
    hero_image_preview.short_description = "Вид баннера на главной"

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        obj = self.model.get_solo()
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse("admin:main_sitesettings_change", args=[obj.pk]))


@admin.register(ProductionFeature)
class ProductionFeatureAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "subtitle", "badge", "icon", "is_active")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "badge")


@admin.register(CompanyTimeline)
class CompanyTimelineAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description",)
    list_display = ("order", "year", "title", "color_badge", "is_active")
    list_display_links = ("year", "title")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "color_class")
    search_fields = ("year", "title", "description")

    def color_badge(self, obj):
        colors = {
            "border-warning": ("#ff8400", "Желтый / Оранжевый (Сибсыр)"),
            "border-primary": ("#0284c7", "Синий"),
            "border-success": ("#10b981", "Зеленый"),
            "border-danger": ("#ef4444", "Красный"),
            "border-dark": ("#1e293b", "Темный"),
        }
        hex_val, label = colors.get(obj.color_class, ("#64748b", obj.color_class))
        return format_html(
            '<span style="background: {}; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            hex_val, label
        )
    color_badge.short_description = "Цвет карточки"


@admin.register(QualityCertificate)
class QualityCertificateAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "subtitle", "icon", "is_active")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description", "details")
    list_display = ("order", "title", "badge", "icon", "is_active")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description", "details", "badge")


@admin.register(PaymentMethod)
class PaymentMethodAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description", "details")
    list_display = ("order", "title", "note", "icon", "is_active")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description", "details", "note")


@admin.register(DeliveryFaq)
class DeliveryFaqAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("answer",)
    list_display = ("order", "question", "is_active")
    list_display_links = ("question",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")


@admin.register(ContactDepartment)
class ContactDepartmentAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description", "extra_info")
    list_display = ("order", "name", "phone", "email", "extra_info", "icon", "is_active")
    list_display_links = ("name",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "phone", "email", "extra_info")


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name_card", "phone_display", "email_display", "request_type_badge", "approval_badge", "created_at_formatted")
    list_display_links = ("name_card",)
    list_filter = ("is_processed", "approval_status", "request_type", "created_at")
    search_fields = ("name", "company_name", "phone", "email", "message", "admin_comment")
    readonly_fields = ("created_at", "approved_at", "price_list_sent_at", "approved_by")

    def name_card(self, obj):
        company = f" • <span style='color: #ff8400;'>{obj.company_name}</span>" if obj.company_name else ""
        return mark_safe(f"<strong>{obj.name}</strong>{company}")
    name_card.short_description = "Заявитель / Компания"

    def phone_display(self, obj):
        if not obj.phone:
            return "—"
        clean = "".join(c for c in obj.phone if c.isdigit() or c == "+")
        return format_html('<a href="tel:{}" style="color: #38bdf8; font-weight: 600; text-decoration: none;">{}</a>', clean, obj.phone)
    phone_display.short_description = "Телефон"

    def email_display(self, obj):
        if not obj.email:
            return mark_safe('<span style="color: #94a3b8;">—</span>')
        return format_html('<a href="mailto:{}" style="color: #a5b4fc; text-decoration: none;">{}</a>', obj.email, obj.email)
    email_display.short_description = "E-mail"

    def request_type_badge(self, obj):
        if obj.request_type == "wholesale":
            return mark_safe('<span style="background: rgba(255, 132, 0, 0.15); color: #ff8400; border: 1px solid rgba(255, 132, 0, 0.3); padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 11px;">📦 Оптовый прайс</span>')
        elif obj.request_type == "question":
            return mark_safe('<span style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 2px 7px; border-radius: 4px; font-size: 11px;">❓ Вопрос</span>')
        return mark_safe('<span style="background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); padding: 2px 7px; border-radius: 4px; font-size: 11px;">📞 Звонок</span>')
    request_type_badge.short_description = "Тип"

    def approval_badge(self, obj):
        if obj.request_type == "wholesale":
            if obj.approval_status == "approved":
                return mark_safe('<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">✅ Одобрено (Отправлен)</span>')
            elif obj.approval_status == "rejected":
                return mark_safe('<span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">❌ Отклонено</span>')
            return mark_safe('<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">⏳ Ожидает одобрения</span>')
        
        if obj.is_processed:
            return mark_safe('<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px;">✓ Обработано</span>')
        return mark_safe('<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px;">⌛ Новая</span>')
    approval_badge.short_description = "Статус"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")
    created_at_formatted.short_description = "Дата"
    created_at_formatted.admin_order_field = "created_at"

    actions = ["mark_as_processed", "mark_as_unprocessed", "approve_and_send_wholesale_selected"]

    @admin.action(description="Отметить выбранные заявки как обработанные")
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)

    @admin.action(description="Вернуть выбранные заявки в статус «Новая»")
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)

    @admin.action(description="⚡ Одобрить и отправить прайс-лист (для оптовых заявок)")
    def approve_and_send_wholesale_selected(self, request, queryset):
        ws_qs = queryset.filter(request_type="wholesale")
        if not ws_qs.exists():
            self.message_user(request, "Среди выбранных записей нет заявок на оптовый прайс-лист.", level=messages.WARNING)
            return
        cached_xlsx = generate_wholesale_price_list_xlsx()
        sent_count = 0
        for r in ws_qs:
            if r.email:
                res = send_wholesale_price_list_email(
                    recipient_email=r.email,
                    recipient_name=r.name,
                    company_name=r.company_name,
                    request_obj=r,
                    admin_user=request.user,
                    cached_xlsx_data=cached_xlsx,
                )
                if res.get("success"):
                    sent_count += 1
        self.message_user(request, f"Успешно одобрено и отправлено прайс-листов: {sent_count}.", level=messages.SUCCESS)


@admin.register(WholesalePriceRequest)
class WholesalePriceRequestAdmin(admin.ModelAdmin):
    change_list_template = "admin/main/wholesalepricerequest/change_list.html"
    list_display = (
        "id",
        "company_and_name_card",
        "phone_display",
        "email_display",
        "approval_badge",
        "approved_by_info",
        "sent_date_formatted",
        "quick_action_buttons",
        "created_at_formatted",
    )
    list_display_links = ("company_and_name_card",)
    list_filter = ("approval_status", "is_processed", "created_at", "approved_at")
    search_fields = ("name", "company_name", "phone", "email", "message", "admin_comment")
    readonly_fields = ("created_at", "approved_at", "price_list_sent_at", "approved_by", "preview_price_list_link")

    fieldsets = (
        ("Данные контрагента / заявителя", {
            "fields": (
                ("company_name", "name"),
                ("phone", "email"),
                "message",
            )
        }),
        ("Одобрение заявки и отправка прайс-листа", {
            "fields": (
                "approval_status",
                ("approved_by", "approved_at"),
                "price_list_sent_at",
                "preview_price_list_link",
                "admin_comment",
            ),
            "description": "После одобрения заявки свежесформированный оптовый прайс-лист автоматически направляется на указанный Email."
        }),
        ("Служебная информация", {
            "classes": ("collapse",),
            "fields": ("is_processed", "created_at"),
        }),
    )

    actions = [
        "approve_and_send_selected",
        "approve_and_send_all_pending",
        "reject_selected",
        "download_price_list_action",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:request_id>/approve-send/",
                self.admin_site.admin_view(self.approve_and_send_single_view),
                name="main_wholesalepricerequest_approve_send",
            ),
            path(
                "download-price-list/",
                self.admin_site.admin_view(self.download_price_list_view),
                name="main_wholesalepricerequest_download",
            ),
            path(
                "preview-html/",
                self.admin_site.admin_view(self.preview_html_view),
                name="main_wholesalepricerequest_preview",
            ),
            path(
                "mailing/",
                self.admin_site.admin_view(self.mailing_view),
                name="main_wholesalepricerequest_mailing",
            ),
        ]
        return custom_urls + urls

    def company_and_name_card(self, obj):
        company = obj.company_name or "Организация не указана"
        contact = obj.name or "Контакт не указан"
        return format_html(
            '<div style="min-width: 170px;">'
            '<div style="font-weight: 700; color: var(--admin-text-title, #f8fafc); font-size: 13px; display: flex; align-items: center; gap: 5px;">'
            '<i class="bi bi-building" style="color: #ff8400; font-size: 12px;"></i> {}'
            '</div>'
            '<div style="font-size: 11px; color: var(--admin-text-muted, #94a3b8); margin-top: 3px;">'
            '👤 {}'
            '</div>'
            '</div>',
            company, contact
        )
    company_and_name_card.short_description = "Организация / Заявитель"

    def phone_display(self, obj):
        if not obj.phone:
            return mark_safe('<span style="color: #94a3b8;">—</span>')
        clean_phone = "".join(c for c in obj.phone if c.isdigit() or c == "+")
        return format_html(
            '<a href="tel:{}" style="color: #38bdf8; font-weight: 600; text-decoration: none; font-size: 12px; white-space: nowrap;">'
            '<i class="bi bi-telephone-fill" style="font-size: 11px; margin-right: 4px;"></i>{}'
            '</a>',
            clean_phone, obj.phone
        )
    phone_display.short_description = "Телефон"

    def email_display(self, obj):
        if not obj.email:
            return mark_safe('<span style="color: #f87171; font-weight: 600; font-size: 11px;">⚠️ Нет Email</span>')
        return format_html(
            '<a href="mailto:{}" style="color: #a5b4fc; font-weight: 600; text-decoration: none; font-size: 12px; white-space: nowrap;">'
            '<i class="bi bi-envelope-at-fill" style="font-size: 11px; margin-right: 4px;"></i>{}'
            '</a>',
            obj.email, obj.email
        )
    email_display.short_description = "E-mail"

    def approval_badge(self, obj):
        if obj.approval_status == "approved":
            return mark_safe(
                '<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; white-space: nowrap;">'
                '<i class="bi bi-check-circle-fill" style="margin-right: 3px;"></i> Одобрено (Прайс отправлен)'
                '</span>'
            )
        elif obj.approval_status == "rejected":
            return mark_safe(
                '<span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; white-space: nowrap;">'
                '<i class="bi bi-x-circle-fill" style="margin-right: 3px;"></i> Отклонено'
                '</span>'
            )
        return mark_safe(
            '<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; white-space: nowrap;">'
            '<i class="bi bi-hourglass-split" style="margin-right: 3px;"></i> Ожидает одобрения'
            '</span>'
        )
    approval_badge.short_description = "Статус одобрения"

    def approved_by_info(self, obj):
        if obj.approved_by:
            name = obj.approved_by.first_name or obj.approved_by.username
            return format_html('<span style="font-size: 11px; color: var(--admin-text-main, #e2e8f0);">👤 {}</span>', name)
        return mark_safe('<span style="color: #64748b; font-size: 11px;">—</span>')
    approved_by_info.short_description = "Кто одобрил"

    def sent_date_formatted(self, obj):
        if obj.price_list_sent_at:
            return format_html(
                '<span style="font-size: 11px; color: var(--admin-text-main, #e2e8f0); white-space: nowrap;">{}</span>',
                obj.price_list_sent_at.strftime("%d.%m.%Y %H:%M")
            )
        return mark_safe('<span style="color: #64748b; font-size: 11px;">Не отправлялся</span>')
    sent_date_formatted.short_description = "Дата отправки"

    def quick_action_buttons(self, obj):
        send_url = reverse("admin:main_wholesalepricerequest_approve_send", args=[obj.id])
        if obj.approval_status != "approved":
            return format_html(
                '<a href="{}" class="sib-btn-action primary" style="padding: 4px 10px; font-size: 11px; font-weight: 700; white-space: nowrap;" onclick="return confirm(\'Одобрить заявку #{}: сгенерировать прайс и отправить на {}?\');">'
                '<i class="bi bi-check2-circle"></i> Одобрить и отправить'
                '</a>',
                send_url, obj.id, obj.email or "не указан"
            )
        return format_html(
            '<a href="{}" class="sib-btn-action" style="padding: 4px 10px; font-size: 11px; font-weight: 600; white-space: nowrap;" onclick="return confirm(\'Отправить обновленный прайс-лист клиенту повторно на {}?\');">'
            '<i class="bi bi-arrow-repeat"></i> Повторить'
            '</a>',
            send_url, obj.email or "не указан"
        )
    quick_action_buttons.short_description = "Действие"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")
    created_at_formatted.short_description = "Дата заявки"
    created_at_formatted.admin_order_field = "created_at"

    def preview_price_list_link(self, obj):
        download_url = reverse("admin:main_wholesalepricerequest_download")
        preview_url = reverse("admin:main_wholesalepricerequest_preview")
        return format_html(
            '<div style="display: flex; gap: 10px; align-items: center; margin-top: 4px;">'
            '<a href="{}" target="_blank" class="sib-btn-action primary" style="font-size: 12px; padding: 6px 12px;"><i class="bi bi-download"></i> Скачать свежий прайс (.xlsx)</a>'
            '<a href="{}" target="_blank" class="sib-btn-action" style="font-size: 12px; padding: 6px 12px;"><i class="bi bi-eye"></i> Предпросмотр в браузере</a>'
            '</div>',
            download_url, preview_url
        )
    preview_price_list_link.short_description = "Сформированный прайс-лист"

    @admin.action(description="⚡ Одобрить и отправить прайс-лист выбранным заявкам")
    def approve_and_send_selected(self, request, queryset):
        cached_xlsx = generate_wholesale_price_list_xlsx()
        sent_count = 0
        skipped_count = 0
        errors = []

        for req_obj in queryset:
            if not req_obj.email or "@" not in req_obj.email:
                skipped_count += 1
                continue
            res = send_wholesale_price_list_email(
                recipient_email=req_obj.email,
                recipient_name=req_obj.name,
                company_name=req_obj.company_name,
                request_obj=req_obj,
                admin_user=request.user,
                cached_xlsx_data=cached_xlsx,
            )
            if res.get("success"):
                sent_count += 1
            else:
                errors.append(f"{req_obj.email}: {res.get('error')}")

        msg = f"Успешно одобрено и отправлено прайс-листов: {sent_count}."
        if skipped_count > 0:
            msg += f" Пропущено из-за отсутствия Email: {skipped_count}."
        if errors:
            msg += f" Ошибок отправки: {len(errors)}."
            self.message_user(request, msg, level=messages.WARNING)
        else:
            self.message_user(request, msg, level=messages.SUCCESS)

    @admin.action(description="🚀 Одобрить и отправить прайс-лист ВСЕМ ожидающим заявкам")
    def approve_and_send_all_pending(self, request, queryset):
        pending_qs = WholesalePriceRequest.objects.filter(approval_status="pending")
        total_pending = pending_qs.count()
        if total_pending == 0:
            self.message_user(request, "Нет заявок, ожидающих одобрения.", level=messages.INFO)
            return

        cached_xlsx = generate_wholesale_price_list_xlsx()
        sent_count = 0
        skipped_count = 0
        errors = []

        for req_obj in pending_qs:
            if not req_obj.email or "@" not in req_obj.email:
                skipped_count += 1
                continue
            res = send_wholesale_price_list_email(
                recipient_email=req_obj.email,
                recipient_name=req_obj.name,
                company_name=req_obj.company_name,
                request_obj=req_obj,
                admin_user=request.user,
                cached_xlsx_data=cached_xlsx,
            )
            if res.get("success"):
                sent_count += 1
            else:
                errors.append(f"{req_obj.email}: {res.get('error')}")

        msg = f"Всего обработано: {total_pending}. Успешно отправлено прайс-листов: {sent_count}."
        if skipped_count:
            msg += f" Пропущено без Email: {skipped_count}."
        if errors:
            self.message_user(request, msg, level=messages.WARNING)
        else:
            self.message_user(request, msg, level=messages.SUCCESS)

    @admin.action(description="❌ Отклонить выбранные заявки")
    def reject_selected(self, request, queryset):
        count = queryset.update(approval_status="rejected", is_processed=True)
        self.message_user(request, f"Отклонено заявок: {count}.", level=messages.INFO)

    @admin.action(description="📥 Скачать актуальный оптовый прайс-лист (.xlsx)")
    def download_price_list_action(self, request, queryset):
        return redirect("admin:main_wholesalepricerequest_download")

    def approve_and_send_single_view(self, request, request_id):
        try:
            req_obj = WholesalePriceRequest.objects.get(id=request_id)
        except WholesalePriceRequest.DoesNotExist:
            self.message_user(request, "Заявка не найдена.", level=messages.ERROR)
            return redirect("admin:main_wholesalepricerequest_changelist")

        if not req_obj.email or "@" not in req_obj.email:
            self.message_user(
                request,
                f"У заявки #{req_obj.id} не указан E-mail. Укажите адрес электронной почты клиента для отправки прайса.",
                level=messages.ERROR
            )
            return redirect("admin:main_wholesalepricerequest_change", req_obj.id)

        res = send_wholesale_price_list_email(
            recipient_email=req_obj.email,
            recipient_name=req_obj.name,
            company_name=req_obj.company_name,
            request_obj=req_obj,
            admin_user=request.user,
        )

        if res.get("success"):
            notice = " (отправка зафиксирована)" if res.get("simulated") else ""
            self.message_user(
                request,
                f"✅ Заявка #{req_obj.id} ({req_obj.name}) успешно одобрена! Свежий оптовый прайс-лист сформирован и отправлен на {req_obj.email}{notice}.",
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f"Ошибка отправки прайс-листа на {req_obj.email}: {res.get('error')}",
                level=messages.ERROR
            )

        referer = request.META.get("HTTP_REFERER")
        if referer and ("change" in referer or "wholesalepricerequest" in referer):
            return HttpResponseRedirect(referer)
        return redirect("admin:main_wholesalepricerequest_changelist")

    def download_price_list_view(self, request):
        xlsx_bytes, filename = generate_wholesale_price_list_xlsx()
        response = HttpResponse(
            xlsx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def preview_html_view(self, request):
        html = generate_wholesale_price_list_html()
        return HttpResponse(html, content_type="text/html; charset=utf-8")

    def mailing_view(self, request):
        from accounts.models import UserProfile
        from shop.models import Product

        site_settings = SiteSettings.get_solo() if hasattr(SiteSettings, "get_solo") else SiteSettings.objects.first()
        default_subject = getattr(site_settings, "wholesale_email_subject", "") or "Оптовый прайс-лист ТМ «Сибсыр» и коммерческие условия"
        default_body = getattr(site_settings, "wholesale_email_body", "")

        pending_requests_count = WholesalePriceRequest.objects.filter(approval_status="pending").exclude(email="").count()
        total_wholesale_requests_count = WholesalePriceRequest.objects.exclude(email="").count()
        legal_clients_count = UserProfile.objects.filter(customer_type="legal").exclude(user__email="").count()
        active_products_count = Product.objects.filter(is_active=True).count()

        target_single_email = request.GET.get("email", "").strip()
        target_single_name = request.GET.get("name", "").strip()
        target_single_request_id = request.GET.get("request_id", "").strip()

        report = None

        if request.method == "POST":
            target = request.POST.get("recipient_target", "pending")
            custom_subject = request.POST.get("email_subject", default_subject).strip()
            custom_body = request.POST.get("email_body", default_body).strip()

            recipients_list = []

            if target == "single":
                s_email = request.POST.get("single_email", "").strip()
                s_name = request.POST.get("single_name", "").strip()
                s_req_id = request.POST.get("single_request_id", "").strip()
                req_instance = None
                if s_req_id:
                    req_instance = WholesalePriceRequest.objects.filter(id=s_req_id).first()
                if s_email:
                    recipients_list.append((s_email, s_name, "", req_instance, None))

            elif target == "pending":
                for r in WholesalePriceRequest.objects.filter(approval_status="pending"):
                    if r.email:
                        recipients_list.append((r.email, r.name, r.company_name, r, None))

            elif target == "legal_profiles":
                for p in UserProfile.objects.filter(customer_type="legal").select_related("user"):
                    if p.user and p.user.email:
                        recipients_list.append((p.user.email, p.display_name, p.company_name, None, p))

            elif target == "all_wholesale":
                seen_emails = set()
                for r in WholesalePriceRequest.objects.all():
                    if r.email and r.email.lower() not in seen_emails:
                        seen_emails.add(r.email.lower())
                        recipients_list.append((r.email, r.name, r.company_name, r, None))
                for p in UserProfile.objects.filter(customer_type="legal").select_related("user"):
                    if p.user and p.user.email and p.user.email.lower() not in seen_emails:
                        seen_emails.add(p.user.email.lower())
                        recipients_list.append((p.user.email, p.display_name, p.company_name, None, p))

            elif target == "custom":
                c_email = request.POST.get("custom_email", "").strip()
                c_name = request.POST.get("custom_name", "").strip()
                if c_email:
                    recipients_list.append((c_email, c_name, "", None, None))

            cached_xlsx = generate_wholesale_price_list_xlsx()
            sent_count = 0
            skipped_count = 0
            details = []
            errors_exist = False

            for email_addr, name_str, comp_str, r_obj, p_obj in recipients_list:
                if not email_addr or "@" not in email_addr:
                    skipped_count += 1
                    continue
                res = send_wholesale_price_list_email(
                    recipient_email=email_addr,
                    recipient_name=name_str,
                    company_name=comp_str,
                    custom_subject=custom_subject,
                    custom_body=custom_body,
                    request_obj=r_obj,
                    user_profile=p_obj,
                    admin_user=request.user,
                    cached_xlsx_data=cached_xlsx,
                )
                if res.get("success"):
                    sent_count += 1
                    details.append({"email": email_addr, "name": name_str, "success": True})
                else:
                    errors_exist = True
                    details.append({"email": email_addr, "name": name_str, "success": False, "error": res.get("error")})

            report = {
                "sent_count": sent_count,
                "skipped_count": skipped_count,
                "errors": errors_exist,
                "details": details,
            }

            if not errors_exist:
                self.message_user(
                    request,
                    f"✅ Прайс-лист успешно сформирован и отправлен {sent_count} контрагентам!",
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"Отправка выполнена: успешно {sent_count}, ошибок {len(details) - sent_count}.",
                    level=messages.WARNING
                )

        context = {
            **self.admin_site.each_context(request),
            "pending_requests_count": pending_requests_count,
            "total_wholesale_requests_count": total_wholesale_requests_count,
            "legal_clients_count": legal_clients_count,
            "active_products_count": active_products_count,
            "default_subject": default_subject,
            "default_body": default_body,
            "target_single_email": target_single_email,
            "target_single_name": target_single_name,
            "target_single_request_id": target_single_request_id,
            "report": report,
        }
        return render(request, "admin/wholesale_mailing.html", context)


class FaqItemInline(RichTextAdminMixin, admin.StackedInline):
    model = FaqItem
    rich_text_fields = ("answer",)
    extra = 1
    fields = ("order", "question", "answer", "is_active")


@admin.register(FaqCategory)
class FaqCategoryAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "slug", "items_count", "is_active")
    list_display_links = ("name",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [FaqItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Вопросов"


@admin.register(FaqItem)
class FaqItemAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("answer",)
    list_display = ("order", "question", "category", "is_active", "updated_at")
    list_display_links = ("question",)
    list_editable = ("order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    autocomplete_fields = ()


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("order", "icon_badge", "name", "url_link", "is_active", "open_in_new_tab")
    list_display_links = ("icon_badge", "name")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "open_in_new_tab")
    search_fields = ("name", "url")
    readonly_fields = ("icon_preview",)
    fieldsets = (
        ("Основные параметры соцсети", {
            "fields": (
                ("name", "is_active"),
                "url",
                ("order", "open_in_new_tab"),
            )
        }),
        ("Иконка социальной сети", {
            "fields": (
                ("icon", "icon_preview"),
                "bootstrap_icon",
            ),
            "description": "Загрузите графический файл иконки (PNG, SVG, WebP) или укажите класс Bootstrap Icons (например, bi-telegram)."
        }),
    )

    def icon_badge(self, obj):
        icon_url = obj.get_icon_url()
        if icon_url:
            return format_html(
                '<div style="width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; background: #0f172a; border-radius: 8px; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);">'
                '<img src="{}" alt="{}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px;" />'
                '</div>',
                icon_url, obj.name
            )
        elif obj.bootstrap_icon:
            return format_html(
                '<div style="width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; background: #ff8400; color: #fff; border-radius: 8px; font-size: 1rem;">'
                '<i class="bi {}"></i>'
                '</div>',
                obj.bootstrap_icon
            )
        return format_html(
            '<div style="width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; background: #64748b; color: #fff; border-radius: 8px;">'
            '<i class="bi bi-link-45deg"></i>'
            '</div>'
        )
    icon_badge.short_description = "Иконка"

    def icon_preview(self, obj):
        icon_url = obj.get_icon_url()
        if icon_url:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 12px;">'
                '<div style="width: 54px; height: 54px; display: inline-flex; align-items: center; justify-content: center; background: #0f172a; border-radius: 12px; padding: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">'
                '<img src="{}" alt="{}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 6px;" />'
                '</div>'
                '<div>'
                '<div style="color: #10b981; font-weight: 600; font-size: 13px;">✓ Иконка загружена и активна</div>'
                '<div style="color: #64748b; font-size: 11px; margin-top: 2px;">Отображается в футере сайта</div>'
                '</div>'
                '</div>',
                icon_url, obj.name
            )
        return format_html('<span style="color: #94a3b8; font-size: 12px;">Файл иконки не загружен (будет использована иконка по умолчанию или Bootstrap)</span>')
    icon_preview.short_description = "Вид иконки"

    def url_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer" style="color: #ff8400; text-decoration: none; font-weight: 500;">'
            '{} <i class="bi bi-box-arrow-up-right" style="font-size: 11px; margin-left: 3px;"></i>'
            '</a>',
            obj.url, obj.url
        )
    url_link.short_description = "Ссылка"


# ==============================================================================
# УПРАВЛЕНИЕ ДИНАМИЧЕСКИМИ СТРАНИЦАМИ И SEO-ПРОДВИЖЕНИЕМ
# ==============================================================================

@admin.register(Page)
class PageAdmin(RichTextAdminMixin, DragDropReorderMixin, admin.ModelAdmin):
    rich_text_fields = ("content",)
    reorder_field = "order"
    change_form_template = "admin/main/page/change_form.html"
    prepopulated_fields = {"slug": ("title",)}
    
    list_display = (
        "title_column",
        "slug_badge",
        "layout_badge",
        "seo_health_badge",
        "nav_badges",
        "sitemap_badge",
        "views_count_badge",
        "published_status",
        "order",
    )
    list_filter = (
        "is_published",
        "show_in_header",
        "show_in_footer",
        "template_layout",
        "sitemap_include",
        "meta_robots_index",
        "schema_type",
    )
    search_fields = (
        "title",
        "slug",
        "subtitle",
        "content",
        "meta_title",
        "meta_description",
        "focus_keyword",
    )
    readonly_fields = (
        "views_count",
        "updated_at",
        "featured_image_preview",
        "og_image_preview",
        "seo_live_preview",
        "og_live_preview",
        "direct_url_preview",
    )

    fieldsets = (
        ("📌 Основная информация о странице", {
            "classes": ("tab-pane-content", "sib-page-card"),
            "description": "Задайте заголовок страницы (H1), человекопонятный URL (слаг) и вводный подзаголовок (lead).",
            "fields": (
                ("title", "slug"),
                ("menu_title", "badge"),
                "subtitle",
                "direct_url_preview",
            )
        }),
        ("📝 Содержимое страницы и медиа", {
            "classes": ("tab-pane-content", "sib-page-card"),
            "description": "Основной текст страницы с поддержкой визуального редактора TinyMCE: заголовки, таблицы, списки, изображения.",
            "fields": (
                "content",
                ("featured_image", "featured_image_preview"),
            )
        }),
        ("🎨 Макет и элементы оформления", {
            "classes": ("tab-pane-layout", "sib-page-card"),
            "description": "Настройка типа контейнера, отображения промо-шапки, цепочки хлебных крошек и нижнего блока CTA.",
            "fields": (
                ("template_layout", "show_hero_banner"),
                ("show_cta_block", "show_breadcrumbs"),
            )
        }),
        ("🧭 Навигация и размещение в меню сайта", {
            "classes": ("tab-pane-layout", "sib-page-card"),
            "description": "Управление выводом ссылки на страницу в шапке сайта и в блоках футера.",
            "fields": (
                ("show_in_header", "show_in_footer"),
                "order",
            )
        }),
        ("🚀 Поисковое продвижение (SEO инструменты)", {
            "classes": ("tab-pane-seo", "sib-page-card"),
            "description": "Ключевые мета-теги для продвижения в поисковых системах Яндекс и Google, интерактивный сниппет и robots.",
            "fields": (
                "seo_live_preview",
                "focus_keyword",
                "meta_title",
                "meta_description",
                "meta_keywords",
                ("canonical_url", "meta_robots_index"),
            )
        }),
        ("📱 Социальные сети и мессенджеры (Open Graph)", {
            "classes": ("tab-pane-og", "sib-page-card"),
            "description": "Настройка привлекательной карточки для шеринга в Telegram, ВКонтакте, WhatsApp и мессенджерах.",
            "fields": (
                "og_live_preview",
                "og_title",
                "og_description",
                ("og_image", "og_image_preview"),
                "og_type",
            )
        }),
        ("🗺 Карта сайта (Sitemap XML)", {
            "classes": ("tab-pane-sitemap", "sib-page-card"),
            "description": "Параметры включения страницы в sitemap.xml для поисковых ботов.",
            "fields": (
                ("sitemap_include", "sitemap_priority", "sitemap_changefreq"),
            )
        }),
        ("⚙️ Микроразметка Schema.org и коды отслеживания", {
            "classes": ("tab-pane-tech", "sib-page-card"),
            "description": "Структурированные данные Schema.org (JSON-LD) и индивидуальные скрипты ретаргетинга/целей для страницы.",
            "fields": (
                "schema_type",
                "custom_schema_json",
                "custom_head_code",
                "custom_body_code",
            )
        }),
        ("👁 Статус публикации и даты", {
            "classes": ("tab-pane-publish", "sib-page-card"),
            "description": "Управление видимостью страницы для гостей и статистика посещений.",
            "fields": (
                ("is_published", "published_at"),
                ("views_count", "updated_at"),
            )
        }),
    )

    actions = [
        "generate_seo_selected",
        "publish_selected",
        "unpublish_selected",
        "include_sitemap_selected",
        "exclude_sitemap_selected",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "auto-seo/",
                self.admin_site.admin_view(self.auto_seo_view),
                name="main_page_auto_seo",
            ),
        ]
        return custom_urls + urls

    def auto_seo_view(self, request):
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
        try:
            body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body
            data = json.loads(body)
        except Exception:
            data = request.POST

        title = data.get("title", "").strip()
        subtitle = data.get("subtitle", "").strip()
        content = data.get("content", "").strip()
        focus_kw = data.get("focus_keyword", "").strip()

        if not title:
            return JsonResponse({"status": "error", "message": "Сначала введите заголовок страницы (H1)"}, status=400)

        temp_page = Page(title=title, subtitle=subtitle, content=content, focus_keyword=focus_kw)
        temp_page.generate_seo(overwrite=True)

        return JsonResponse({
            "status": "success",
            "meta_title": temp_page.meta_title,
            "meta_description": temp_page.meta_description,
            "meta_keywords": temp_page.meta_keywords,
            "og_title": temp_page.og_title,
            "og_description": temp_page.og_description,
        })

    def title_column(self, obj):
        badge_html = f'<span style="background: rgba(255, 132, 0, 0.15); color: #c25e00; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 6px; font-weight: 600;">{obj.badge}</span>' if obj.badge else ""
        view_url = obj.get_absolute_url()
        return format_html(
            '<div style="font-weight: 600; font-size: 14px; color: #1e293b; display: flex; align-items: center; gap: 4px;">'
            '{}{}'
            '<a href="{}" target="_blank" title="Открыть страницу на сайте" style="color: #64748b; font-size: 12px; margin-left: 6px; text-decoration: none;">'
            '<i class="bi bi-box-arrow-up-right"></i>'
            '</a>'
            '</div>'
            '<div style="color: #64748b; font-size: 12px; margin-top: 2px;">{}</div>',
            mark_safe(badge_html),
            obj.title,
            view_url,
            (obj.subtitle[:90] + "...") if obj.subtitle and len(obj.subtitle) > 90 else (obj.subtitle or "—")
        )
    title_column.short_description = "Заголовок страницы"

    def slug_badge(self, obj):
        return format_html(
            '<code style="background: #f1f5f9; color: #0284c7; padding: 3px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">/{}</code>',
            obj.slug
        )
    slug_badge.short_description = "URL (Слаг)"

    def layout_badge(self, obj):
        layout_map = {
            'standard': ('Стандарт', '#e0f2fe', '#0369a1'),
            'narrow': ('Документ', '#f1f5f9', '#475569'),
            'fullwidth': ('Лендинг', '#fef3c7', '#92400e'),
        }
        name, bg, color = layout_map.get(obj.template_layout, ('Стандарт', '#f1f5f9', '#334155'))
        return format_html(
            '<span style="background: {}; color: {}; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">{}</span>',
            bg, color, name
        )
    layout_badge.short_description = "Макет"

    def seo_health_badge(self, obj):
        analysis = obj.get_seo_analysis()
        score = analysis["score"]
        grade = analysis["grade"]
        if grade == "success":
            bg, color, icon = "#dcfce7", "#166534", "✓"
        elif grade == "warning":
            bg, color, icon = "#fef3c7", "#92400e", "!"
        else:
            bg, color, icon = "#fee2e2", "#991b1b", "✕"

        return format_html(
            '<span style="background: {}; color: {}; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">'
            '{} {}%'
            '</span>',
            bg, color, icon, score
        )
    seo_health_badge.short_description = "SEO-готовность"

    def nav_badges(self, obj):
        items = []
        if obj.show_in_header:
            items.append('<span style="background: #e0e7ff; color: #3730a3; padding: 2px 5px; border-radius: 4px; font-size: 10px; font-weight: 600;">Шапка</span>')
        if obj.show_in_footer:
            items.append('<span style="background: #f1f5f9; color: #475569; padding: 2px 5px; border-radius: 4px; font-size: 10px; font-weight: 600;">Подвал</span>')
        if not items:
            return format_html('<span style="color: #94a3b8; font-size: 11px;">Прямой URL</span>')
        return mark_safe(" ".join(items))
    nav_badges.short_description = "В меню"

    def sitemap_badge(self, obj):
        if obj.sitemap_include and "noindex" not in obj.meta_robots_index:
            return format_html(
                '<span style="color: #10b981; font-weight: 600; font-size: 11px;">✓ XML ({})</span>',
                obj.sitemap_priority
            )
        elif "noindex" in obj.meta_robots_index:
            return format_html('<span style="color: #ef4444; font-size: 11px;">noindex</span>')
        return format_html('<span style="color: #94a3b8; font-size: 11px;">Скрыто</span>')
    sitemap_badge.short_description = "Sitemap"

    def views_count_badge(self, obj):
        return format_html(
            '<span style="font-size: 12px; color: #475569; font-weight: 500;"><i class="bi bi-eye text-muted me-1"></i>{}</span>',
            obj.views_count
        )
    views_count_badge.short_description = "Просмотры"

    def published_status(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">Активна</span>'
            )
        return format_html(
            '<span style="background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">Черновик</span>'
        )
    published_status.short_description = "Статус"

    def direct_url_preview(self, obj):
        if not obj or not obj.pk:
            return format_html('<span style="color: #94a3b8; font-size: 12px;">Адрес будет доступен после сохранения</span>')
        main_url = obj.get_absolute_url()
        direct_url = f"/{obj.slug}/"
        pages_url = f"/pages/{obj.slug}/"
        company_url = f"/company/{obj.slug}/"
        urls = [main_url]
        for candidate in [company_url, direct_url, pages_url]:
            if candidate not in urls:
                urls.append(candidate)

        links_html = "".join([
            f'<a href="{u}" target="_blank" style="color: #0284c7; text-decoration: none; font-weight: 600; padding: 4px 10px; background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;"><i class="bi bi-link-45deg"></i> {u} ↗</a> '
            for u in urls
        ])
        return format_html(
            '<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; font-size: 13px;">'
            '<div style="color: #475569; margin-bottom: 8px; font-weight: 600;">Страница доступна по следующим адресам на сайте:</div>'
            '<div style="display: flex; gap: 8px; flex-wrap: wrap;">'
            '{}'
            '</div>'
            '</div>',
            mark_safe(links_html)
        )
    direct_url_preview.short_description = "Адреса страницы на сайте"

    def featured_image_preview(self, obj):
        if obj and obj.featured_image:
            return format_html(
                '<div style="margin-top: 6px;">'
                '<img src="{}" alt="Обложка" style="max-width: 200px; max-height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 6px rgba(0,0,0,0.08);" />'
                '</div>',
                obj.featured_image.url
            )
        return format_html('<span style="color: #94a3b8; font-size: 12px;">Обложка не загружена</span>')
    featured_image_preview.short_description = "Превью обложки"

    def og_image_preview(self, obj):
        if obj and obj.og_image:
            return format_html(
                '<div style="margin-top: 6px;">'
                '<img src="{}" alt="OG Image" style="max-width: 220px; max-height: 115px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 6px rgba(0,0,0,0.08);" />'
                '</div>',
                obj.og_image.url
            )
        return format_html('<span style="color: #94a3b8; font-size: 12px;">Изображение соцсетей не загружено (будет использована обложка)</span>')
    og_image_preview.short_description = "Превью соцсетей"

    def seo_live_preview(self, obj):
        return mark_safe("""
        <div class="sib-seo-preview-card" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;">
                <span style="font-weight: 700; font-size: 12px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 6px;">
                    <i class="bi bi-google text-primary"></i> <i class="bi bi-search text-warning"></i> Живой поисковый сниппет (Яндекс / Google)
                </span>
                <button type="button" id="btnAutoSeoInForm" class="button" style="background: #ff8400; color: #ffffff; font-size: 11px; padding: 4px 12px; border-radius: 6px; border: none; cursor: pointer; font-weight: 600;">
                    ⚡ Автозаполнить SEO из текста
                </button>
            </div>
            <div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.4; max-width: 600px;">
                <div style="font-size: 12px; color: #202124; display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                    <span style="background: #fff3e0; border-radius: 50%; width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px;">🧀</span>
                    <span id="livePreviewUrl" style="color: #202124; font-size: 12px;">https://sibsir.ru › pages › ...</span>
                </div>
                <div id="livePreviewTitle" style="color: #1a0dab; font-size: 18px; font-weight: 400; text-decoration: none; cursor: pointer; margin-bottom: 3px; word-break: break-word;">
                    Заголовок страницы появится здесь...
                </div>
                <div id="livePreviewDesc" style="color: #4d5156; font-size: 13px; word-break: break-word;">
                    Здесь будет отображаться описание сниппета для поисковых систем Яндекс и Google (Meta Description)...
                </div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #f1f5f9; display: flex; gap: 10px; font-size: 11px; color: #64748b;">
                <span id="titleCounterBadge" style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">Title: <strong id="titleCount">0</strong> / 65 симв.</span>
                <span id="descCounterBadge" style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">Description: <strong id="descCount">0</strong> / 175 симв.</span>
            </div>
        </div>
        """)
    seo_live_preview.short_description = "Интерактивный поисковый сниппет"

    def og_live_preview(self, obj):
        return mark_safe("""
        <div class="sib-og-preview-card" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="font-weight: 700; font-size: 12px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <i class="bi bi-telegram text-info"></i> <i class="bi bi-share-fill text-primary"></i> Превью карточки в Telegram и ВКонтакте
            </div>
            <div style="border-left: 3px solid #2563eb; background: #f8fafc; border-radius: 0 8px 8px 0; padding: 10px 14px; max-width: 480px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="font-size: 11px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">SIBSIR.RU</div>
                <div id="liveOgTitle" style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px; line-height: 1.3;">
                    Заголовок для соцсетей...
                </div>
                <div id="liveOgDesc" style="font-size: 12px; color: #64748b; line-height: 1.4;">
                    Описание ссылки в соцсетях...
                </div>
            </div>
        </div>
        """)
    og_live_preview.short_description = "Превью для соцсетей"

    @admin.action(description="⚡ Сгенерировать SEO-теги автоматически")
    def generate_seo_selected(self, request, queryset):
        count = 0
        for page in queryset:
            page.generate_seo(overwrite=True)
            page.save(update_fields=["meta_title", "meta_description", "meta_keywords", "og_title", "og_description"])
            count += 1
        self.message_user(request, f"SEO-теги успешно сгенерированы для {count} страниц.", level=messages.SUCCESS)

    @admin.action(description="✅ Опубликовать выбранные страницы")
    def publish_selected(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Опубликовано страниц: {updated}.", level=messages.SUCCESS)

    @admin.action(description="⏸ Снять с публикации")
    def unpublish_selected(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Снято с публикации страниц: {updated}.", level=messages.WARNING)

    @admin.action(description="🗺 Включить в sitemap.xml")
    def include_sitemap_selected(self, request, queryset):
        updated = queryset.update(sitemap_include=True)
        self.message_user(request, f"Включено в карту сайта: {updated} страниц.", level=messages.SUCCESS)

    @admin.action(description="🚫 Исключить из sitemap.xml")
    def exclude_sitemap_selected(self, request, queryset):
        updated = queryset.update(sitemap_include=False)
        self.message_user(request, f"Исключено из карты сайта: {updated} страниц.", level=messages.WARNING)



