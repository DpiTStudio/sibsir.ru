from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    SiteSettings, ProductionFeature, CallbackRequest,
    CompanyTimeline, QualityCertificate, DeliveryMethod,
    PaymentMethod, DeliveryFaq, ContactDepartment,
    FaqCategory, FaqItem, Page
)
from .captcha import generate_captcha, verify_captcha
from shop.models import Category, Product, Order, Review, Promotion, PromoCode
from articles.models import Article


def index(request):
    settings = SiteSettings.get_solo()
    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    features = ProductionFeature.objects.filter(is_active=True).order_by("order", "id")
    all_products = list(Product.objects.filter(is_active=True).select_related("category").order_by("order", "id"))
    articles = Article.objects.filter(is_published=True).order_by("order", "-id")[:6]
    reviews = Review.objects.filter(is_approved=True).order_by("-created_at")[:6]

    now = timezone.now()
    promotions = Promotion.objects.filter(
        is_active=True,
        show_banner=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by("order", "-id")

    # Активные промокоды, рекомендуемые для показа
    featured_promocodes = PromoCode.objects.filter(
        is_active=True
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=now)
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gte=now)
    ).order_by("-id")[:3]

    # --- 1. САМЫЕ ПОПУЛЯРНЫЕ ТОВАРЫ (6 товаров для карусели: по 3 на десктопе, по 1 на планшетах и смартфонах) ---
    pop_candidates = [p for p in all_products if any(b in (p.badge or "").lower() for b in ["хит", "популярн"])]
    if len(pop_candidates) < 6:
        for p in all_products:
            if p not in pop_candidates and p.is_featured:
                pop_candidates.append(p)
                if len(pop_candidates) >= 6:
                    break
    if len(pop_candidates) < 6:
        for p in all_products:
            if p not in pop_candidates:
                pop_candidates.append(p)
                if len(pop_candidates) >= 6:
                    break
    popular_products = pop_candidates[:6]
    popular_ids = {p.id for p in popular_products}

    # --- 2. ТОВАРЫ ПО АКЦИИ (до 6 товаров, по 3 товара на строчку) ---
    sale_candidates = [p for p in all_products if p.has_discount]
    sale_products = sale_candidates[:6]
    sale_products_count = len(sale_candidates)

    # --- 3. ВЫБОР ПОКУПАТЕЛЕЙ / РЕКОМЕНДУЕМ (6 товаров для карусели) ---
    rec_candidates = [p for p in all_products if any(b in (p.badge or "").lower() for b in ["выбор", "рекоменд"])]
    if len(rec_candidates) < 6:
        for p in all_products:
            if p not in rec_candidates and p.id not in popular_ids:
                rec_candidates.append(p)
                if len(rec_candidates) >= 6:
                    break
    if len(rec_candidates) < 6:
        for p in all_products:
            if p not in rec_candidates:
                rec_candidates.append(p)
                if len(rec_candidates) >= 6:
                    break
    recommended_products = rec_candidates[:6]

    seo_data = settings.get_page_seo("home")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "hero_title": settings.hero_title,
        "hero_subtitle": settings.hero_subtitle,
        "hero_badge_text": settings.hero_badge_text,
        "hero_image_url": settings.hero_image_url,
        "cta_button_text": settings.cta_button_text,
        "categories": categories,
        "features": features,
        "popular_products": popular_products,
        "sale_products": sale_products,
        "recommended_products": recommended_products,
        "total_products_count": len(all_products),
        "articles": articles,
        "reviews": reviews,
        "promotions": promotions,
        "featured_promocodes": featured_promocodes,
        "sale_products_count": sale_products_count,
        "total_articles_count": Article.objects.filter(is_published=True).count(),
    }
    return render(request, "main/index.html", context)


def catalog_view(request):
    """
    Отдельная страница полного каталога продукции с фильтрацией по категориям,
    акциям и поиском.
    """
    settings = SiteSettings.get_solo()
    categories = Category.objects.filter(is_active=True).annotate(
        num_products=Count('products', filter=Q(products__is_active=True))
    ).filter(num_products__gt=0).order_by("order", "name")
    products = list(Product.objects.filter(is_active=True).select_related("category").order_by("order", "id"))

    sale_products_count = sum(1 for p in products if p.has_discount)
    selected_cat = (request.GET.get("cat") or request.GET.get("category") or "all").strip()

    valid_prices = [p.effective_price_numeric for p in products if p.effective_price_numeric > 0]
    min_price = min(valid_prices) if valid_prices else 0
    max_price = max(valid_prices) if valid_prices else 1000
    hits_count = sum(1 for p in products if any(b in (p.effective_badge or "").lower() or (p.badge and b in p.badge.lower()) for b in ["хит", "популярн", "выбор", "топ"]))
    gost_count = sum(1 for p in products if "гост" in (p.standard or "").lower())

    current_category = None
    if selected_cat and selected_cat != "all":
        current_category = Category.objects.filter(slug=selected_cat, is_active=True).first()

    if current_category:
        page_title = current_category.get_meta_title()
        page_description = current_category.get_meta_description()
        page_keywords = current_category.get_meta_keywords()
    else:
        seo_data = settings.get_page_seo("catalog")
        page_title = seo_data["title"]
        page_description = seo_data["description"]
        page_keywords = seo_data["keywords"]

    # Постраничная навигация (по 9 товаров на страницу)
    page_size = 9
    try:
        current_page = int(request.GET.get("page", 1))
        if current_page < 1:
            current_page = 1
    except (ValueError, TypeError):
        current_page = 1

    total_products_count = len(products)
    total_pages = (total_products_count + page_size - 1) // page_size if total_products_count > 0 else 1
    if current_page > total_pages:
        current_page = total_pages

    start_product_idx = (current_page - 1) * page_size + 1 if total_products_count > 0 else 0
    end_product_idx = min(current_page * page_size, total_products_count)

    context = {
        "page_title": page_title,
        "page_description": page_description,
        "page_keywords": page_keywords,
        "current_category": current_category,
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "categories": categories,
        "products": products,
        "sale_products_count": sale_products_count,
        "hits_count": hits_count,
        "gost_count": gost_count,
        "min_price": min_price,
        "max_price": max_price,
        "selected_cat": selected_cat,
        "page_size": page_size,
        "current_page": current_page,
        "total_pages": total_pages,
        "page_range": list(range(1, total_pages + 1)),
        "start_product_idx": start_product_idx,
        "end_product_idx": end_product_idx,
    }
    return render(request, "main/catalog.html", context)


