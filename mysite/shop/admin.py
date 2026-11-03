from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from main.admin_mixins import RichTextAdminMixin, DragDropReorderMixin
from .models import Category, Product, Promotion, PromoCode, Order, OrderItem, Review


@admin.register(Category)
class CategoryAdmin(DragDropReorderMixin, RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description", "seo_text")
    list_display = ("order", "image_preview", "icon_badge", "name", "slug", "products_count", "promotions_info", "is_active")
    list_display_links = ("name",)
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "description")
    list_filter = ("is_active",)

    fieldsets = (
        ("Информация о категории", {
            "fields": ("name", "slug", "icon", "image", "description", "order", "is_active")
        }),
        ("Поисковая оптимизация (SEO) и статья раздела", {
            "fields": ("meta_title", "meta_description", "meta_keywords", "seo_text"),
            "description": "Мета-теги и подробная SEO-статья для категории в каталоге. Если оставить пустыми, генерируются автоматически."
        }),
    )
    actions = ["generate_seo_selected", "make_active", "make_inactive"]

    @admin.action(description="⚡ Сгенерировать SEO-теги для выбранных категорий")
    def generate_seo_selected(self, request, queryset):
        count = 0
        for category in queryset:
            category.generate_seo(overwrite=True)
            category.save()
            count += 1
        self.message_user(request, f"SEO-теги успешно сгенерированы для {count} категорий.")

    @admin.action(description="Активировать выбранные категории")
    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Активировано категорий: {count}.")

    @admin.action(description="Деактивировать выбранные категории")
    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано категорий: {count}.")

    def image_preview(self, obj):
        url = obj.image_url
        if url:
            return format_html('<img src="{}" style="width: 48px; height: 36px; object-fit: cover; border-radius: 6px; border: 1px solid #e2e8f0;" />', url)
        return "—"
    image_preview.short_description = "Фото"

    def icon_badge(self, obj):
        return format_html('<i class="bi {}" style="font-size: 1.2rem; color: #ff8400;"></i>', obj.icon or "bi-tag")
    icon_badge.short_description = "Иконка"

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "Товаров"

    def promotions_info(self, obj):
        promo = obj.get_active_promotion()
        if promo:
            val = f"{promo.discount_percent}%" if promo.discount_percent else f"{promo.discount_amount} ₽"
            return format_html(
                '<span style="background: #fee2e2; color: #b91c1c; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 11px;">🔥 {} (-{})</span>',
                promo.badge_text, val
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px;">Нет скидок</span>')
    promotions_info.short_description = "Акции каталога"


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "badge_preview",
        "title",
        "discount_display",
        "applies_to_badge",
        "dates_display",
        "show_banner",
        "is_active"
    )
    list_display_links = ("title",)
    list_editable = ("order", "show_banner", "is_active")
    list_filter = ("is_active", "applies_to", "show_banner")
    search_fields = ("title", "description", "badge_text")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories", "products")

    fieldsets = (
        ("Информация об акции", {
            "fields": ("title", "slug", "badge_text", "description", "icon", "banner_image")
        }),
        ("Размер скидки", {
            "fields": ("discount_percent", "discount_amount"),
            "description": "Укажите процент скидки (например, 15) ИЛИ фиксированную сумму в рублях"
        }),
        ("Область действия (Где действует акция)", {
            "fields": ("applies_to", "categories", "products"),
            "description": "Выберите: на весь каталог, на выбранные каталоги/категории, или на отдельные товары"
        }),
        ("Период действия и отображение", {
            "fields": ("start_date", "end_date", "show_banner", "order", "is_active")
        }),
    )

    def badge_preview(self, obj):
        return format_html(
            '<span style="background: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            obj.badge_text or "АКЦИЯ"
        )
    badge_preview.short_description = "Метка"

    def discount_display(self, obj):
        if obj.discount_percent:
            return format_html('<strong style="color: #dc2626; font-size: 13px;">-{}%</strong>', obj.discount_percent)
        elif obj.discount_amount:
            return format_html('<strong style="color: #dc2626; font-size: 13px;">-{} ₽</strong>', obj.discount_amount)
        return "-"
    discount_display.short_description = "Скидка"

    def applies_to_badge(self, obj):
        colors = {
            "all": ("#eff6ff", "#1d4ed8", "Весь каталог"),
            "categories": ("#fef3c7", "#b45309", f"Категории ({obj.categories.count()})"),
            "products": ("#f3e8ff", "#6b21a8", f"Товары ({obj.products.count()})"),
        }
        bg, text, label = colors.get(obj.applies_to, ("#eee", "#333", obj.get_applies_to_display()))
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            bg, text, label
        )
    applies_to_badge.short_description = "Применение"

    def dates_display(self, obj):
        if not obj.start_date and not obj.end_date:
            return "Бессрочно"
        s = obj.start_date.strftime("%d.%m.%Y") if obj.start_date else "—"
        e = obj.end_date.strftime("%d.%m.%Y") if obj.end_date else "—"
        return f"{s} по {e}"
    dates_display.short_description = "Сроки действия"


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code_badge",
        "title",
        "discount_display",
        "min_order_amount_display",
        "usage_display",
        "applies_to_badge",
        "is_active",
        "created_at"
    )
    list_display_links = ("title",)
    list_editable = ("is_active",)
    list_filter = ("is_active", "discount_type", "applies_to")
    search_fields = ("code", "title")
    filter_horizontal = ("categories", "products")

    fieldsets = (
        ("Код и описание", {
            "fields": ("code", "title", "is_active")
        }),
        ("Условия скидки", {
            "fields": ("discount_type", "discount_value", "min_order_amount", "max_discount_amount")
        }),
        ("Применимость к каталогам / товарам", {
            "fields": ("applies_to", "categories", "products"),
            "description": "Применимо ко всей корзине, к товарам определенных категорий или к конкретным товарам"
        }),
        ("Лимиты и сроки", {
            "fields": ("valid_from", "valid_to", "usage_limit", "times_used")
        }),
    )

    def code_badge(self, obj):
        return format_html(
            '<code style="background: #fef08a; color: #854d0e; padding: 4px 8px; border-radius: 4px; font-size: 13px; font-weight: 800; letter-spacing: 0.5px; border: 1px dashed #ca8a04;">{}</code>',
            obj.code
        )
    code_badge.short_description = "Код промокода"

    def discount_display(self, obj):
        if obj.discount_type == "percent":
            return format_html('<strong style="color: #16a34a; font-size: 13px;">{}%</strong>', int(obj.discount_value))
        return format_html('<strong style="color: #16a34a; font-size: 13px;">{} ₽</strong>', int(obj.discount_value))
    discount_display.short_description = "Размер скидки"

    def min_order_amount_display(self, obj):
        if obj.min_order_amount > 0:
            return f"от {int(obj.min_order_amount)} ₽"
        return "от 0 ₽"
    min_order_amount_display.short_description = "Мин. заказ"

    def usage_display(self, obj):
        if obj.usage_limit > 0:
            return f"{obj.times_used} / {obj.usage_limit}"
        return f"{obj.times_used} (безлимит)"
    usage_display.short_description = "Использований"

    def applies_to_badge(self, obj):
        colors = {
            "all": ("#eff6ff", "#1d4ed8", "Вся корзина"),
            "categories": ("#fef3c7", "#b45309", f"Категории ({obj.categories.count()})"),
            "products": ("#f3e8ff", "#6b21a8", f"Товары ({obj.products.count()})"),
        }
        bg, text, label = colors.get(obj.applies_to, ("#eee", "#333", obj.get_applies_to_display()))
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            bg, text, label
        )
    applies_to_badge.short_description = "Область"


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ("author_name", "city", "rating", "text", "is_approved", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Product)
class ProductAdmin(DragDropReorderMixin, RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("description", "full_description", "composition", "cooking_tips")
    list_per_page = 10
    inlines = [ReviewInline]
    list_display = (
        "order",
        "image_preview",
        "title",
        "category",
        "price_display",
        "price_numeric",
        "wholesale_display",
        "discount_info",
        "fat_content",
        "unit_weight",
        "badge_tag",
        "is_featured",
        "is_active",
    )
    list_display_links = ("title",)
    list_editable = ("order", "price_display", "price_numeric", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active", "badge")
    search_fields = ("title", "description", "full_description", "fat_content", "package_type", "price_display", "wholesale_price_display")
    prepopulated_fields = {"slug": ("title",)}
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("title", "slug", "category", "description")
        }),
        ("Стоимость, скидки и акции", {
            "fields": (
                "price_display", 
                "price_numeric", 
                "old_price_numeric", 
                "discount_percent", 
                "button_text", 
                "badge"
            ),
            "description": "Для скидки укажите 'Старая цена' (будет зачеркнута) или 'Прямая скидка на товар (%)'."
        }),
        ("Оптовые условия и цены (B2B / Опт)", {
            "fields": (
                "wholesale_price_display",
                "wholesale_price_numeric",
                "wholesale_min_qty",
            ),
            "description": "Укажите оптовую стоимость (отображение и число для фильтров) и минимальный объем оптового заказа."
        }),
        ("Характеристики (Сибсыр)", {
            "fields": ("fat_content", "package_type", "unit_weight", "shelf_life")
        }),
        ("Детальное описание и состав (Страница товара)", {
            "fields": (
                "full_description",
                "composition",
                "nutritional_value",
                "storage_conditions",
                "standard",
                "cooking_tips",
                "rating",
                "reviews_count"
            ),
            "description": "Полноценные данные для отдельной страницы товара, поисковых систем и соцсетей."
        }),
        ("Изображение и верстка", {
            "fields": ("image", "static_fallback_image", "card_style")
        }),
        ("Поисковая оптимизация (SEO)", {
            "fields": (
                "meta_title",
                "meta_description",
                "meta_keywords",
                "canonical_url",
            ),
            "description": "Поисковые мета-теги и канонический адрес для поисковиков Яндекс и Google. Генерируются автоматически при создании или если оставить пустыми."
        }),
        ("Отображение и статус", {
            "fields": ("order", "is_featured", "is_active")
        }),
    )

    def image_preview(self, obj):
        url = obj.image_url
        if url:
            return format_html(
                '<img src="{}" class="admin-product-thumb" alt="" />',
                url
            )
        return "—"
    image_preview.short_description = "Фото"

    def wholesale_display(self, obj):
        if obj.effective_wholesale_price_display:
            min_q = f"<br><span style='color: #64748b; font-size: 10px; font-weight: normal;'>{obj.wholesale_min_qty}</span>" if obj.wholesale_min_qty else ""
            return format_html(
                '<span style="color: #15803d; font-weight: 700; font-size: 12px; background: #f0fdf4; padding: 2px 7px; border-radius: 4px; border: 1px solid #bbf7d0; display: inline-block; line-height: 1.3;">{}'
                '{}'
                '</span>',
                obj.effective_wholesale_price_display,
                mark_safe(min_q)
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px;">Не указана</span>')
    wholesale_display.short_description = "Оптовая цена"

    def discount_info(self, obj):
        if obj.has_discount:
            old = obj.effective_old_price_numeric
            cur = obj.effective_price_numeric
            badge = obj.effective_badge
            return format_html(
                '<span style="background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;">'
                '<s>{} ₽</s> ➔ {} ₽ ({})'
                '</span>',
                old, cur, badge
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px;">Без скидки</span>')
    discount_info.short_description = "Акция / Скидка"

    def badge_tag(self, obj):
        if not obj.badge:
            return "-"
        return format_html(
            '<span style="background-color: #ff8400; color: white; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            obj.badge
        )
    badge_tag.short_description = "Метка"

    actions = [
        "generate_seo_selected",
        "make_featured", 
        "make_unfeatured", 
        "make_active", 
        "make_inactive", 
        "apply_discount_10", 
        "apply_discount_15", 
        "clear_discounts"
    ]

    @admin.action(description="⚡ Сгенерировать SEO-теги для выбранных товаров")
    def generate_seo_selected(self, request, queryset):
        count = 0
        for prod in queryset:
            prod.generate_seo(overwrite=True)
            prod.save()
            count += 1
        self.message_user(request, f"SEO-теги успешно сгенерированы для {count} товаров.")

    @admin.action(description="Поместить выбранные товары на главную")
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Убрать выбранные товары с главной")
    def make_unfeatured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description="Сделать выбранные товары активными (в наличии)")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Снять выбранные товары с продажи (неактивны)")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Установить скидку 10%% на выбранные товары")
    def apply_discount_10(self, request, queryset):
        for prod in queryset:
            if prod.price_numeric > 0 and not prod.old_price_numeric:
                prod.old_price_numeric = prod.price_numeric
            prod.discount_percent = 10
            prod.save()

    @admin.action(description="Установить скидку 15%% на выбранные товары")
    def apply_discount_15(self, request, queryset):
        for prod in queryset:
            if prod.price_numeric > 0 and not prod.old_price_numeric:
                prod.old_price_numeric = prod.price_numeric
            prod.discount_percent = 15
            prod.save()

    @admin.action(description="Сбросить индивидуальные скидки с выбранных товаров")
    def clear_discounts(self, request, queryset):
        queryset.update(discount_percent=0, old_price_numeric=0)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "title", "unit", "quantity", "price", "item_total")
    readonly_fields = ("item_total",)

    def item_total(self, obj):
        if obj.id:
            val = f"{obj.total:,.2f} ₽".replace(",", " ")
            return format_html('<strong style="color: #0f172a; font-size: 13px; white-space: nowrap;">{}</strong>', val)
        return "—"
    item_total.short_description = "Сумма"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number_badge",
        "customer_card",
        "phone_display",
        "items_summary",
        "amount_and_discount",
        "payment_badge",
        "status_colored",
        "print_actions_buttons",
        "created_at_formatted",
    )
    list_display_links = ("order_number_badge", "customer_card")
    list_filter = ("customer_type", "status", "is_paid", "payment_method", "created_at")
    search_fields = (
        "id", "name", "phone", "email", "company_name", "inn", "kpp", "legal_address", "delivery_address", "promocode_code"
    )
    readonly_fields = ("created_at", "updated_at", "order_token", "document_links_preview")
    inlines = [OrderItemInline]

    raw_id_fields = ("user", "promocode")

    fieldsets = (
        ("Документы и быстрая печать", {
            "fields": ("document_links_preview",)
        }),
        ("Статус и параметры заказа", {
            "fields": (
                ("status", "customer_type"),
                ("payment_method", "is_paid"),
                ("subtotal_price", "discount_amount", "total_price"),
                ("promocode", "promocode_code"),
                "user",
            )
        }),
        ("Контактная информация покупателя", {
            "fields": (
                ("name", "phone"),
                ("email", "delivery_address"),
            )
        }),
        ("Реквизиты Юридического лица / ИП (для ТОРГ-12 и счетов)", {
            "classes": ("collapse",),
            "description": "Заполняется для организаций и индивидуальных предпринимателей для автоматического формирования ТОРГ-12 и счетов",
            "fields": (
                ("company_name", "inn"),
                ("kpp", "ogrn"),
                "legal_address",
                ("bank_name", "bik"),
                ("account_number", "corr_account"),
            )
        }),
        ("Состав заказа и комментарии", {
            "fields": (
                "comment",
                "product_choice",
            )
        }),
        ("Служебная информация", {
            "classes": ("collapse",),
            "fields": (
                ("created_at", "updated_at"),
                "order_token",
            )
        }),
    )

    def order_number_badge(self, obj):
        return format_html(
            '<span class="order-id-badge" style="display: inline-block; background: var(--admin-card-header, #1e293b); color: var(--admin-text-title, #f8fafc); border: 1px solid var(--admin-border-color, #334155); padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 12px; letter-spacing: 0.5px; box-shadow: 0 1px 3px rgba(0,0,0,0.15);">#{}</span>',
            obj.id
        )
    order_number_badge.short_description = "№ Заказа"

    def customer_card(self, obj):
        if obj.is_legal:
            company = obj.company_name or "Без названия компании"
            contact = obj.name or "Контакт не указан"
            inn_info = f'<span style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 11px; white-space: nowrap;">ИНН {obj.inn}</span>' if obj.inn else ""
            kpp_info = f'<span style="background: var(--admin-card-header, #1e293b); color: var(--admin-text-muted, #94a3b8); border: 1px solid var(--admin-border-color, #334155); padding: 1px 5px; border-radius: 4px; font-size: 10px; white-space: nowrap;">КПП {obj.kpp}</span>' if obj.kpp else ""
            
            return format_html(
                '<div style="min-width: 170px;">'
                '<div style="display: flex; align-items: center; gap: 6px;">'
                '<span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">🏢 ЮР. ЛИЦО</span>'
                '<strong style="color: var(--admin-text-title, #f8fafc); font-size: 13px;">{}</strong>'
                '</div>'
                '<div style="font-size: 11px; color: var(--admin-text-muted, #94a3b8); margin-top: 4px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">'
                '{} {} <span style="color: var(--admin-text-light, #64748b);">•</span> 👤 <span style="color: var(--admin-text-main, #e2e8f0);">{}</span>'
                '</div>'
                '</div>',
                company, mark_safe(inn_info), mark_safe(kpp_info), contact
            )
        
        name = obj.name or "Покупатель без имени"
        return format_html(
            '<div style="min-width: 150px;">'
            '<div style="display: flex; align-items: center; gap: 6px;">'
            '<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">👤 ФИЗ. ЛИЦО</span>'
            '<strong style="color: var(--admin-text-title, #f8fafc); font-size: 13px;">{}</strong>'
            '</div>'
            '</div>',
            name
        )
    customer_card.short_description = "Покупатель / Организация"

    def phone_display(self, obj):
        if not obj.phone:
            return mark_safe('<span style="color: var(--admin-text-muted, #94a3b8); font-size: 11px;">—</span>')
        clean_phone = "".join(c for c in obj.phone if c.isdigit() or c == "+")
        return format_html(
            '<a href="tel:{}" class="order-phone-link" style="color: #38bdf8 !important; font-weight: 600; font-size: 12px; text-decoration: none !important; display: inline-flex; align-items: center; gap: 4px; white-space: nowrap;" title="Позвонить клиенту">'
            '<i class="bi bi-telephone-fill" style="color: #38bdf8 !important; font-size: 11px;"></i>{}'
            '</a>',
            clean_phone, obj.phone
        )
    phone_display.short_description = "Телефон"

    def items_summary(self, obj):
        items = list(obj.items.all())
        count = len(items)
        if count > 0:
            names = ", ".join(f"{it.title} ({it.quantity} {it.unit})" for it in items[:3])
            if count > 3:
                names += f" и еще {count - 3}..."
            return format_html(
                '<div style="min-width: 140px; max-width: 260px;" title="{}">'
                '<span style="background: var(--admin-card-header, #1e293b); color: var(--admin-text-title, #f8fafc); border: 1px solid var(--admin-border-color, #334155); font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 4px;">{} поз.</span>'
                '<span style="color: var(--admin-text-muted, #94a3b8); font-size: 11px; line-height: 1.3;">{}</span>'
                '</div>',
                names, count, names
            )
        
        fallback = obj.product_choice or "Без позиций"
        return format_html(
            '<div style="min-width: 120px; max-width: 220px; color: var(--admin-text-muted, #94a3b8); font-size: 11px;" title="{}">{}</div>',
            fallback, fallback[:45] + ("..." if len(fallback) > 45 else "")
        )
    items_summary.short_description = "Состав заказа"

    def amount_and_discount(self, obj):
        total = f"{obj.total_price:,.2f} ₽".replace(",", " ")
        if obj.discount_amount > 0:
            subtotal = f"{obj.subtotal_price:,.2f} ₽".replace(",", " ")
            discount = f"{obj.discount_amount:,.2f} ₽".replace(",", " ")
            promo_tag = f" ({obj.promocode_code})" if obj.promocode_code else ""
            return format_html(
                '<div style="white-space: nowrap;">'
                '<div style="font-weight: 800; font-size: 13px; color: var(--admin-text-title, #f8fafc);">{}</div>'
                '<div style="font-size: 11px; color: #4ade80; font-weight: 600; margin-top: 2px;">'
                '<s>{}</s> <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 1px 4px; border-radius: 3px;">-{}</span>{}'
                '</div>'
                '</div>',
                total, subtotal, discount, promo_tag
            )
        return format_html('<span style="font-weight: 800; font-size: 13px; color: var(--admin-text-title, #f8fafc); white-space: nowrap;">{}</span>', total)
    amount_and_discount.short_description = "Сумма заказа"

    def payment_badge(self, obj):
        method_name = obj.get_payment_method_display()
        if obj.is_paid:
            return format_html(
                '<div style="white-space: nowrap;">'
                '<span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">'
                '✅ Оплачен'
                '</span>'
                '<div style="color: var(--admin-text-muted, #94a3b8); font-size: 10px; margin-top: 2px;">{}</div>'
                '</div>',
                method_name
            )
        
        is_invoice = (obj.payment_method == "invoice")
        bg = "rgba(245, 158, 11, 0.15)" if is_invoice else "rgba(239, 68, 68, 0.15)"
        color = "#fbbf24" if is_invoice else "#f87171"
        border = "rgba(245, 158, 11, 0.3)" if is_invoice else "rgba(239, 68, 68, 0.3)"
        status_text = "⏳ Ожидает оплаты" if is_invoice else "Не оплачен"

        return format_html(
            '<div style="white-space: nowrap;">'
            '<span style="display: inline-flex; align-items: center; gap: 4px; background: {}; color: {}; border: 1px solid {}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px;">'
            '{}'
            '</span>'
            '<div style="color: var(--admin-text-muted, #94a3b8); font-size: 10px; margin-top: 2px;">{}</div>'
            '</div>',
            bg, color, border, status_text, method_name
        )
    payment_badge.short_description = "Оплата"

    def status_colored(self, obj):
        configs = {
            "new": ("rgba(245, 158, 11, 0.15)", "#fbbf24", "rgba(245, 158, 11, 0.3)", "bi-bell-fill"),
            "processing": ("rgba(14, 165, 233, 0.15)", "#38bdf8", "rgba(14, 165, 233, 0.3)", "bi-arrow-repeat"),
            "confirmed": ("rgba(139, 92, 246, 0.15)", "#a78bfa", "rgba(139, 92, 246, 0.3)", "bi-check2-all"),
            "shipped": ("rgba(59, 130, 246, 0.15)", "#60a5fa", "rgba(59, 130, 246, 0.3)", "bi-truck"),
            "completed": ("rgba(16, 185, 129, 0.15)", "#34d399", "rgba(16, 185, 129, 0.3)", "bi-patch-check-fill"),
            "cancelled": ("rgba(239, 68, 68, 0.15)", "#f87171", "rgba(239, 68, 68, 0.3)", "bi-x-circle"),
        }
        bg, text, border, icon = configs.get(obj.status, ("rgba(100, 116, 139, 0.15)", "#94a3b8", "rgba(100, 116, 139, 0.3)", "bi-circle"))
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 4px; background-color: {}; color: {}; border: 1px solid {}; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; white-space: nowrap;">'
            '<i class="bi {}" style="font-size: 11px;"></i> {}'
            '</span>',
            bg, text, border, icon, obj.get_status_display()
        )
    status_colored.short_description = "Статус"

    def print_actions_buttons(self, obj):
        receipt_url = reverse("shop:order_receipt", args=[obj.id])
        waybill_url = reverse("shop:order_waybill", args=[obj.id])
        torg12_url = reverse("shop:order_torg12", args=[obj.id])
        bill_url = reverse("shop:order_bill", args=[obj.id])

        return format_html(
            '<div class="order-doc-grid">'
            '<a href="{}" target="_blank" class="order-doc-btn btn-receipt" title="Товарный / кассовый чек">'
            '<i class="bi bi-receipt"></i><span>Чек</span>'
            '</a>'
            '<a href="{}" target="_blank" class="order-doc-btn btn-waybill" title="Расходная товарная накладная">'
            '<i class="bi bi-card-checklist"></i><span>Накладная</span>'
            '</a>'
            '<a href="{}" target="_blank" class="order-doc-btn btn-torg12" title="Унифицированная форма ТОРГ-12 (для организаций и ИП)">'
            '<i class="bi bi-building"></i><span>ТОРГ-12</span>'
            '</a>'
            '<a href="{}" target="_blank" class="order-doc-btn btn-bill" title="Счет на безналичную оплату">'
            '<i class="bi bi-wallet2"></i><span>Счет</span>'
            '</a>'
            '</div>',
            receipt_url,
            waybill_url,
            torg12_url,
            bill_url,
        )
    print_actions_buttons.short_description = "Печать документов"

    def created_at_formatted(self, obj):
        if not obj.created_at:
            return "—"
        date_str = obj.created_at.strftime("%d.%m.%Y")
        time_str = obj.created_at.strftime("%H:%M")
        return format_html(
            '<div style="white-space: nowrap; font-size: 12px; color: var(--admin-text-main, #e2e8f0);">'
            '<span style="font-weight: 600;">{}</span> '
            '<span style="color: var(--admin-text-muted, #94a3b8); font-size: 11px;">{}</span>'
            '</div>',
            date_str, time_str
        )
    created_at_formatted.short_description = "Дата оформления"
    created_at_formatted.admin_order_field = "created_at"

    def document_links_preview(self, obj):
        if not obj.id:
            return mark_safe(
                '<div style="background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412; padding: 12px 16px; border-radius: 8px; font-weight: 600;">'
                'ℹ️ Сохраните новый заказ, чтобы сформировать и распечатать документы (товарный чек, накладную, ТОРГ-12, счет).'
                '</div>'
            )
        
        receipt_url = reverse("shop:order_receipt", args=[obj.id])
        waybill_url = reverse("shop:order_waybill", args=[obj.id])
        torg12_url = reverse("shop:order_torg12", args=[obj.id])
        bill_url = reverse("shop:order_bill", args=[obj.id])

        total_fmt = f"{obj.total_price:,.2f} ₽".replace(",", " ")
        subtotal_fmt = f"{obj.subtotal_price:,.2f} ₽".replace(",", " ")
        discount_fmt = f"{obj.discount_amount:,.2f} ₽".replace(",", " ") if obj.discount_amount > 0 else ""

        client_type = "Юридическое лицо / ИП" if obj.is_legal else "Физическое лицо"
        client_name = obj.customer_display_title

        status_name = obj.get_status_display()
        pay_status = "Оплачен" if obj.is_paid else f"Ожидает оплаты ({obj.get_payment_method_display()})"
        pay_class = "pay-paid" if obj.is_paid else "pay-pending"
        client_type = "Юр. лицо / ИП" if obj.customer_type == "legal" else "Физическое лицо"
        client_name = obj.company_name if obj.customer_type == "legal" and obj.company_name else (obj.name or "Гость")
        total_fmt = f"{obj.total_price:,.2f} ₽".replace(",", " ")
        subtotal_fmt = f"{obj.subtotal_price:,.2f} ₽".replace(",", " ")
        discount_fmt = f"{obj.discount_amount:,.2f} ₽".replace(",", " ") if obj.discount_amount > 0 else ""

        discount_html = ""
        if discount_fmt:
            discount_html = f'<div class="order-summary-discount">Скидка: -{discount_fmt} (базовая сумма {subtotal_fmt})</div>'

        return format_html(
            '''
            <div class="order-summary-card">
                <div class="order-summary-header">
                    <div>
                        <div class="order-summary-title-row">
                            <h3 class="order-summary-title">Заказ #{}</h3>
                            <span class="order-summary-badge badge-status">{}</span>
                            <span class="order-summary-badge {}">{}</span>
                            <span class="order-summary-badge badge-client">{}</span>
                        </div>
                        <div class="order-summary-buyer-info">
                            Покупатель: <strong>{}</strong>
                            <span class="order-summary-dot">•</span>
                            Телефон: <strong>{}</strong>
                        </div>
                    </div>
                    <div class="order-summary-total-box">
                        <div class="order-summary-total-label">Итого к оплате</div>
                        <div class="order-summary-total-val">{}</div>
                        {}
                    </div>
                </div>

                <div class="order-summary-actions">
                    <div class="order-summary-actions-label">
                        <i class="bi bi-printer-fill"></i> Документы для быстрой печати:
                    </div>
                    <div class="order-summary-buttons">
                        <a href="{}" target="_blank" class="order-doc-btn btn-receipt">
                            <i class="bi bi-receipt"></i><span>Товарный чек</span>
                        </a>
                        <a href="{}" target="_blank" class="order-doc-btn btn-waybill">
                            <i class="bi bi-card-checklist"></i><span>Накладная (Физ. лицо)</span>
                        </a>
                        <a href="{}" target="_blank" class="order-doc-btn btn-torg12">
                            <i class="bi bi-building"></i><span>ТОРГ-12 (Юр. лицо / ИП)</span>
                        </a>
                        <a href="{}" target="_blank" class="order-doc-btn btn-bill">
                            <i class="bi bi-cash-stack"></i><span>Счет на безналичную оплату</span>
                        </a>
                    </div>
                </div>
            </div>
            ''',
            obj.id, status_name, pay_class, pay_status, client_type,
            client_name, obj.phone or "—", total_fmt, mark_safe(discount_html),
            receipt_url, waybill_url, torg12_url, bill_url
        )
    document_links_preview.short_description = "Сводка заказа и печать документов"

    actions = ["mark_processing", "mark_completed", "mark_paid", "mark_cancelled"]

    @admin.action(description="Перевести в статус «В обработке»")
    def mark_processing(self, request, queryset):
        queryset.update(status="processing")

    @admin.action(description="Перевести в статус «Выполнен»")
    def mark_completed(self, request, queryset):
        queryset.update(status="completed")

    @admin.action(description="Отметить выбранные заказы как ОПЛАЧЕННЫЕ")
    def mark_paid(self, request, queryset):
        queryset.update(is_paid=True)

    @admin.action(description="Отменить выбранные заказы")
    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author_name", "product_display", "city", "rating_stars", "is_approved", "created_at")
    list_display_links = ("author_name",)
    list_editable = ("is_approved",)
    list_filter = ("is_approved", "rating", "created_at", "product")
    search_fields = ("author_name", "city", "text", "product_mention", "product__title")
    autocomplete_fields = ("product",)
    raw_id_fields = ("user",)
    date_hierarchy = "created_at"

    def product_display(self, obj):
        if obj.product:
            url = reverse("admin:shop_product_change", args=[obj.product.pk])
            return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.product.title)
        return obj.product_mention or "—"
    product_display.short_description = "Товар"

    def rating_stars(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html('<span style="color: #ff8400; font-size: 1.1rem;">{}</span>', stars)
    rating_stars.short_description = "Оценка"
