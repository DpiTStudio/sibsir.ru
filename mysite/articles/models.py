from django.db import models
from django.templatetags.static import static
from tinymce.models import HTMLField


class Article(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок статьи")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Слаг (URL)")
    date_str = models.CharField(max_length=50, default="24.07.2025", verbose_name="Отображаемая дата")
    snippet = models.TextField(verbose_name="Краткий анонс статьи")
    content = HTMLField(verbose_name="Полный текст (HTML / абзацы)")
    image = models.ImageField(upload_to="articles/", blank=True, null=True, verbose_name="Изображение статьи")
    views_count = models.PositiveIntegerField(default=120, verbose_name="Просмотры")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # SEO поля
    meta_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Заголовок (Meta Title)",
        help_text="Если пусто, создается автоматически: «Заголовок — Блог сыроварни Сибсыр»"
    )
    meta_description = models.TextField(
        blank=True, 
        verbose_name="SEO Описание (Meta Description)",
        help_text="Сниппет для поисковых систем (140-180 символов). Если пусто, создается из анонса статьи"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Ключевые слова (Keywords)",
        help_text="Через запятую. Если пусто, создается автоматически"
    )

    class Meta:
        verbose_name = "Статья о сыре"
        verbose_name_plural = "Статьи и полезные материалы"
        ordering = ["order", "-id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        if self.slug:
            return reverse("main:article_detail", kwargs={"slug": self.slug})
        return reverse("main:articles")

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return static("images/hero_cheese.jpg")

    def generate_seo(self, overwrite=False):
        """Автоматическая генерация SEO-тегов для статьи."""
        import re
        title = self.title.strip()
        if not self.meta_title or overwrite:
            gen_title = f"{title} — Блог сыроварни «Сибсыр»"
            self.meta_title = gen_title[:250]

        if not self.meta_description or overwrite:
            raw_text = self.snippet or self.content or ""
            clean_snippet = re.sub(r'<[^>]+>', '', raw_text).replace('&nbsp;', ' ').strip()
            if clean_snippet:
                words = clean_snippet.split()
                clean_snippet = " ".join(words[:20])
                if not clean_snippet.endswith('.'):
                    clean_snippet += "."
            else:
                clean_snippet = "Полезный материал о сыроделии, культуре употребления сыров и рецептах."
            
            gen_desc = f"{clean_snippet} Читайте полезные статьи и советы сыроделов на официальном сайте ТМ «Сибсыр»."
            self.meta_description = gen_desc[:280]

        if not self.meta_keywords or overwrite:
            clean_title = title.lower()
            kw_list = [clean_title, "статьи о сыре", "сибсыр", "сыроварня омск", "производство сыра", "сыр рецепты", "сыроделие", "натуральные сыры"]
            self.meta_keywords = ", ".join(dict.fromkeys(kw_list))[:250]

        if overwrite and self.pk:
            self.save(update_fields=["meta_title", "meta_description", "meta_keywords"])

    def get_meta_title(self):
        if self.meta_title:
            return self.meta_title
        return f"{self.title} — Блог сыроварни «Сибсыр»"

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        if self.snippet:
            import re
            clean = re.sub(r'<[^>]+>', '', self.snippet).replace('&nbsp;', ' ').strip()
            return f"{clean[:150]}... ТМ «Сибсыр»."
        return f"{self.title} — читайте статью экспертов сыродельного производства ТМ «Сибсыр»."

    def get_meta_keywords(self):
        if self.meta_keywords:
            return self.meta_keywords
        return f"{self.title.lower()}, статьи о сыре, сибсыр, блог сыродела"

    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description or not self.meta_keywords:
            self.generate_seo(overwrite=False)
        super().save(*args, **kwargs)