def categories_list_view(request):
    """
    Отдельная страница со списком всех категорий продукции завода ТМ «Сибсыр».
    Каждая категория представлена с фото, иконкой, описанием, активными скидками,
    количеством товаров, превью ведущих позиций и прямой ссылкой в каталог.
    """
    settings = SiteSettings.get_solo()
    categories_qs = Category.objects.filter(is_active=True).order_by("order", "name")

    categories_data = []
    total_products_count = 0
    for cat in categories_qs:
        prods = list(cat.products.filter(is_active=True).order_by("order", "id"))
        p_count = len(prods)
        if p_count == 0:
            continue
        total_products_count += p_count
        categories_data.append({
            "category": cat,
            "products_count": p_count,
            "preview_products": prods[:4],
            "has_discount": cat.has_discount,
            "promotion": cat.get_active_promotion(),
            "image_url": cat.image_url,
        })

    seo_data = settings.get_page_seo("categories")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "categories_data": categories_data,
        "total_categories_count": len(categories_data),
        "total_products_count": total_products_count,
    }
    return render(request, "main/categories_list.html", context)


def product_detail_view(request, slug):
    """
    Полноценная страница товара с деталями, характеристиками,
    дополнительным описанием, составом, гастрономическими советами,
    кнопками 'Поделиться' в соцсетях и мессенджерах, корзиной и похожими товарами.
    """
    settings = SiteSettings.get_solo()
    product = get_object_or_404(
        Product.objects.select_related("category"), 
        slug=slug, 
        is_active=True
    )

    # Похожие товары (из той же категории или популярные)
    related_qs = Product.objects.filter(is_active=True).select_related("category").exclude(id=product.id)
    if product.category_id:
        cat_related = list(related_qs.filter(category=product.category).order_by("order", "id")[:4])
    else:
        cat_related = []

    if len(cat_related) < 4:
        needed = 4 - len(cat_related)
        already_ids = {p.id for p in cat_related}
        extra_prods = list(related_qs.exclude(id__in=already_ids).order_by("order", "id")[:needed])
        related_products = cat_related + extra_prods
    else:
        related_products = cat_related

    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    
    # Отзывы именно к данному товару
    product_reviews = product.reviews.filter(is_approved=True).order_by("-created_at")
    product_reviews_count = product_reviews.count()
    avg_rating = product.dynamic_rating
    total_reviews_display = product.dynamic_reviews_count

    # Распределение оценок (5, 4, 3, 2, 1) для детальной шкалы
    rating_distribution = []
    if product_reviews_count > 0:
        for star in [5, 4, 3, 2, 1]:
            cnt = sum(1 for r in product_reviews if r.rating == star)
            pct = int(round((cnt / product_reviews_count) * 100))
            rating_distribution.append({
                "star": star,
                "count": cnt,
                "percent": pct
            })
    else:
        # Для гармоничного вида при базовом рейтинге 4.9
        rating_distribution = [
            {"star": 5, "count": 12, "percent": 86},
            {"star": 4, "count": 2, "percent": 14},
            {"star": 3, "count": 0, "percent": 0},
            {"star": 2, "count": 0, "percent": 0},
            {"star": 1, "count": 0, "percent": 0},
        ]

    # Общие отзывы (на случай, если к товару пока мало отзывов)
    general_reviews = Review.objects.filter(is_approved=True).exclude(product=product).order_by("-created_at")[:4]

    # Данные для шаринга в соцсетях и мессенджерах
    full_url = request.build_absolute_uri()
    share_title = f"{product.title} — ТМ «Сибсыр»"
    share_text = f"Натуральный продукт: {product.title}. Цена: {product.effective_price_display}. Доставка из Омска."

    context = {
        "page_title": product.get_meta_title(),
        "page_description": product.get_meta_description(),
        "page_keywords": product.get_meta_keywords(),
        "canonical_url": product.get_canonical_url(request),
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "product": product,
        "related_products": related_products,
        "categories": categories,
        "reviews": product_reviews,
        "product_reviews": product_reviews,
        "product_reviews_count": product_reviews_count,
        "total_reviews_display": total_reviews_display,
        "average_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "general_reviews": general_reviews,
        "full_url": full_url,
        "share_title": share_title,
        "share_text": share_text,
    }
    return render(request, "main/product_detail.html", context)


