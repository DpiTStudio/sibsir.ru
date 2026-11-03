from django.contrib import admin
from django.utils.html import format_html
from main.admin_mixins import RichTextAdminMixin
from .models import Article


@admin.register(Article)
class ArticleAdmin(RichTextAdminMixin, admin.ModelAdmin):
    rich_text_fields = ("content",)
    list_display = ("order", "image_thumbnail", "title", "date_str", "views_count", "is_published", "created_at")
    list_display_links = ("title",)
    list_editable = ("order", "is_published", "views_count")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "snippet", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Статья", {
            "fields": ("title", "slug", "date_str", "snippet", "content")
        }),
        ("Изображение и параметры", {
            "fields": ("image", "views_count", "order", "is_published", "created_at")
        }),
        ("Поисковая оптимизация (SEO)", {
            "fields": ("meta_title", "meta_description", "meta_keywords"),
            "description": "Поисковые мета-теги для статьи в Яндекс и Google. Генерируются автоматически на основе заголовка и краткого описания."
        }),
    )

    actions = ["generate_seo_selected", "make_published", "make_unpublished"]

    @admin.action(description="⚡ Сгенерировать SEO-теги для выбранных статей")
    def generate_seo_selected(self, request, queryset):
        count = 0
        for article in queryset:
            article.generate_seo(overwrite=True)
            article.save()
            count += 1
        self.message_user(request, f"SEO-теги успешно сгенерированы для {count} статей.")

    @admin.action(description="Опубликовать выбранные статьи")
    def make_published(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f"Опубликовано статей: {count}.")

    @admin.action(description="Снять с публикации выбранные статьи")
    def make_unpublished(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f"Снято с публикации статей: {count}.")

    def image_thumbnail(self, obj):
        url = obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 35px; object-fit: cover; border-radius: 4px;" />',
                url
            )
        return "-"
    image_thumbnail.short_description = "Превью"
