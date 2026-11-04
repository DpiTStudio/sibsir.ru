from decimal import Decimal
from django.db import models
from django.conf import settings
from django.templatetags.static import static


class Category(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название категории")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Слаг (URL-идентификатор)")
    description = models.TextField(blank=True, verbose_name="Описание категории")
    image = models.ImageField(
        upload_to="categories/", 
        blank=True, 
        null=True, 
        verbose_name="Изображение / баннер категории"
    )
    icon = models.CharField(
        max_length=60, 
        default="bi-grid-fill", 
        blank=True, 
        verbose_name="Иконка Bootstrap"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    # SEO поля
    meta_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Заголовок (Meta Title)",
        help_text="Если не заполнено, будет создано автоматически"
    )
    meta_description = models.TextField(
        blank=True, 
        verbose_name="SEO Описание (Meta Description)",
        help_text="Краткое описание для поисковиков (сниппет Яндекса и Google). Если пусто, создается автоматически"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Ключевые слова (Keywords)",
        help_text="Через запятую. Если пусто, создается автоматически"
    )
    seo_text = models.TextField(
        blank=True, 
        verbose_name="SEO-текст категории (для продвижения)",
        help_text="Подробный текст с описанием категории для поисковых систем (отображается внизу страницы каталога)"
    )

    class Meta:
        verbose_name = "Категория продукции"
        verbose_name_plural = "Категории продукции"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def generate_seo(self, overwrite=False):
        """Автоматическая генерация SEO-тегов для категории."""
        import re
        name = self.name.strip()
        if not self.meta_title or overwrite:
            gen_title = f"{name} — купить от производителя ТМ «Сибсыр» в Омске | Каталог"
            self.meta_title = gen_title[:250]

        if not self.meta_description or overwrite:
            desc_snippet = (self.description or "").strip()
            if desc_snippet:
                desc_snippet = re.sub(r'<[^>]+>', '', desc_snippet).replace('&nbsp;', ' ').strip()
                if len(desc_snippet) > 100:
                    desc_snippet = desc_snippet[:97] + "..."
                self.meta_description = f"Каталог {name} от завода ТМ «Сибсыр» в Омске. {desc_snippet} Натуральное молоко ГОСТ, оптовые и розничные поставки по всей России."
            else:
                self.meta_description = f"Каталог {name} от сыродельного завода ТМ «Сибсыр» в Омске. 100% натуральное отборное молоко, стандарты ГОСТ, оптовые и розничные поставки по всей России."

        if not self.meta_keywords or overwrite:
            clean_name = name.lower()
            self.meta_keywords = f"{clean_name}, {clean_name} омск, купить {clean_name} оптом, сыры сибсыр, сыродельный завод омск, натуральная молочная продукция"[:250]

        if overwrite and self.pk:
            self.save(update_fields=["meta_title", "meta_description", "meta_keywords"])

    def get_meta_title(self):
        if self.meta_title:
            return self.meta_title
        return f"{self.name} — купить от производителя ТМ «Сибсыр» в Омске | Каталог"

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        return f"Каталог {self.name} от сыродельного завода ТМ «Сибсыр» в Омске. 100% натуральное молоко, стандарты ГОСТ, оптовые и розничные поставки по всей России."

    def get_meta_keywords(self):
        if self.meta_keywords:
            return self.meta_keywords
        return f"{self.name.lower()}, сыры омск, купить сыр оптом, сибсыр, молочная продукция омск"

    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description or not self.meta_keywords:
            self.generate_seo(overwrite=False)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.image and hasattr(self.image, "url"):
            return self.image.url
        first_prod = self.products.filter(is_active=True).exclude(image="").first()
        if first_prod and first_prod.image:
            return first_prod.image.url
        return static("images/hero_cheese.jpg")

    def get_active_promotion(self):
        """Возвращает активную акцию для этой категории (или каталога)."""
        from django.utils import timezone
        now = timezone.now()
        return self.promotions.filter(
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).first()

    @property
    def has_discount(self):
        return self.get_active_promotion() is not None