def articles_list_view(request):
    """
    Отдельная страница каталога статей и базы знаний о сыре.
    Поддерживает поиск по статьям.
    """
    settings = SiteSettings.get_solo()
    articles_qs = Article.objects.filter(is_published=True).order_by("order", "-id")

    query = request.GET.get("q", "").strip()
    if query:
        words = [w.lower() for w in query.split() if w]
        q_obj = Q()
        for w in words:
            q_obj &= (Q(title__icontains=w) | Q(snippet__icontains=w) | Q(content__icontains=w))
        articles = list(articles_qs.filter(q_obj))
    else:
        articles = list(articles_qs)

    seo_data = settings.get_page_seo("articles")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "articles": articles,
        "total_count": len(articles),
        "all_articles_count": Article.objects.filter(is_published=True).count(),
        "query": query,
    }
    return render(request, "main/articles.html", context)


def article_detail_view(request, slug):
    """
    Отдельная страница детального просмотра статьи с полным текстом,
    иллюстрацией, временем чтения и похожими материалами.
    """
    settings = SiteSettings.get_solo()
    article = get_object_or_404(Article, slug=slug, is_published=True)

    # Инкремент просмотров
    Article.objects.filter(pk=article.pk).update(views_count=article.views_count + 1)
    article.views_count += 1

    # Другие статьи для блока рекомендаций
    related_articles = Article.objects.filter(is_published=True).exclude(pk=article.pk).order_by("order", "-id")[:3]

    # Расчет примерного времени чтения
    words = article.content.split() if article.content else []
    read_time = max(1, round(len(words) / 100))

    canonical_url = request.build_absolute_uri(article.get_absolute_url())

    context = {
        "page_title": article.get_meta_title(),
        "page_description": article.get_meta_description(),
        "page_keywords": article.get_meta_keywords(),
        "canonical_url": canonical_url,
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "article": article,
        "related_articles": related_articles,
        "read_time": read_time,
    }
    return render(request, "main/article_detail.html", context)



def search_api(request):
    """
    AJAX-эндпоинт быстрого поиска (живой поиск / autocomplete).
    Ищет по активным товарам, категориям и статьям.
    Поддерживает регистронезависимый поиск по русским символам и составным фразам.
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({
            "query": "",
            "total_count": 0,
            "products_count": 0,
            "categories_count": 0,
            "articles_count": 0,
            "products": [],
            "categories": [],
            "articles": [],
        })

    words = [w.lower() for w in query.split() if w.strip()]
    q_lower = query.lower()

    # 1. Товары
    all_products = list(Product.objects.filter(is_active=True).select_related("category"))
    matched_products = []
    for p in all_products:
        cat_name = p.category.name if p.category else ""
        searchable_text = f"{p.title} {p.description or ''} {cat_name} {p.fat_content or ''} {p.package_type or ''} {p.unit_weight or ''} {p.badge or ''}".lower()
        if all(w in searchable_text for w in words):
            # Ранжирование релевантности
            title_lower = p.title.lower()
            if title_lower.startswith(q_lower):
                rank = 0
            elif q_lower in title_lower:
                rank = 1
            elif any(w in title_lower for w in words):
                rank = 2
            elif q_lower in cat_name.lower():
                rank = 3
            else:
                rank = 4
            matched_products.append((rank, p))

    matched_products.sort(key=lambda item: (item[0], item[1].order, item[1].id))
    sorted_products = [item[1] for item in matched_products]
    products_count = len(sorted_products)

    # 2. Категории
    all_categories = list(Category.objects.filter(is_active=True))
    matched_categories = []
    for c in all_categories:
        c_text = f"{c.name} {c.description or ''}".lower()
        if all(w in c_text for w in words):
            matched_categories.append(c)
    categories_count = len(matched_categories)

    # 3. Статьи
    all_articles = list(Article.objects.filter(is_published=True))
    matched_articles = []
    for a in all_articles:
        a_text = f"{a.title} {a.snippet or ''} {a.content or ''}".lower()
        if all(w in a_text for w in words):
            matched_articles.append(a)
    articles_count = len(matched_articles)

    # 4. Динамические страницы
    all_pages = list(Page.objects.filter(is_published=True))
    matched_pages = []
    for pg in all_pages:
        pg_text = f"{pg.title} {pg.subtitle or ''} {pg.content or ''} {pg.focus_keyword or ''}".lower()
        if all(w in pg_text for w in words):
            matched_pages.append(pg)
    pages_count = len(matched_pages)

    # Формируем JSON ответ для live-поиска
    products_data = []
    for p in sorted_products[:8]:
        products_data.append({
            "id": p.id,
            "title": p.title,
            "category": p.category.name if p.category else "Сибсыр",
            "category_slug": p.category.slug if p.category else "",
            "price_display": p.effective_price_display,
            "price_numeric": p.effective_price_numeric,
            "old_price_numeric": p.effective_old_price_numeric,
            "wholesale_price_display": p.effective_wholesale_price_display,
            "wholesale_min_qty": p.wholesale_min_qty,
            "has_discount": p.has_discount,
            "image_url": p.image_url,
            "fat_content": p.fat_content,
            "unit_weight": p.unit_weight,
            "package_type": p.package_type,
            "badge": p.effective_badge or p.badge,
        })

    categories_data = []
    for c in matched_categories[:4]:
        categories_data.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "icon": c.icon or "bi-tag",
            "products_count": c.products.filter(is_active=True).count(),
        })

    articles_data = []
    for a in matched_articles[:4]:
        snippet_clean = a.snippet[:130] + "..." if len(a.snippet) > 130 else a.snippet
        articles_data.append({
            "id": a.id,
            "title": a.title,
            "slug": a.slug,
            "date_str": a.date_str,
            "snippet": snippet_clean,
            "image_url": a.image_url,
        })

    pages_data = []
    for pg in matched_pages[:4]:
        snippet_clean = pg.subtitle[:130] + "..." if pg.subtitle and len(pg.subtitle) > 130 else (pg.subtitle or pg.get_clean_text()[:130])
        pages_data.append({
            "id": pg.id,
            "title": pg.title,
            "slug": pg.slug,
            "url": pg.get_absolute_url(),
            "badge": pg.badge or "Страница",
            "snippet": snippet_clean,
        })

    return JsonResponse({
        "query": query,
        "total_count": products_count + categories_count + articles_count + pages_count,
        "products_count": products_count,
        "categories_count": categories_count,
        "articles_count": articles_count,
        "pages_count": pages_count,
        "products": products_data,
        "categories": categories_data,
        "articles": articles_data,
        "pages": pages_data,
    })


def search_view(request):
    """
    Полноценная отдельная страница результатов поиска по сайту и каталогу.
    Поддерживает фильтрацию по категориям, вкладкам и сортировку.
    """
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    active_tab = request.GET.get("tab", "all").strip()
    sort_by = request.GET.get("sort", "relevance").strip()

    all_categories = Category.objects.filter(is_active=True).order_by("order", "name")

    products = []
    categories = []
    articles = []
    pages = []

    if query:
        words = [w.lower() for w in query.split() if w.strip()]
        q_lower = query.lower()

        # 1. Фильтр товаров
        prod_qs = Product.objects.filter(is_active=True).select_related("category")
        if category_slug == "sale":
            all_products = [p for p in prod_qs if p.has_discount]
        elif category_slug:
            prod_qs = prod_qs.filter(category__slug=category_slug)
            all_products = list(prod_qs)
        else:
            all_products = list(prod_qs)

        matched_products = []
        for p in all_products:
            cat_name = p.category.name if p.category else ""
            searchable_text = f"{p.title} {p.description or ''} {cat_name} {p.fat_content or ''} {p.package_type or ''} {p.unit_weight or ''} {p.badge or ''}".lower()
            if all(w in searchable_text for w in words):
                title_lower = p.title.lower()
                if title_lower.startswith(q_lower):
                    rank = 0
                elif q_lower in title_lower:
                    rank = 1
                elif any(w in title_lower for w in words):
                    rank = 2
                elif q_lower in cat_name.lower():
                    rank = 3
                else:
                    rank = 4
                matched_products.append((rank, p))

        # Сортировка товаров
        if sort_by == "price_asc":
            matched_products.sort(key=lambda item: (item[1].price_numeric, item[1].title))
        elif sort_by == "price_desc":
            matched_products.sort(key=lambda item: (-item[1].price_numeric, item[1].title))
        elif sort_by == "name_asc":
            matched_products.sort(key=lambda item: item[1].title)
        elif sort_by == "name_desc":
            matched_products.sort(key=lambda item: item[1].title, reverse=True)
        else:
            # relevance
            matched_products.sort(key=lambda item: (item[0], item[1].order, item[1].id))

        products = [item[1] for item in matched_products]

        # 2. Фильтр категорий
        all_cat_list = list(Category.objects.filter(is_active=True).order_by("order", "name"))
        for c in all_cat_list:
            c_text = f"{c.name} {c.description or ''}".lower()
            if all(w in c_text for w in words):
                categories.append(c)

        # 3. Фильтр статей
        all_art_list = list(Article.objects.filter(is_published=True).order_by("-views_count", "-id"))
        for a in all_art_list:
            a_text = f"{a.title} {a.snippet or ''} {a.content or ''}".lower()
            if all(w in a_text for w in words):
                articles.append(a)

        # 4. Фильтр динамических страниц
        all_page_list = list(Page.objects.filter(is_published=True).order_by("order", "-views_count"))
        for pg in all_page_list:
            pg_text = f"{pg.title} {pg.subtitle or ''} {pg.content or ''} {pg.focus_keyword or ''}".lower()
            if all(w in pg_text for w in words):
                pages.append(pg)

    products_count = len(products)
    categories_count = len(categories)
    articles_count = len(articles)
    pages_count = len(pages)
    total_count = products_count + categories_count + articles_count + pages_count

    popular_queries = [
        "Сулугуни", "Косичка", "Масло 82.5%", "Чечил", "Адыгейский", 
        "Брынза", "Тан", "Айран", "Творожный"
    ]

    selected_category_obj = None
    if category_slug:
        selected_category_obj = Category.objects.filter(slug=category_slug).first()

    context = {
        "query": query,
        "selected_category": category_slug,
        "selected_category_obj": selected_category_obj,
        "active_tab": active_tab,
        "sort_by": sort_by,
        "products": products,
        "products_count": products_count,
        "categories": categories,
        "categories_count": categories_count,
        "articles": articles,
        "articles_count": articles_count,
        "pages": pages,
        "pages_count": pages_count,
        "total_count": total_count,
        "all_categories": all_categories,
        "popular_queries": popular_queries,
    }
    return render(request, "main/search.html", context)


import json
from decimal import Decimal
from django.urls import reverse
from shop.models import Category, Product, Order, OrderItem, Review, PromoCode


@require_POST
def create_order(request):
    customer_type = request.POST.get("customer_type", "individual").strip()
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    email = request.POST.get("email", "").strip()
    product_choice = request.POST.get("product_choice", "").strip()
    comment = request.POST.get("comment", "").strip()
    delivery_address = request.POST.get("delivery_address", "").strip()
    promocode_code = request.POST.get("promocode_code", "").strip()

    # Реквизиты для юрлиц
    company_name = request.POST.get("company_name", "").strip()
    inn = request.POST.get("inn", "").strip()
    kpp = request.POST.get("kpp", "").strip()
    legal_address = request.POST.get("legal_address", "").strip()

    if not name or not phone:
        return JsonResponse(
            {"success": False, "error": "Пожалуйста, укажите имя/контактное лицо и номер телефона."}, 
            status=400
        )

    # Проверка капчи для неавторизованных (гостевых) покупателей
    site_settings = SiteSettings.get_solo()
    if site_settings.is_captcha_required("order", user=request.user):
        captcha_key = request.POST.get("captcha_key", "").strip()
        captcha_answer = request.POST.get("captcha_answer", "").strip()
        is_valid, err_msg = verify_captcha(captcha_key, captcha_answer)
        if not is_valid:
            return JsonResponse({
                "success": False, 
                "error": err_msg or "Неверный проверочный код с картинки."
            }, status=400)


    if customer_type == "legal" and not company_name:
        company_name = f"ИП / Организация {name}"

    current_user = request.user if request.user.is_authenticated else None

    order = Order.objects.create(
        user=current_user,
        customer_type=customer_type,
        name=name,
        phone=phone,
        email=email,
        company_name=company_name,
        inn=inn,
        kpp=kpp,
        legal_address=legal_address,
        delivery_address=delivery_address or comment,
        product_choice=product_choice or "Продукция ТМ «Сибсыр»",
        comment=comment,
        status="new"
    )

    # Синхронизация данных с профилем авторизованного пользователя
    if current_user and hasattr(current_user, 'profile'):
        try:
            profile = current_user.profile
            save_prof = False
            if phone and not profile.phone:
                profile.phone = phone
                save_prof = True
            if delivery_address and not profile.delivery_address:
                profile.delivery_address = delivery_address
                save_prof = True
            if customer_type == "legal":
                profile.customer_type = "legal"
                if company_name and not profile.company_name:
                    profile.company_name = company_name
                if inn and not profile.inn:
                    profile.inn = inn
                if kpp and not profile.kpp:
                    profile.kpp = kpp
                if legal_address and not profile.legal_address:
                    profile.legal_address = legal_address
                save_prof = True
            if save_prof:
                profile.save()
        except Exception:
            pass

    # Попытка парсинга позиций из корзины (cart_items_json)
    cart_items_json = request.POST.get("cart_items_json", "").strip()
    total_calculated = Decimal("0.00")
    items_list_for_discount = []

    if cart_items_json:
        try:
            items_data = json.loads(cart_items_json)
            if isinstance(items_data, list):
                items_list_for_discount = items_data
                for item in items_data:
                    title = item.get("title", "Товар")
                    num_price = Decimal(str(item.get("numPrice", 0)))
                    count = int(item.get("count", 1))
                    
                    product_obj = Product.objects.filter(title__iexact=title).first()
                    if num_price <= 0 and product_obj and product_obj.price_numeric > 0:
                        num_price = Decimal(product_obj.effective_price_numeric or product_obj.price_numeric)

                    OrderItem.objects.create(
                        order=order,
                        product=product_obj,
                        title=title,
                        unit="шт.",
                        quantity=count,
                        price=num_price
                    )
                    total_calculated += num_price * count
        except Exception as e:
            pass

    # Расчет промокода и скидки
    discount_amount = Decimal("0.00")
    promocode_obj = None

    if promocode_code:
        promocode_obj = PromoCode.objects.filter(code__iexact=promocode_code).first()
        if promocode_obj:
            promo_calc = promocode_obj.calculate_discount_for_cart(items_list_for_discount)
            if promo_calc.get("is_valid"):
                discount_amount = promo_calc["discount_amount"]
                # Увеличиваем счетчик использования промокода
                PromoCode.objects.filter(id=promocode_obj.id).update(times_used=promocode_obj.times_used + 1)

    order.subtotal_price = total_calculated if total_calculated > 0 else order.calculate_total_amount()
    order.discount_amount = discount_amount
    order.promocode = promocode_obj
    order.promocode_code = promocode_obj.code if promocode_obj else promocode_code
    order.total_price = max(Decimal("0.00"), order.subtotal_price - discount_amount)
    order.save()

    # Ссылки на печать документов
    receipt_url = reverse("shop:order_token_doc", kwargs={"token": order.order_token, "doc_type": "receipt"})
    waybill_url = reverse("shop:order_token_doc", kwargs={"token": order.order_token, "doc_type": "waybill"})
    torg12_url = reverse("shop:order_token_doc", kwargs={"token": order.order_token, "doc_type": "torg12"})
    bill_url = reverse("shop:order_token_doc", kwargs={"token": order.order_token, "doc_type": "bill"})

    doc_primary_url = torg12_url if order.is_legal else waybill_url

    client_display = order.company_name if (order.is_legal and order.company_name) else order.name

    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "order_token": order.order_token,
        "customer_type": order.customer_type,
        "receipt_url": receipt_url,
        "waybill_url": waybill_url,
        "torg12_url": torg12_url,
        "bill_url": bill_url,
        "doc_primary_url": doc_primary_url,
        "discount_amount": float(order.discount_amount),
        "promocode_code": order.promocode_code,
        "total_price": float(order.total_price),
        "message": f"Спасибо, {client_display}! Заказ #{order.id} успешно принят. Наш менеджер свяжется с вами по номеру {order.phone} для подтверждения."
    })


@require_POST
def create_callback(request):
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    email = request.POST.get("email", "").strip()
    company_name = request.POST.get("company_name", "").strip()
    request_type = request.POST.get("request_type", "call").strip()
    message = request.POST.get("message", "").strip()

    if not name or not phone:
        return JsonResponse(
            {"success": False, "error": "Пожалуйста, укажите ваше имя и контактный телефон."}, 
            status=400
        )

    # Если пользователь авторизован, подтягиваем email и организацию при отсутствии
    if request.user.is_authenticated:
        if not email and request.user.email:
            email = request.user.email
        if hasattr(request.user, "profile"):
            if not company_name and request.user.profile.company_name:
                company_name = request.user.profile.company_name

    # Проверка капчи при отправке обращений / заявок
    site_settings = SiteSettings.get_solo()
    if site_settings.is_captcha_required("callback"):
        captcha_key = request.POST.get("captcha_key", "").strip()
        captcha_answer = request.POST.get("captcha_answer", "").strip()
        is_valid, err_msg = verify_captcha(captcha_key, captcha_answer)
        if not is_valid:
            return JsonResponse({
                "success": False, 
                "error": err_msg or "Неверный проверочный код с картинки."
            }, status=400)

    req = CallbackRequest.objects.create(
        name=name,
        company_name=company_name,
        phone=phone,
        email=email,
        request_type=request_type,
        message=message,
        approval_status="pending" if request_type == "wholesale" else "pending"
    )

    if request_type == "wholesale":
        response_msg = f"Благодарим вас, {req.name}! Заявка на оптовый прайс-лист принята. После одобрения администратором актуальный прайс будет направлен вам на Email."
    else:
        response_msg = f"Благодарим вас, {req.name}! Заявка принята. Специалист отдела продаж «Сибсыр» свяжется с вами."

    return JsonResponse({
        "success": True,
        "request_id": req.id,
        "message": response_msg
    })


@require_GET
def captcha_refresh(request):
    """API генерации и обновления проверочного кода капчи без перезагрузки страницы."""
    settings_obj = SiteSettings.get_solo()
    req_type = request.GET.get("type", "").strip()
    captcha_type = req_type if req_type in ["math", "image"] else settings_obj.captcha_type
    captcha_data = generate_captcha(captcha_type=captcha_type)
    return JsonResponse({
        "success": True,
        "key": captcha_data["key"],
        "image_url": captcha_data["image_url"],
        "placeholder": captcha_data["placeholder"],
        "type": captcha_data["type"],
    })



@require_GET
def get_article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    article.views_count += 1
    article.save(update_fields=["views_count"])

    return JsonResponse({
        "success": True,
        "title": article.title,
        "date_str": article.date_str,
        "views_count": article.views_count,
        "content": article.content,
        "image_url": article.image_url,
    })


def about_view(request):
    """
    Отдельная страница «О компании»: история завода, производство,
    стандарты ХАССП, технологии, руководство и реквизиты.
    """
    settings = SiteSettings.get_solo()
    features = ProductionFeature.objects.filter(is_active=True).order_by("order", "id")
    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    timeline = CompanyTimeline.objects.filter(is_active=True).order_by("order", "id")
    certificates = QualityCertificate.objects.filter(is_active=True).order_by("order", "id")
    total_products_count = Product.objects.filter(is_active=True).count()
    reviews_count = Review.objects.filter(is_approved=True).count()

    seo_data = settings.get_page_seo("about")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "features": features,
        "categories": categories,
        "timeline": timeline,
        "certificates": certificates,
        "total_products_count": total_products_count,
        "reviews_count": reviews_count,
    }
    return render(request, "main/about.html", context)


def delivery_view(request):
    """
    Отдельная страница «Доставка и оплата»: температурные перевозки в рефрижераторах,
    условия доставки по Омску, Омской области и России, самовывоз, безналичный и наличный расчет.
    """
    settings = SiteSettings.get_solo()
    total_products_count = Product.objects.filter(is_active=True).count()
    delivery_methods = DeliveryMethod.objects.filter(is_active=True).order_by("order", "id")
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by("order", "id")
    faqs = DeliveryFaq.objects.filter(is_active=True).order_by("order", "id")

    seo_data = settings.get_page_seo("delivery")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "total_products_count": total_products_count,
        "delivery_methods": delivery_methods,
        "payment_methods": payment_methods,
        "faqs": faqs,
    }
    return render(request, "main/delivery.html", context)


def reviews_view(request):
    """
    Отдельная страница «Отзывы»: отзывы покупателей и партнеров, статистика,
    форма добавления отзыва (в том числе с возможностью привязки к конкретному товару).
    """
    settings = SiteSettings.get_solo()
    reviews_qs = Review.objects.filter(is_approved=True).select_related("product").order_by("-created_at")
    total_reviews_count = reviews_qs.count()

    if total_reviews_count > 0:
        avg_val = sum(r.rating for r in reviews_qs) / total_reviews_count
        average_rating = round(avg_val, 1)
    else:
        average_rating = 5.0

    products = list(Product.objects.filter(is_active=True).order_by("order", "title"))
    selected_product_id = request.GET.get("product", "").strip()

    seo_data = settings.get_page_seo("reviews")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "reviews": reviews_qs,
        "total_reviews_count": total_reviews_count,
        "average_rating": average_rating,
        "products": products,
        "selected_product_id": selected_product_id,
    }
    return render(request, "main/reviews.html", context)


def contacts_view(request):
    """
    Отдельная страница «Контакты»: адрес завода, телефоны отделов,
    режим работы, официальные реквизиты, карта и форма обратной связи.
    """
    settings = SiteSettings.get_solo()
    departments = ContactDepartment.objects.filter(is_active=True).order_by("order", "id")

    seo_data = settings.get_page_seo("contacts")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "departments": departments,
    }
    return render(request, "main/contacts.html", context)


def faq_view(request):
    """
    Отдельная страница «Вопрос-ответ» (FAQ):
    Вопросы и ответы о сыре, молочной продукции, технологии производства,
    правилах хранения и выборе с группировкой по категориям, интерактивным поиском и Schema.org разметкой.
    """
    settings = SiteSettings.get_solo()
    categories = FaqCategory.objects.filter(is_active=True).prefetch_related('items').order_by("order", "name")
    
    selected_category_slug = request.GET.get("category", "").strip()
    search_query = request.GET.get("q", "").strip()

    faq_items = FaqItem.objects.filter(is_active=True, category__is_active=True).select_related('category').order_by("category__order", "order", "id")

    selected_category = None
    if selected_category_slug:
        selected_category = categories.filter(slug=selected_category_slug).first()
        if selected_category:
            faq_items = faq_items.filter(category=selected_category)

    if search_query:
        faq_items = faq_items.filter(
            Q(question__icontains=search_query) | Q(answer__icontains=search_query)
        )

    # Категории со счетчиками активных вопросов
    categories_with_counts = []
    for cat in categories:
        cnt = cat.items.filter(is_active=True).count()
        if cnt > 0:
            cat.active_items_count = cnt
            categories_with_counts.append(cat)

    total_questions = FaqItem.objects.filter(is_active=True, category__is_active=True).count()

    seo_data = settings.get_page_seo("faq")
    context = {
        "page_title": seo_data["title"],
        "page_description": seo_data["description"],
        "page_keywords": seo_data["keywords"],
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
        "categories": categories_with_counts,
        "faq_items": faq_items,
        "selected_category": selected_category,
        "selected_category_slug": selected_category_slug,
        "search_query": search_query,
        "total_questions": total_questions,
    }
    return render(request, "main/faq.html", context)


@require_POST
def create_review(request):
    """
    API отправки нового отзыва покупателем (к товару или общему).
    """
    author_name = request.POST.get("author_name", "").strip()
    city = request.POST.get("city", "").strip()
    rating = request.POST.get("rating", "5").strip()
    product_mention = request.POST.get("product_mention", "").strip()
    product_id = request.POST.get("product_id", "").strip()
    text = request.POST.get("text", "").strip()

    # Если пользователь авторизован и имя не передано, берем из профиля
    if request.user.is_authenticated and not author_name:
        author_name = request.user.get_full_name() or request.user.username

    if not author_name or not text:
        return JsonResponse(
            {"success": False, "error": "Пожалуйста, укажите ваше имя и текст отзыва."},
            status=400
        )

    try:
        rating_int = max(1, min(5, int(rating)))
    except (ValueError, TypeError):
        rating_int = 5

    # Проверка капчи, если включена
    site_settings = SiteSettings.get_solo()
    if site_settings.is_captcha_required("callback"):
        captcha_key = request.POST.get("captcha_key", "").strip()
        captcha_answer = request.POST.get("captcha_answer", "").strip()
        is_valid, err_msg = verify_captcha(captcha_key, captcha_answer)
        if not is_valid:
            return JsonResponse({
                "success": False,
                "error": err_msg or "Неверный проверочный код с картинки."
            }, status=400)

    # Привязка к товару, если указан product_id или совпадает по названию
    product = None
    if product_id:
        try:
            product = Product.objects.filter(id=int(product_id), is_active=True).first()
        except (ValueError, TypeError):
            product = None
    elif product_mention:
        product = Product.objects.filter(title__iexact=product_mention, is_active=True).first()

    if product and not product_mention:
        product_mention = product.title

    user = request.user if request.user.is_authenticated else None

    review = Review.objects.create(
        product=product,
        user=user,
        author_name=author_name,
        city=city or "г. Омск",
        rating=rating_int,
        product_mention=product_mention,
        text=text,
        is_approved=True
    )

    # Рейтинг товара пересчитывается автоматически сигналом, но для верности проверяем
    if product:
        product.refresh_from_db(fields=["rating", "reviews_count"])

    return JsonResponse({
        "success": True,
        "review_id": review.id,
        "author_name": review.author_name,
        "city": review.city,
        "rating": review.rating,
        "product_id": product.id if product else None,
        "product_title": product.title if product else "",
        "product_url": product.get_absolute_url() if product else "",
        "product_mention": review.product_mention,
        "text": review.text,
        "created_at": review.created_at.strftime("%d.%m.%Y"),
        "new_rating": float(product.dynamic_rating) if product else None,
        "new_reviews_count": product.dynamic_reviews_count if product else None,
        "message": f"Спасибо за ваш отзыв, {review.author_name}! Отзыв успешно опубликован."
    })


@require_POST
def tinymce_image_upload(request):
    """
    Эндпоинт загрузки изображений из визуального редактора TinyMCE в админке.
    Поддерживает drag & drop, вставку из буфера обмена и диалог «Вставить изображение».
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({"error": "Требуются права администратора."}, status=403)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "Файл изображения не найден в запросе."}, status=400)

    import os
    import uuid
    from django.conf import settings
    from django.utils.text import slugify

    # Проверка допустимых расширений
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
    name, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    if ext not in allowed_exts:
        return JsonResponse({
            "error": f"Недопустимый формат файла ({ext}). Разрешены только: {', '.join(allowed_exts)}"
        }, status=400)

    # Ограничение размера файла (макс. 10 МБ)
    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "Размер файла превышает 10 МБ."}, status=400)

    # Генерация безопасного уникального имени файла
    safe_name = slugify(name)[:40] or "image"
    unique_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"

    upload_dir = os.path.join(settings.MEDIA_ROOT, "editor_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    dest_path = os.path.join(upload_dir, unique_filename)
    try:
        with open(dest_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
    except Exception as exc:
        return JsonResponse({"error": f"Ошибка сохранения файла: {str(exc)}"}, status=500)

    media_url = settings.MEDIA_URL.rstrip("/")
    file_url = f"{media_url}/editor_uploads/{unique_filename}"
    return JsonResponse({"location": file_url})


def company_page_detail_view(request, slug):
    """
    Отображение страниц раздела компании (/company/consent/, /company/soglasie/ и др.).
    Полностью управляется через панель администратора в разделе 'Динамические страницы'.
    """
    return page_detail_view(request, slug=slug)


def page_detail_view(request, slug):
    """
    Отображение динамической страницы произвольного типа.
    Поддерживает:
    - Различные типы макетов (standard, narrow, fullwidth)
    - Полноценные SEO метатеги (Title, Description, Keywords, Canonical, Robots)
    - OpenGraph & Twitter Cards
    - Микроразметку Schema.org (WebPage, Article, AboutPage, ContactPage, FAQPage, ItemPage)
    - Защиту предпросмотра: неопубликованные страницы доступны только персоналу (is_staff)
    - Умный учет просмотров (с сессионной защитой от накрутки)
    - Блок призыва к действию (CTA)
    - Индивидуальные коды счетчиков и стилей (head/body)
    """
    settings = SiteSettings.get_solo()
    
    # Администраторы могут просматривать черновики страниц
    if request.user.is_staff:
        page = get_object_or_404(Page, slug=slug)
    else:
        page = get_object_or_404(Page, slug=slug, is_published=True)

    # Учет уникальных просмотров в рамках сессии
    session_key = f"viewed_page_{page.pk}"
    if not request.session.get(session_key, False):
        Page.objects.filter(pk=page.pk).update(views_count=page.views_count + 1)
        page.views_count += 1
        request.session[session_key] = True

    # Определение базового и канонического адреса
    base_url = (settings.site_base_url or f"{request.scheme}://{request.get_host()}").rstrip('/')
    canonical_url = page.canonical_url.strip() if page.canonical_url else f"{base_url}{page.get_absolute_url()}"

    # Изображение для Open Graph
    if page.og_image:
        og_image_url = page.og_image.url if page.og_image.url.startswith("http") else f"{base_url}{page.og_image.url}"
    elif page.featured_image:
        og_image_url = page.featured_image.url if page.featured_image.url.startswith("http") else f"{base_url}{page.featured_image.url}"
    else:
        og_image_url = f"{base_url}/static/images/hero_cheese.jpg"

    # Формирование JSON-LD микроразметки
    schema_type = page.schema_type or "WebPage"
    import json
    schema_data = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": page.title,
        "headline": page.title,
        "description": page.get_meta_description(),
        "url": canonical_url,
        "datePublished": page.published_at.strftime("%Y-%m-%d") if page.published_at else "",
        "dateModified": page.updated_at.strftime("%Y-%m-%d") if page.updated_at else "",
        "inLanguage": "ru-RU",
        "publisher": {
            "@type": "Organization",
            "name": settings.brand_name,
            "url": base_url,
            "logo": {
                "@type": "ImageObject",
                "url": f"{base_url}{settings.logo.url}" if settings.logo else f"{base_url}/static/images/favicon.svg"
            }
        },
        "image": [og_image_url] if og_image_url else []
    }
    schema_json_str = json.dumps(schema_data, ensure_ascii=False)

    context = {
        "page": page,
        "page_title": page.get_meta_title(),
        "page_description": page.get_meta_description(),
        "page_keywords": page.get_meta_keywords(),
        "canonical_url": canonical_url,
        "meta_robots": page.meta_robots_index,
        "og_title": page.get_og_title(),
        "og_description": page.get_og_description(),
        "og_image_url": og_image_url,
        "og_type": page.og_type or "website",
        "schema_json": schema_json_str,
        "site_settings": settings,
        "brand_name": settings.brand_name,
        "brand_short_name": settings.brand_short_name,
    }
    return render(request, "main/page_detail.html", context)