class Product(models.Model):
    CARD_STYLE_CHOICES = [
        ("standard", "Стандартная вертикальная карточка"),
        ("split", "Широкая карточка (Split layout)"),
    ]

    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="products", 
        verbose_name="Категория"
    )
    title = models.CharField(max_length=200, verbose_name="Наименование продукции")
    slug = models.SlugField(max_length=200, blank=True, verbose_name="Слаг (URL)")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Цены
    price_display = models.CharField(
        max_length=100, 
        default="По запросу", 
        verbose_name="Отображение цены",
        help_text="Например: '410 ₽' или 'По запросу'"
    )
    price_numeric = models.PositiveIntegerField(
        default=0, 
        verbose_name="Числовая цена (для сортировки и фильтра)", 
        help_text="В рублях, 0 = по запросу"
    )
    old_price_numeric = models.PositiveIntegerField(
        default=0, 
        verbose_name="Старая цена (без скидки), ₽", 
        help_text="Если указана, отображается зачеркнутой (например: 490)"
    )
    discount_percent = models.PositiveIntegerField(
        default=0, 
        verbose_name="Прямая скидка на товар (%)", 
        help_text="Процент прямой скидки на товар (например: 10 или 15)"
    )
    wholesale_price_display = models.CharField(
        max_length=100, 
        blank=True, 
        default="", 
        verbose_name="Оптовая цена (отображение)", 
        help_text="Например: '340 ₽' или 'По запросу'"
    )
    wholesale_price_numeric = models.PositiveIntegerField(
        default=0, 
        verbose_name="Оптовая цена (число, ₽)", 
        help_text="В рублях, 0 = по запросу или не указана"
    )
    wholesale_min_qty = models.CharField(
        max_length=100, 
        blank=True, 
        default="от 10 шт.", 
        verbose_name="Условие оптовой цены", 
        help_text="Например: 'от 10 шт.', 'от 1 коробки', 'от 5 кг'"
    )
    
    # Характеристики продукта (Сибсыр)
    fat_content = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Массовая доля жира (м.д.ж.)",
        help_text="Например: 45%, 72,5%, 20%"
    )
    package_type = models.CharField(
        max_length=150, 
        blank=True, 
        verbose_name="Тип упаковки",
        help_text="Например: Пленка | вакуум, Пакет, Стакан, Ванна"
    )
    unit_weight = models.CharField(
        max_length=150, 
        blank=True, 
        verbose_name="Вес / фасовка",
        help_text="Например: 2,2 | 0,6 кг, 180 гр, 400 гр, 1 кг"
    )
    shelf_life = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Срок годности",
        help_text="Например: 35 суток, 120 суток"
    )

    # Дополнительные данные для страницы товара
    full_description = models.TextField(
        blank=True,
        verbose_name="Подробное описание (для страницы товара)",
        help_text="Развернутый рассказ о продукте: органолептика, традиция приготовления, вкусовой профиль"
    )
    composition = models.TextField(
        blank=True,
        verbose_name="Состав продукта",
        help_text="Ингредиенты: отборное молоко, живая закваска, сычужный фермент, соль и т.д."
    )
    nutritional_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Пищевая ценность (на 100 г)",
        help_text="Например: Белки 19.5 г, Жиры 22.0 г, Углеводы 0 г. Энергетическая ценность: 276 ккал"
    )
    storage_conditions = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Условия хранения",
        help_text="Например: Хранить при температуре от 0°C до +6°C и относительной влажности не более 85%"
    )
    standard = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Стандарт качества (ГОСТ / ТУ)",
        help_text="Например: ГОСТ 32260-2013 или ТУ 10.51.40-001"
    )
    cooking_tips = models.TextField(
        blank=True,
        verbose_name="Кулинарные советы и гастрономические пары",
        help_text="С чем подавать: сырная тарелка, выпечка, хачапури, сочетание с вином, кофе или медом"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("4.9"),
        verbose_name="Рейтинг товара"
    )
    reviews_count = models.PositiveIntegerField(
        default=14,
        verbose_name="Количество отзывов"
    )

    image = models.ImageField(
        upload_to="products/", 
        blank=True, 
        null=True, 
        verbose_name="Загруженное фото"
    )
    static_fallback_image = models.CharField(
        max_length=100, 
        blank=True, 
        default="", 
        verbose_name="Статическое фото по умолчанию"
    )
    badge = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Бейдж / Метка",
        help_text="Например: Хит, Новинка, Популярное, Выбор покупателей"
    )
    card_style = models.CharField(
        max_length=20, 
        choices=CARD_STYLE_CHOICES, 
        default="standard", 
        verbose_name="Стиль карточки"
    )
    button_text = models.CharField(
        max_length=50, 
        default="Заказать", 
        verbose_name="Текст кнопки"
    )
    is_featured = models.BooleanField(
        default=True, 
        verbose_name="Отображать на главной"
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="Порядок сортировки"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="В наличии (активен)"
    )

    # SEO поля
    meta_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Заголовок (Meta Title)",
        help_text="Если пусто, сгенерируется автоматически: «Название — купить в Омске по цене... | ТМ Сибсыр»"
    )
    meta_description = models.TextField(
        blank=True, 
        verbose_name="SEO Описание (Meta Description)",
        help_text="Сниппет для поиска Яндекса и Google (140-180 символов). Если пусто, создается автоматически"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Ключевые слова (Keywords)",
        help_text="Через запятую. Если пусто, создается автоматически"
    )
    canonical_url = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Канонический URL (Canonical)",
        help_text="Оставьте пустым для автоопределения адреса карточки товара"
    )

    class Meta:
        verbose_name = "Товар / Продукт"
        verbose_name_plural = "Каталог продукции"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({self.price_display})"

    def get_absolute_url(self):
        from django.urls import reverse
        if self.slug:
            return reverse("main:product_detail", kwargs={"slug": self.slug})
        return reverse("main:catalog")

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        if self.static_fallback_image:
            return static(self.static_fallback_image)
        return static("images/hero_cheese.jpg")

    def get_active_promotion(self):
        """
        Ищет активную акцию для товара:
        1. Персональная акция на данный товар.
        2. Акция на категорию (каталог), к которой принадлежит товар.
        3. Общая акция на весь каталог продукции.
        """
        from django.utils import timezone
        now = timezone.now()

        # 1. Точечная акция на товар
        p_promo = self.promotions.filter(
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).first()
        if p_promo:
            return p_promo

        # 2. Акция на категорию / каталог
        if self.category_id:
            c_promo = self.category.promotions.filter(
                is_active=True
            ).filter(
                models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
            ).first()
            if c_promo:
                return c_promo

        # 3. Акция на весь каталог (all)
        return Promotion.objects.filter(
            applies_to="all",
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).first()

    @property
    def has_discount(self):
        """Есть ли у товара скидка или активная акция."""
        if self.discount_percent > 0:
            return True
        if self.old_price_numeric > 0 and self.price_numeric > 0 and self.old_price_numeric > self.price_numeric:
            return True
        promo = self.get_active_promotion()
        if promo and (promo.discount_percent > 0 or promo.discount_amount > 0):
            return True
        return False

    @property
    def effective_price_numeric(self):
        """Вычисляет актуальную цену с учетом лучшей скидки (в рублях)."""
        base_price = self.price_numeric
        if base_price <= 0:
            return 0

        best_price = base_price
        if self.old_price_numeric > base_price and self.discount_percent == 0:
            best_price = base_price
        elif self.discount_percent > 0:
            best_price = int(round(base_price * (100 - self.discount_percent) / 100))

        promo = self.get_active_promotion()
        if promo:
            if promo.discount_percent > 0:
                promo_price = int(round(base_price * (100 - promo.discount_percent) / 100))
                best_price = min(best_price, promo_price)
            elif promo.discount_amount > 0:
                promo_price = max(0, int(base_price - promo.discount_amount))
                best_price = min(best_price, promo_price)

        return best_price

    @property
    def effective_old_price_numeric(self):
        """Возвращает старую цену (до скидки) для перечеркивания."""
        if self.old_price_numeric > 0:
            return self.old_price_numeric
        if self.has_discount and self.price_numeric > self.effective_price_numeric:
            return self.price_numeric
        return 0

    @property
    def effective_discount_percent(self):
        """Вычисляет процент скидки для бейджа."""
        if self.effective_old_price_numeric > self.effective_price_numeric > 0:
            diff = self.effective_old_price_numeric - self.effective_price_numeric
            return int(round((diff / self.effective_old_price_numeric) * 100))
        if self.discount_percent > 0:
            return self.discount_percent
        promo = self.get_active_promotion()
        if promo and promo.discount_percent > 0:
            return promo.discount_percent
        return 0

    @property
    def effective_badge(self):
        """Возвращает текст бейджа: явный бейдж, скидка '-15%' или название акции."""
        if self.badge:
            return self.badge
        pct = self.effective_discount_percent
        if pct > 0:
            return f"-{pct}%"
        promo = self.get_active_promotion()
        if promo and promo.badge_text:
            return promo.badge_text
        if self.has_discount:
            return "АКЦИЯ"
        return ""

    @property
    def effective_price_display(self):
        """Форматированное отображение актуальной цены с учетом скидки."""
        if self.has_discount and self.effective_price_numeric > 0:
            return f"{self.effective_price_numeric} ₽"
        return self.price_display

    @property
    def effective_wholesale_price_display(self):
        """Форматированное отображение оптовой цены."""
        if self.wholesale_price_display:
            return self.wholesale_price_display
        if self.wholesale_price_numeric > 0:
            return f"{self.wholesale_price_numeric} ₽"
        return ""

    def generate_seo(self, overwrite=False):
        """Автоматическая генерация оптимизированных SEO-тегов для товара."""
        import re
        title = self.title.strip()
        cat_name = self.category.name if self.category else "Сыры и молочная продукция"
        weight_part = f" {self.unit_weight}" if self.unit_weight else ""
        fat_part = f" {self.fat_content}" if self.fat_content else ""
        price_part = f", цена {self.effective_price_display}" if self.effective_price_display else ""

        if not self.meta_title or overwrite:
            gen_title = f"{title}{weight_part} — купить в Омске{price_part} | ТМ «Сибсыр»"
            self.meta_title = gen_title[:250]

        if not self.meta_description or overwrite:
            raw_text = self.description or self.full_description or ""
            clean_snippet = re.sub(r'<[^>]+>', '', raw_text).replace('&nbsp;', ' ').strip()
            if clean_snippet:
                words = clean_snippet.split()
                clean_snippet = " ".join(words[:18])
                if not clean_snippet.endswith('.'):
                    clean_snippet += "."
            else:
                clean_snippet = "Натуральная продукция от омского производителя ТМ «Сибсыр»."

            std_part = f" Стандарт качества: {self.standard}." if self.standard else ""
            gen_desc = f"Купить {title}{fat_part}{weight_part} от производителя ТМ «Сибсыр». {clean_snippet}{std_part} Доставка по Омску и всей России. Выгодные оптовые и розничные цены."
            self.meta_description = gen_desc[:280]

        if not self.meta_keywords or overwrite:
            clean_title = title.lower()
            cat_kw = cat_name.lower()
            kw_list = [clean_title, f"{clean_title} омск", f"купить {clean_title}", f"{clean_title} оптом", "сибсыр", cat_kw, "производитель сыра омск", "натуральный сыр"]
            if self.standard:
                kw_list.append(self.standard.lower())
            self.meta_keywords = ", ".join(dict.fromkeys(kw_list))[:250]

        if overwrite and self.pk:
            self.save(update_fields=["meta_title", "meta_description", "meta_keywords"])

    def get_meta_title(self):
        if self.meta_title:
            return self.meta_title
        weight_part = f" {self.unit_weight}" if self.unit_weight else ""
        return f"{self.title}{weight_part} — купить в Омске, цена {self.effective_price_display} | ТМ «Сибсыр»"

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        return f"{self.title}. Натуральная продукция от производителя ТМ «Сибсыр». Доставка по Омску и всей России. Выгодные цены для опта и розницы."

    def get_meta_keywords(self):
        if self.meta_keywords:
            return self.meta_keywords
        cat_name = self.category.name if self.category else ""
        return f"{self.title.lower()}, сыр омск, купить сыр, сибсыр, {cat_name.lower()}, оптовые поставки сыра"

    def get_canonical_url(self, request=None):
        if self.canonical_url:
            return self.canonical_url
        if request:
            return request.build_absolute_uri(self.get_absolute_url())
        return self.get_absolute_url()

    @property
    def approved_reviews(self):
        """Возвращает опубликованные отзывы именно к данному товару."""
        return self.reviews.filter(is_approved=True).order_by("-created_at")

    @property
    def dynamic_reviews_count(self):
        """
        Реальное количество опубликованных отзывов к товару.
        Если реальных отзывов пока нет, возвращает базовое значение reviews_count.
        """
        real_count = self.reviews.filter(is_approved=True).count()
        return real_count if real_count > 0 else self.reviews_count

    @property
    def dynamic_rating(self):
        """
        Средний рейтинг товара на основе опубликованных отзывов.
        Если реальных отзывов нет, возвращает базовый рейтинг.
        """
        approved = self.reviews.filter(is_approved=True)
        cnt = approved.count()
        if cnt > 0:
            avg = sum(r.rating for r in approved) / cnt
            return round(avg, 1)
        return float(self.rating) if self.rating else 4.9

    def update_rating_stats(self):
        """Пересчитывает рейтинг и количество отзывов на основе подтвержденных отзывов."""
        approved = self.reviews.filter(is_approved=True)
        cnt = approved.count()
        if cnt > 0:
            avg = sum(r.rating for r in approved) / cnt
            self.rating = Decimal(str(round(avg, 1)))
            self.reviews_count = cnt
            self.save(update_fields=["rating", "reviews_count"])

    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description or not self.meta_keywords:
            self.generate_seo(overwrite=False)
        super().save(*args, **kwargs)


import uuid
from decimal import Decimal
from .utils import amount_in_words, count_items_in_words


class Promotion(models.Model):
    APPLIES_CHOICES = [
        ("all", "Весь каталог продукции"),
        ("categories", "Выбранные категории (каталоги)"),
        ("products", "Отдельные товары"),
    ]

    title = models.CharField(max_length=200, verbose_name="Название акции")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Слаг (URL)")
    badge_text = models.CharField(
        max_length=50, 
        default="АКЦИЯ", 
        verbose_name="Текст бейджа",
        help_text="Например: АКЦИЯ, -15%, ВЫГОДА, СКИДКА ДНЯ"
    )
    description = models.TextField(blank=True, verbose_name="Описание и условия акции")
    discount_percent = models.PositiveIntegerField(
        default=0, 
        verbose_name="Скидка по акции (%)",
        help_text="Например, 15 означает скидку 15%"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Фиксированная скидка (₽)",
        help_text="Если указана, отнимается фиксированная сумма в рублях"
    )
    applies_to = models.CharField(
        max_length=20, 
        choices=APPLIES_CHOICES, 
        default="all", 
        verbose_name="Область действия"
    )
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name="promotions", 
        verbose_name="Категории товаров (каталоги)"
    )
    products = models.ManyToManyField(
        Product, 
        blank=True, 
        related_name="promotions", 
        verbose_name="Товары, участвующие в акции"
    )
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата и время начала")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата и время окончания")
    banner_image = models.ImageField(
        upload_to="promotions/", 
        blank=True, 
        null=True, 
        verbose_name="Баннер акции"
    )
    icon = models.CharField(
        max_length=60, 
        default="bi-tag-fill", 
        blank=True, 
        verbose_name="Иконка Bootstrap"
    )
    show_banner = models.BooleanField(
        default=True, 
        verbose_name="Отображать баннер акции на сайте"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Активна"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Акция / Скидочная кампания"
        verbose_name_plural = "Акции и скидки"
        ordering = ["order", "-id"]

    def __str__(self):
        val = f"{self.discount_percent}%" if self.discount_percent else f"{self.discount_amount} ₽"
        return f"{self.title} (Скидка {val})"

    def is_currently_active(self):
        if not self.is_active:
            return False
        from django.utils import timezone
        now = timezone.now()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percent", "Процент от стоимости (%)"),
        ("fixed", "Фиксированная сумма (₽)"),
    ]

    APPLIES_CHOICES = [
        ("all", "На всю корзину"),
        ("categories", "На определенные категории (каталоги)"),
        ("products", "На определенные товары"),
    ]

    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Код промокода",
        help_text="Например: SIBCHEESE10, VESNA2026, SUPERСЫР (автоматически переводится в верхний регистр)"
    )
    title = models.CharField(
        max_length=200, 
        verbose_name="Название / Назначение",
        help_text="Например: Скидка 10% для постоянных покупателей"
    )
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default="percent", 
        verbose_name="Тип скидки"
    )
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Величина скидки (% или ₽)",
        help_text="Если процент — укажите например 10. Если рубли — укажите например 300."
    )
    min_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Минимальная сумма заказа, ₽",
        help_text="Промокод сработает только если сумма заказа не меньше этого значения"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Максимальный размер скидки, ₽",
        help_text="Ограничение максимальной скидки в рублях для процентных промокодов (необязательно)"
    )
    applies_to = models.CharField(
        max_length=20, 
        choices=APPLIES_CHOICES, 
        default="all", 
        verbose_name="Область действия промокода"
    )
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name="promocodes", 
        verbose_name="Применимо к категориям"
    )
    products = models.ManyToManyField(
        Product, 
        blank=True, 
        related_name="promocodes", 
        verbose_name="Применимо к товарам"
    )
    valid_from = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Действует с"
    )
    valid_to = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Действует до"
    )
    usage_limit = models.PositiveIntegerField(
        default=0, 
        verbose_name="Лимит использований",
        help_text="0 — без ограничений по количеству"
    )
    times_used = models.PositiveIntegerField(
        default=0, 
        verbose_name="Использован раз"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ["-created_at"]

    def clean(self):
        if self.code:
            self.code = self.code.strip().upper()

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        val = f"{int(self.discount_value)}%" if self.discount_type == 'percent' else f"{self.discount_value} ₽"
        return f"{self.code} — {self.title} ({val})"

    def check_validity(self):
        """Проверяет общие условия валидности промокода."""
        if not self.is_active:
            return False, "Данный промокод деактивирован."
        
        from django.utils import timezone
        now = timezone.now()
        if self.valid_from and self.valid_from > now:
            return False, "Срок действия промокода еще не начался."
        if self.valid_to and self.valid_to < now:
            return False, "Срок действия промокода истек."
        if self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False, "Лимит использований данного промокода исчерпан."
            
        return True, ""

    def calculate_discount_for_cart(self, items):
        """
        Рассчитывает скидку для переданного списка товаров в корзине.
        items: list of dicts: [{'title': str, 'numPrice': number, 'count': int}, ...]
        """
        valid, msg = self.check_validity()
        if not valid:
            return {
                "is_valid": False, 
                "error": msg, 
                "discount_amount": Decimal("0.00"),
                "subtotal": Decimal("0.00"),
                "total": Decimal("0.00")
            }

        subtotal = Decimal("0.00")
        qualifying_amount = Decimal("0.00")

        qualifying_cat_ids = set(self.categories.values_list("id", flat=True)) if self.applies_to == "categories" else set()
        qualifying_prod_titles = set(self.products.values_list("title", flat=True)) if self.applies_to == "products" else set()

        for it in items:
            p_price = Decimal(str(it.get("numPrice", 0)))
            p_count = int(it.get("count", 1))
            line_total = p_price * p_count
            subtotal += line_total

            title = it.get("title", "")
            is_qualifying = False

            if self.applies_to == "all":
                is_qualifying = True
            elif self.applies_to == "categories":
                prod = Product.objects.filter(title__iexact=title).select_related("category").first()
                if prod and prod.category_id in qualifying_cat_ids:
                    is_qualifying = True
            elif self.applies_to == "products":
                if title in qualifying_prod_titles or Product.objects.filter(title__iexact=title, pk__in=self.products.all()).exists():
                    is_qualifying = True

            if is_qualifying:
                qualifying_amount += line_total

        if subtotal < self.min_order_amount:
            return {
                "is_valid": False,
                "error": f"Минимальная сумма заказа для промокода: {int(self.min_order_amount)} ₽ (сейчас в корзине {int(subtotal)} ₽)",
                "discount_amount": Decimal("0.00"),
                "subtotal": subtotal,
                "total": subtotal,
            }

        if qualifying_amount <= 0:
            scope_desc = "товары из определенных категорий" if self.applies_to == "categories" else "определенные товары акции"
            return {
                "is_valid": False,
                "error": f"Промокод действует только на {scope_desc}. В вашей корзине нет таких позиций.",
                "discount_amount": Decimal("0.00"),
                "subtotal": subtotal,
                "total": subtotal,
            }

        # Вычисление скидки
        if self.discount_type == "percent":
            discount = (qualifying_amount * (self.discount_value / Decimal("100"))).quantize(Decimal("1.00"))
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            discount = min(self.discount_value, qualifying_amount)

        total = max(Decimal("0.00"), subtotal - discount)
        return {
            "is_valid": True,
            "error": "",
            "discount_amount": discount,
            "subtotal": subtotal,
            "total": total,
            "qualifying_amount": qualifying_amount,
        }


class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("confirmed", "Подтвержден"),
        ("shipped", "Отгружен"),
        ("completed", "Выполнен"),
        ("cancelled", "Отменен"),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ("individual", "Физическое лицо (Обычный покупатель)"),
        ("legal", "Юридическое лицо / ИП"),
    ]

    PAYMENT_CHOICES = [
        ("cash", "Наличными при получении"),
        ("card", "Банковской картой"),
        ("invoice", "Безналичный расчет (по счету для юрлиц)"),
        ("online", "Онлайн-оплата"),
    ]

    # Связь с пользователем (для ЛК)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Пользователь (аккаунт)"
    )

    # Основная информация
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default="individual",
        verbose_name="Тип покупателя"
    )
    name = models.CharField(max_length=150, verbose_name="Контактное лицо / ФИО")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    email = models.CharField(max_length=100, blank=True, verbose_name="E-mail")

    # Реквизиты для Юр. Лиц / ИП
    company_name = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Наименование организации / ИП",
        help_text="Например: ООО «Сырная Лавка» или ИП Смирнов И.И."
    )
    inn = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="ИНН покупателя"
    )
    kpp = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="КПП (для юр. лиц)"
    )
    ogrn = models.CharField(
        max_length=25, 
        blank=True, 
        verbose_name="ОГРН / ОГРНИП"
    )
    legal_address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Юридический адрес покупателя"
    )
    bank_name = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Банк покупателя"
    )
    bik = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="БИК банка покупателя"
    )
    account_number = models.CharField(
        max_length=35, 
        blank=True, 
        verbose_name="Расчетный счет покупателя"
    )
    corr_account = models.CharField(
        max_length=35, 
        blank=True, 
        verbose_name="Корреспондентский счет покупателя"
    )

    # Доставка и оплата
    delivery_address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Адрес доставки / Отгрузки"
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_CHOICES,
        default="cash",
        verbose_name="Способ оплаты"
    )
    is_paid = models.BooleanField(
        default=False, 
        verbose_name="Заказ оплачен"
    )
    subtotal_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Сумма без скидки, ₽"
    )
    discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Сумма скидки, ₽"
    )
    promocode = models.ForeignKey(
        PromoCode, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="orders", 
        verbose_name="Использованный промокод"
    )
    promocode_code = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Код промокода"
    )
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Итоговая сумма, ₽"
    )
    order_token = models.CharField(
        max_length=64, 
        blank=True, 
        unique=True,
        verbose_name="Токен доступа (для чеков/накладных)"
    )

    # Состав заказа текстовым полем (для обратной совместимости)
    product_choice = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name="Интересующий продукт / объем"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="new", 
        verbose_name="Статус заказа"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата оформления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Заказ клиента"
        verbose_name_plural = "Заказы клиентов"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_token:
            self.order_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        client = self.company_name if (self.customer_type == 'legal' and self.company_name) else self.name
        return f"Заказ #{self.id} от {client} ({self.get_customer_type_display()}) — {self.get_status_display()}"

    @property
    def is_legal(self):
        return self.customer_type == "legal"

    @property
    def customer_display_title(self):
        if self.is_legal and self.company_name:
            details = []
            if self.inn:
                details.append(f"ИНН {self.inn}")
            if self.kpp:
                details.append(f"КПП {self.kpp}")
            info = f" ({', '.join(details)})" if details else ""
            return f"{self.company_name}{info}"
        return self.name

    def get_order_items(self):
        """Возвращает позиции заказа или динамически формирует их из product_choice."""
        items = list(self.items.all())
        if items:
            return items

        # Fallback: формируем виртуальные позиции из текстового поля product_choice
        virtual_items = []
        raw_text = self.product_choice or "Продукция ТМ «Сибсыр»"
        parts = [p.strip() for p in raw_text.split(";") if p.strip()]
        
        if not parts:
            parts = [raw_text]

        for p_str in parts:
            # Попытка парсинга: "Сыр Сулугуни x 2 шт."
            qty = 1
            title = p_str
            if " x " in p_str:
                t, q_part = p_str.rsplit(" x ", 1)
                title = t.strip()
                q_digits = "".join([c for c in q_part if c.isdigit()])
                if q_digits:
                    qty = int(q_digits)

            # Вычисляем ориентировочную цену, если есть общая сумма
            price = self.total_price / len(parts) if self.total_price and len(parts) > 0 else Decimal("0.00")
            virtual_items.append({
                "title": title,
                "unit": "шт.",
                "quantity": qty,
                "price": price / qty if qty else price,
                "total": price
            })
        return virtual_items

    def calculate_total_amount(self):
        """Пересчитывает общую сумму заказа по позициям с учетом скидки."""
        items = self.items.all()
        if items.exists():
            subtotal = sum(i.quantity * i.price for i in items)
            self.subtotal_price = subtotal
            total = max(Decimal("0.00"), subtotal - self.discount_amount)
            return total
        if self.discount_amount > 0 and self.subtotal_price > 0:
            return max(Decimal("0.00"), self.subtotal_price - self.discount_amount)
        return self.total_price

    def get_total_in_words(self):
        total = self.calculate_total_amount()
        return amount_in_words(total)

    def get_items_count(self):
        items = self.get_order_items()
        return len(items)

    def get_items_count_in_words(self):
        return count_items_in_words(self.get_items_count())

    @property
    def clean_phone(self):
        if not self.phone:
            return ""
        return "".join(c for c in self.phone if c.isdigit() or c == "+")

    @property
    def formatted_total_price(self):
        return f"{self.total_price:,.2f} ₽".replace(",", " ")

    @property
    def formatted_subtotal_price(self):
        return f"{self.subtotal_price:,.2f} ₽".replace(",", " ")

    @property
    def formatted_discount_amount(self):
        return f"{self.discount_amount:,.2f} ₽".replace(",", " ")


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name="items", 
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="order_items", 
        verbose_name="Товар из каталога"
    )
    title = models.CharField(max_length=255, verbose_name="Наименование товара / услуги")
    unit = models.CharField(max_length=30, default="шт.", verbose_name="Единица измерения")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name="Цена за ед., ₽"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.title} — {self.quantity} {self.unit} x {self.price} ₽"

    @property
    def total(self):
        return self.quantity * self.price


class Review(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Товар"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Пользователь"
    )
    author_name = models.CharField(max_length=150, verbose_name="Имя автора")
    city = models.CharField(max_length=100, default="г. Омск", blank=True, verbose_name="Город")
    rating = models.PositiveSmallIntegerField(default=5, verbose_name="Оценка (1-5)")
    text = models.TextField(verbose_name="Текст отзыва")
    product_mention = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="О каком сыре / продукте отзыв"
    )
    is_approved = models.BooleanField(default=True, verbose_name="Опубликован на сайте")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Отзыв клиента"
        verbose_name_plural = "Отзывы клиентов"
        ordering = ["-created_at"]

    def __str__(self):
        target = f" о «{self.product.title}»" if self.product else (f" ({self.product_mention})" if self.product_mention else "")
        return f"Отзыв от {self.author_name}{target} ({self.rating}★)"

    def save(self, *args, **kwargs):
        if self.product and not self.product_mention:
            self.product_mention = self.product.title
        super().save(*args, **kwargs)


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Review)
def update_product_rating_on_review_save(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return
    if instance.product:
        instance.product.update_rating_stats()


@receiver(post_delete, sender=Review)
def update_product_rating_on_review_delete(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return
    if instance.product:
        instance.product.update_rating_stats()

