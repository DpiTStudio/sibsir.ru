# -*- coding: utf-8 -*-
"""
Парсинг данных с https://sibsir.ru/ и загрузка в Django БД.
Запуск:
    python scratch/scrape_and_populate.py
"""
import os
import sys
import re
import time
import io
import django
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ── Django setup ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

# ── imports after Django ────────────────────────────────────────────────────
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.utils.text import slugify

from shop.models import Category, Product
from main.models import SiteSettings, Review, FaqCategory, FaqItem, ProductionFeature, SocialLink
from articles.models import Article

SITE = "https://sibsir.ru"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get(url, retries=3):
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  [WARN] GET {url} attempt {i+1}: {e}")
            time.sleep(2)
    return None


def soup(url):
    r = get(url)
    if r:
        return BeautifulSoup(r.text, "html.parser")
    return None


def save_image(model_instance, field_name, img_url, filename=None):
    """Скачивает картинку и сохраняет в поле модели."""
    if not img_url:
        return False
    full_url = urljoin(SITE, img_url)
    r = get(full_url)
    if not r:
        return False
    if filename is None:
        path = urlparse(full_url).path
        filename = Path(path).name or "image.jpg"
    field = getattr(model_instance, field_name)
    field.save(filename, ContentFile(r.content), save=False)
    return True


def ru_slug(text, max_len=50):
    """Transliterate Russian text to slug."""
    ru_map = str.maketrans(
        'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
        'abvgdeejzijklmnoprstufhcchshshhyeyujaabvgdeejzijklmnoprstufhcchshshhyeyuja'
    )
    translit = text.translate(ru_map)
    base = slugify(translit)
    return base[:max_len] if base else "item"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. КАТЕГОРИИ И ТОВАРЫ
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_SLUGS = {
    "Рассольные сыры": "rassol-syry",
    "Мягкие сыры": "myagkie-syry",
    "Сливочное масло": "slivochnoe-maslo",
    "Кисломолочные напитки": "kislomolochka",
    "Плавленые сыры": "plavlenye-syry",
}

STATIC_CATEGORIES = [
    {
        "name": "Рассольные сыры",
        "slug": "rassol-syry",
        "description": "Натуральные рассольные сыры из отборного молока: Сулугуни, Брынза, Адыгейский, Чанах, Косичка, Чечил и другие. Производство ТМ «Сибсыр», г. Омск.",
        "icon": "bi-grid-fill",
        "order": 1,
    },
    {
        "name": "Мягкие сыры",
        "slug": "myagkie-syry",
        "description": "Мягкие молочные сыры: нежная творожная консистенция, отборное молоко, стандарты ГОСТ.",
        "icon": "bi-droplet-half",
        "order": 2,
    },
    {
        "name": "Сливочное масло",
        "slug": "slivochnoe-maslo",
        "description": "Натуральное сливочное масло ГОСТ 72.5% и 82.5% из свежих сливок омских фермерских хозяйств. Без растительных жиров и консервантов.",
        "icon": "bi-brightness-high",
        "order": 3,
    },
    {
        "name": "Кисломолочные напитки",
        "slug": "kislomolochka",
        "description": "Тан, Айран, Катык, Мацун — традиционные кисломолочные напитки из натурального молока. Живые культуры, без консервантов.",
        "icon": "bi-cup-straw",
        "order": 4,
    },
    {
        "name": "Плавленые сыры",
        "slug": "plavlenye-syry",
        "description": "Плавленые и колбасные сыры: термостабильные, с выраженным сырным вкусом, для выпечки, пиццы и хачапури.",
        "icon": "bi-fire",
        "order": 5,
    },
]

# Статические данные о товарах (из каталога sibsir.ru)
PRODUCTS_DATA = [
    # ── РАССОЛЬНЫЕ СЫРЫ ──────────────────────────────────────────────────────
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Адыгейский",
        "slug": "syr-adygejskij",
        "description": "Традиционный кавказский мягкий сыр с чистым молочным, слегка солоноватым вкусом.",
        "fat_content": "45%",
        "unit_weight": "0,5 кг / 3,0 кг",
        "shelf_life": "30 суток",
        "price_display": "По запросу",
        "badge": "Хит",
        "is_featured": True,
        "order": 1,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Сулугуни",
        "slug": "syr-suluguni",
        "description": "Классический грузинский рассольный сыр с характерной слоистой эластичной структурой.",
        "fat_content": "45%",
        "unit_weight": "1,0 кг / 5,0 кг",
        "shelf_life": "35 суток",
        "price_display": "По запросу",
        "badge": "Хит",
        "is_featured": True,
        "order": 2,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Брынза",
        "slug": "syr-brynza",
        "description": "Популярный рассольный сыр с выразительным солоноватым кисломолочным вкусом.",
        "fat_content": "45%",
        "unit_weight": "1,0 кг / 5,0 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": True,
        "order": 3,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Чанах",
        "slug": "syr-chanah",
        "description": "Кавказский рассольный сыр с пикантным, остро-соленым вкусом и насыщенным ароматом.",
        "fat_content": "45%",
        "unit_weight": "3,0 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 4,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Косичка (Чечил)",
        "slug": "syr-kosichka-chechil",
        "description": "Волокнистый рассольный сыр ручной вязки с мягким солоноватым вкусом.",
        "fat_content": "45%",
        "unit_weight": "0,2 кг / 0,4 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "Новинка",
        "is_featured": True,
        "order": 5,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Косичка копченая",
        "slug": "syr-kosichka-kopchyonaya",
        "description": "Волокнистый сыр ручной вязки с деликатным натуральным копчением на буковой щепе.",
        "fat_content": "45%",
        "unit_weight": "0,2 кг / 0,4 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 6,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Балык копченый",
        "slug": "syr-balyk-kopchyonyj",
        "description": "Рассольный сыр в форме балыка с золотистой копченой корочкой и упругой текстурой.",
        "fat_content": "45%",
        "unit_weight": "0,2 кг / 1,0 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 7,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Соломка копченая",
        "slug": "syr-solomka-kopchyonaya",
        "description": "Тонкие нити рассольного сыра с натуральным копчением — идеальная закуска.",
        "fat_content": "45%",
        "unit_weight": "0,1 кг / 0,2 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 8,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Снопики с паприкой",
        "slug": "syr-snopiki-s-paprikoj",
        "description": "Волокнистый сыр в форме снопиков, обвалянный в натуральной паприке.",
        "fat_content": "45%",
        "unit_weight": "0,1 кг / 0,3 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 9,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "rassol-syry",
        "title": "Сыр Спагетти копченые",
        "slug": "syr-spagetti-kopchyonye",
        "description": "Тонкие сырные нити в форме спагетти с деликатным копчением.",
        "fat_content": "45%",
        "unit_weight": "0,1 кг / 0,25 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 10,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    # ── МЯГКИЕ СЫРЫ ──────────────────────────────────────────────────────────
    {
        "category_slug": "myagkie-syry",
        "title": "Сыр Аревтур",
        "slug": "syr-arevtur",
        "description": "Фирменный мягкий сыр ТМ «Сибсыр» с нежной сливочной текстурой — авторский рецепт.",
        "fat_content": "50%",
        "unit_weight": "0,5 кг / 3,0 кг",
        "shelf_life": "30 суток",
        "price_display": "По запросу",
        "badge": "Эксклюзив",
        "is_featured": True,
        "order": 1,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    # ── СЛИВОЧНОЕ МАСЛО ──────────────────────────────────────────────────────
    {
        "category_slug": "slivochnoe-maslo",
        "title": "Масло сливочное ГОСТ 72,5%",
        "slug": "maslo-slivochnoe-gost-725",
        "description": "Натуральное сливочное масло высшего сорта из свежих сливок, м.д.ж. 72,5%.",
        "fat_content": "72,5%",
        "unit_weight": "200 г / 500 г / 1 кг / 5 кг / 20 кг",
        "shelf_life": "35 суток",
        "price_display": "По запросу",
        "badge": "Хит",
        "is_featured": True,
        "order": 1,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "slivochnoe-maslo",
        "title": "Масло сливочное ГОСТ 82,5%",
        "slug": "maslo-slivochnoe-gost-825",
        "description": "Натуральное сливочное масло Традиционное высшего сорта, м.д.ж. 82,5%.",
        "fat_content": "82,5%",
        "unit_weight": "200 г / 500 г / 1 кг / 5 кг",
        "shelf_life": "35 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": True,
        "order": 2,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "slivochnoe-maslo",
        "title": "Масло топленое ГОСТ",
        "slug": "maslo-toplenoe-gost",
        "description": "Традиционное топленое масло (Гхи), янтарный цвет, ореховый аромат. м.д.ж. 99%.",
        "fat_content": "99%",
        "unit_weight": "200 г / 500 г / 1 кг",
        "shelf_life": "90 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 3,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "slivochnoe-maslo",
        "title": "Масло домашнее",
        "slug": "maslo-domashnee",
        "description": "Классическое крестьянское масло с мягким сливочным вкусом и золотистым цветом.",
        "fat_content": "72,5%",
        "unit_weight": "200 г / 500 г",
        "shelf_life": "35 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 4,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "slivochnoe-maslo",
        "title": "Спред сливочно-растительный",
        "slug": "spred-slivochno-rastitelnyj",
        "description": "Высококачественный спред с мягкой пластичной консистенцией, легко намазывается.",
        "fat_content": "72,5%",
        "unit_weight": "200 г / 500 г",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 5,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    # ── КИСЛОМОЛОЧНЫЕ НАПИТКИ ─────────────────────────────────────────────────
    {
        "category_slug": "kislomolochka",
        "title": "Тан газированный",
        "slug": "tan-gazirovannyj",
        "description": "Натуральный газированный кисломолочный напиток из отборного молока с солью и водой.",
        "fat_content": "1,0%",
        "unit_weight": "0,5 л / 1,0 л / 3,0 л",
        "shelf_life": "7 суток",
        "price_display": "По запросу",
        "badge": "Хит",
        "is_featured": True,
        "order": 1,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "kislomolochka",
        "title": "Айран",
        "slug": "ajran",
        "description": "Традиционный кавказский кисломолочный напиток с шелковистой текстурой.",
        "fat_content": "1,0%",
        "unit_weight": "0,5 л / 1,0 л",
        "shelf_life": "7 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": True,
        "order": 2,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "kislomolochka",
        "title": "Тан с огурцом и укропом",
        "slug": "tan-s-ogurcom-i-ukropom",
        "description": "Освежающий кисломолочный напиток с добавлением свежего огурца и укропа.",
        "fat_content": "1,0%",
        "unit_weight": "0,5 л / 1,0 л",
        "shelf_life": "5 суток",
        "price_display": "По запросу",
        "badge": "Новинка",
        "is_featured": False,
        "order": 3,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "kislomolochka",
        "title": "Катык (Мацун)",
        "slug": "katyk-macun",
        "description": "Густой традиционный восточный кисломолочный продукт с кремовой бархатной текстурой.",
        "fat_content": "3,5%",
        "unit_weight": "0,5 кг / 1,0 кг",
        "shelf_life": "10 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 4,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "kislomolochka",
        "title": "Сметанный продукт 20%",
        "slug": "smetannyj-produkt-20",
        "description": "Густой кремовый кисломолочный продукт с нежной бархатистой текстурой, м.д.ж. 20%.",
        "fat_content": "20%",
        "unit_weight": "0,35 кг / 0,5 кг / 5,0 кг",
        "shelf_life": "21 сутки",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 5,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    # ── ПЛАВЛЕНЫЕ СЫРЫ ───────────────────────────────────────────────────────
    {
        "category_slug": "plavlenye-syry",
        "title": "Сыр колбасный копченый",
        "slug": "syr-kolbasnyj-kopchyonyj",
        "description": "Ароматный колбасный сыр с деликатным натуральным копчением.",
        "fat_content": "30%",
        "unit_weight": "250 г / 0,5 кг / 2,0 кг",
        "shelf_life": "60 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 1,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "plavlenye-syry",
        "title": "Сыр плавленый Голландский",
        "slug": "syr-plavlenyj-gollandskij",
        "description": "Термостабильный плавленый сырный продукт с насыщенным вкусом сыра Голландский.",
        "fat_content": "45%",
        "unit_weight": "250 г / 1,0 кг",
        "shelf_life": "90 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 2,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "plavlenye-syry",
        "title": "Сыр плавленый Чеддер",
        "slug": "syr-plavlenyj-chedder",
        "description": "Термостабильный плавленый сырный продукт с ярким вкусом Чеддер.",
        "fat_content": "45%",
        "unit_weight": "250 г / 1,0 кг",
        "shelf_life": "90 суток",
        "price_display": "По запросу",
        "badge": "",
        "is_featured": False,
        "order": 3,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
    {
        "category_slug": "plavlenye-syry",
        "title": "Сыр плавленый Пиццерелла",
        "slug": "syr-plavlenyj-piccerella",
        "description": "Специальный плавленый сыр для пиццы — хорошо плавится, тянется и не горит.",
        "fat_content": "40%",
        "unit_weight": "250 г / 1,0 кг / 5,0 кг",
        "shelf_life": "90 суток",
        "price_display": "По запросу",
        "badge": "Для HoReCa",
        "is_featured": False,
        "order": 4,
        "static_fallback_image": "images/hero_cheese.jpg",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# 2. ДАННЫЕ ДЛЯ ПАРСИНГА С САЙТА
# ═══════════════════════════════════════════════════════════════════════════════

def parse_reviews():
    """Парсит отзывы со страницы /reviews/."""
    print("\n[1/6] Парсим отзывы...")
    page = soup(f"{SITE}/reviews/")
    if not page:
        print("  [SKIP] Страница отзывов недоступна")
        return []

    reviews = []
    # Попробуем разные селекторы
    cards = (
        page.select(".review-card")
        or page.select(".review")
        or page.select("[class*='review']")
        or page.select("blockquote")
        or page.select(".card")
    )
    print(f"  Найдено карточек: {len(cards)}")
    for card in cards[:20]:
        name = ""
        text = ""
        rating = 5

        # Имя
        for sel in [".review-author", ".author", "strong", "h5", "h4", ".name"]:
            el = card.select_one(sel)
            if el:
                name = el.get_text(strip=True)
                break

        # Текст
        for sel in [".review-text", ".review-body", "p", ".text", ".content"]:
            el = card.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if len(t) > 20:
                    text = t
                    break

        if name and text:
            reviews.append({"name": name, "text": text, "rating": rating})
    return reviews


def parse_articles():
    """Парсит статьи со страницы /articles/."""
    print("\n[2/6] Парсим статьи...")
    page = soup(f"{SITE}/articles/")
    if not page:
        print("  [SKIP] Страница статей недоступна")
        return []

    articles = []
    links = page.select("a[href*='/articles/']")
    article_urls = list({
        urljoin(SITE, a["href"])
        for a in links
        if a.get("href") and a["href"] not in ["/articles/", "/articles"]
        and re.search(r'/articles/[\w-]+/?$', a["href"])
    })
    print(f"  Найдено статей: {len(article_urls)}")

    for url in article_urls[:10]:
        a_page = soup(url)
        if not a_page:
            continue

        title = ""
        for sel in ["h1", ".article-title", ".post-title"]:
            el = a_page.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        content = ""
        for sel in [".article-body", ".post-content", ".content", "article", "main"]:
            el = a_page.select_one(sel)
            if el:
                content = el.get_text(separator="\n", strip=True)
                break

        if title:
            slug_part = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
            articles.append({"title": title, "content": content, "slug": slug_part, "url": url})
            print(f"    + {title[:60]}")
        time.sleep(0.5)

    return articles


def parse_catalog_from_site():
    """
    Попытка парсинга каталога с сайта. Если не получится — используем статические данные.
    """
    print("\n[3/6] Парсим каталог с сайта...")
    page = soup(f"{SITE}/catalog/")
    if not page:
        print("  [SKIP] Каталог недоступен, используем встроенные данные")
        return None

    # Проверяем наличие товаров
    product_cards = (
        page.select(".product-card")
        or page.select(".product")
        or page.select("[class*='product']")
        or page.select(".card")
    )
    print(f"  Найдено карточек товаров: {len(product_cards)}")
    return product_cards if product_cards else None


def parse_site_settings():
    """Парсит контактную информацию и общие данные с главной страницы."""
    print("\n[4/6] Парсим настройки сайта с главной...")
    page = soup(SITE)
    if not page:
        print("  [SKIP] Главная страница недоступна")
        return {}

    data = {}

    # Телефон
    phone_el = page.select_one("a[href^='tel:']")
    if phone_el:
        data["phone"] = re.sub(r'[^\d\s\+\-\(\)]', '', phone_el.get_text(strip=True))
        print(f"  Телефон: {data['phone']}")

    # Email
    email_el = page.select_one("a[href^='mailto:']")
    if email_el:
        data["email"] = email_el["href"].replace("mailto:", "").strip()
        print(f"  Email: {data['email']}")

    # Hero заголовок
    h1 = page.select_one("h1")
    if h1:
        data["hero_title"] = h1.get_text(strip=True)[:200]
        print(f"  Hero: {data['hero_title'][:60]}")

    # Адрес
    for pattern in [r'г\.\s*Омск[^<"]{5,80}', r'ул\.[^<"]{5,60}']:
        match = re.search(pattern, page.get_text())
        if match:
            data["address"] = match.group(0).strip()[:255]
            print(f"  Адрес: {data['address']}")
            break

    return data


def parse_and_download_product_images():
    """Пытается найти изображения товаров на сайте."""
    print("\n[5/6] Ищем изображения товаров...")
    page = soup(f"{SITE}/catalog/")
    if not page:
        return {}

    images = {}
    img_tags = page.find_all("img")
    for img in img_tags:
        src = img.get("src") or img.get("data-src") or ""
        alt = (img.get("alt") or "").lower()
        if src and ("product" in src.lower() or "cheese" in src.lower() or "product" in alt or "сыр" in alt):
            images[alt] = src
    print(f"  Найдено изображений: {len(images)}")
    return images


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PRODUCTION FEATURES (преимущества)
# ═══════════════════════════════════════════════════════════════════════════════

FEATURES_DATA = [
    {
        "title": "100% Натуральное молоко",
        "subtitle": "Только отборное молоко от проверенных фермерских хозяйств Омской области без добавления сухого молока",
        "badge": "ГОСТ",
        "icon": "bi-droplet-half",
        "order": 1,
    },
    {
        "title": "Собственное производство в Омске",
        "subtitle": "Сыроварня ТМ «Сибсыр» с 1999 года в Омске: закрытые сыроизготовители, камеры созревания, пастеризация",
        "badge": "Омск",
        "icon": "bi-building",
        "order": 2,
    },
    {
        "title": "Без пальмового масла",
        "subtitle": "Принципиально не используем растительные заменители молочного жира, красители, консерванты и стабилизаторы",
        "badge": "Натурально",
        "icon": "bi-shield-check",
        "order": 3,
    },
    {
        "title": "Стандарты ГОСТ и ТУ",
        "subtitle": "Вся продукция сертифицирована по ТР ТС 033/2013 и ТР ТС 021/2011. Жёсткий контроль качества на каждом этапе",
        "badge": "Сертификат",
        "icon": "bi-award",
        "order": 4,
    },
    {
        "title": "Доставка с контролем холодовой цепи",
        "subtitle": "Собственные авторефрижераторы поддерживают температуру +2...+4 °C по всему маршруту доставки",
        "badge": "+2...+4°C",
        "icon": "bi-truck",
        "order": 5,
    },
    {
        "title": "Более 25 лет на рынке",
        "subtitle": "С 1999 года — надёжный поставщик для магазинов, сетей и ресторанов Сибири, Урала и всей России",
        "badge": "25+ лет",
        "icon": "bi-clock-history",
        "order": 6,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ОТЗЫВЫ — статические данные
# ═══════════════════════════════════════════════════════════════════════════════

REVIEWS_DATA = [
    {
        "author_name": "Алексей Петров",
        "author_type": "Розничный покупатель",
        "text": "Покупаю сулугуни «Сибсыр» уже несколько лет. Качество стабильное, вкус отличный — настоящий, без лишних добавок. Идеально подходит для хачапури, плавится равномерно.",
        "rating": 5,
        "product_name": "Сыр Сулугуни",
        "is_approved": True,
        "is_featured": True,
    },
    {
        "author_name": "Марина Сидорова",
        "author_type": "Шеф-повар",
        "text": "Работаю шеф-поваром в ресторане. Используем масло сливочное 82,5% «Сибсыр» для соусов и выпечки. Превосходный сливочный аромат, пластичная консистенция. Очень рекомендую профессионалам!",
        "rating": 5,
        "product_name": "Масло сливочное ГОСТ 82,5%",
        "is_approved": True,
        "is_featured": True,
    },
    {
        "author_name": "ИП Корнилов А.В.",
        "author_type": "Оптовый покупатель",
        "text": "Сотрудничаем с «Сибсыр» по оптовым поставкам уже 5 лет. Брынза и адыгейский сыр у нас в постоянном ассортименте. Стабильное качество, точные поставки по графику.",
        "rating": 5,
        "product_name": "Сыр Брынза",
        "is_approved": True,
        "is_featured": True,
    },
    {
        "author_name": "Ольга Иванова",
        "author_type": "Постоянный покупатель",
        "text": "Открыла для себя Тан «Сибсыр» прошлым летом. Натуральный состав, настоящий кисломолочный вкус — освежает лучше любой газировки. Беру регулярно для всей семьи.",
        "rating": 5,
        "product_name": "Тан газированный",
        "is_approved": True,
        "is_featured": False,
    },
    {
        "author_name": "Дмитрий Козлов",
        "author_type": "Покупатель",
        "text": "Заказывал косичку копченую для корпоратива — гости в восторге. Нити ровные, аромат натурального дыма, не пересоленная. Теперь беру регулярно.",
        "rating": 5,
        "product_name": "Сыр Косичка копченая",
        "is_approved": True,
        "is_featured": False,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. СОЦИАЛЬНЫЕ СЕТИ
# ═══════════════════════════════════════════════════════════════════════════════

SOCIAL_DATA = [
    {"name": "ВКонтакте", "url": "https://vk.com/sibsyr", "icon": "bi-vk", "order": 1},
    {"name": "Telegram", "url": "https://t.me/sibsyr", "icon": "bi-telegram", "order": 2},
    {"name": "WhatsApp", "url": "https://wa.me/73812433536", "icon": "bi-whatsapp", "order": 3},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  ПАРСИНГ И ЗАГРУЗКА ДАННЫХ SIBSIR.RU → Django DB")
    print("=" * 65)

    # ── Попробуем получить данные с сайта ────────────────────────────────────
    site_settings_data = parse_site_settings()
    parsed_reviews = parse_reviews()
    parsed_articles = parse_articles()
    parse_catalog_from_site()   # Диагностика, основные данные - статические

    # ── 1. КАТЕГОРИИ ─────────────────────────────────────────────────────────
    print("\n[CAT] Создаём категории...")
    cat_map = {}
    for cd in STATIC_CATEGORIES:
        obj, created = Category.objects.get_or_create(
            slug=cd["slug"],
            defaults={
                "name": cd["name"],
                "description": cd["description"],
                "icon": cd["icon"],
                "order": cd["order"],
                "is_active": True,
            }
        )
        if not created:
            obj.name = cd["name"]
            obj.description = cd["description"]
            obj.icon = cd["icon"]
            obj.order = cd["order"]
            obj.save()
        cat_map[cd["slug"]] = obj
        print(f"  {'✓ создана' if created else '↺ обновлена'}: {obj.name}")

    # ── 2. ТОВАРЫ ─────────────────────────────────────────────────────────────
    print(f"\n[PROD] Создаём {len(PRODUCTS_DATA)} товаров...")
    for pd in PRODUCTS_DATA:
        cat = cat_map.get(pd["category_slug"])
        obj, created = Product.objects.get_or_create(
            slug=pd["slug"],
            defaults={
                "category": cat,
                "title": pd["title"],
                "description": pd["description"],
                "fat_content": pd.get("fat_content", ""),
                "unit_weight": pd.get("unit_weight", ""),
                "shelf_life": pd.get("shelf_life", ""),
                "price_display": pd.get("price_display", "По запросу"),
                "badge": pd.get("badge", ""),
                "is_featured": pd.get("is_featured", True),
                "order": pd.get("order", 0),
                "static_fallback_image": pd.get("static_fallback_image", ""),
                "is_active": True,
            }
        )
        if not created:
            obj.category = cat
            obj.title = pd["title"]
            obj.description = pd["description"]
            obj.fat_content = pd.get("fat_content", "")
            obj.unit_weight = pd.get("unit_weight", "")
            obj.shelf_life = pd.get("shelf_life", "")
            obj.price_display = pd.get("price_display", "По запросу")
            obj.badge = pd.get("badge", "")
            obj.is_featured = pd.get("is_featured", True)
            obj.order = pd.get("order", 0)
            obj.static_fallback_image = pd.get("static_fallback_image", "")
            obj.save()
        action = "✓ создан" if created else "↺ обновлён"
        print(f"  {action}: {obj.title}")

    # ── 3. ПРЕИМУЩЕСТВА ───────────────────────────────────────────────────────
    print("\n[FEAT] Создаём преимущества производства...")
    try:
        for fd in FEATURES_DATA:
            obj, created = ProductionFeature.objects.get_or_create(
                title=fd["title"],
                defaults={
                    "subtitle": fd["subtitle"],
                    "badge": fd["badge"],
                    "icon": fd["icon"],
                    "order": fd["order"],
                }
            )
            if not created:
                obj.subtitle = fd["subtitle"]
                obj.badge = fd["badge"]
                obj.icon = fd["icon"]
                obj.order = fd["order"]
                obj.save()
            print(f"  {'✓' if created else '↺'}: {obj.title}")
    except Exception as e:
        print(f"  [WARN] ProductionFeature: {e}")

    # ── 4. ОТЗЫВЫ ─────────────────────────────────────────────────────────────
    print("\n[REV] Загружаем отзывы...")
    # Сначала используем спарсенные, потом статические
    all_reviews = parsed_reviews + [r for r in REVIEWS_DATA if r["author_name"] not in [p.get("name") for p in parsed_reviews]]
    reviews_created = 0
    try:
        for rd in all_reviews[:20]:
            name = rd.get("author_name") or rd.get("name", "Покупатель")
            text = rd.get("text", "")
            if not text or len(text) < 10:
                continue

            # Проверяем дубликаты
            if Review.objects.filter(author_name=name, text__startswith=text[:50]).exists():
                print(f"  → уже есть: {name}")
                continue

            defaults = {
                "text": text,
                "rating": rd.get("rating", 5),
                "is_approved": rd.get("is_approved", True),
                "is_featured": rd.get("is_featured", False),
            }
            if rd.get("author_type"):
                defaults["author_type"] = rd["author_type"]
            if rd.get("product_name"):
                defaults["product_name"] = rd["product_name"]

            obj = Review.objects.create(author_name=name, **defaults)
            reviews_created += 1
            print(f"  ✓ {name}: {text[:60]}...")
    except Exception as e:
        print(f"  [WARN] Review: {e}")
        import traceback; traceback.print_exc()

    print(f"  Создано отзывов: {reviews_created}")

    # ── 5. СТАТЬИ ─────────────────────────────────────────────────────────────
    if parsed_articles:
        print(f"\n[ART] Загружаем {len(parsed_articles)} статей...")
        try:
            for ad in parsed_articles:
                obj, created = Article.objects.get_or_create(
                    slug=ad["slug"],
                    defaults={
                        "title": ad["title"],
                        "content": ad["content"],
                        "is_published": True,
                    }
                )
                print(f"  {'✓' if created else '↺'}: {ad['title'][:60]}")
        except Exception as e:
            print(f"  [WARN] Article: {e}")

    # ── 6. СОЦИАЛЬНЫЕ СЕТИ ────────────────────────────────────────────────────
    print("\n[SOC] Создаём ссылки на соцсети...")
    try:
        for sd in SOCIAL_DATA:
            obj, created = SocialLink.objects.get_or_create(
                url=sd["url"],
                defaults={
                    "name": sd["name"],
                    "icon": sd["icon"],
                    "order": sd["order"],
                    "is_active": True,
                }
            )
            if not created:
                obj.name = sd["name"]
                obj.icon = sd["icon"]
                obj.order = sd["order"]
                obj.save()
            print(f"  {'✓' if created else '↺'}: {obj.name}")
    except Exception as e:
        print(f"  [WARN] SocialLink: {e}")

    # ── 7. НАСТРОЙКИ САЙТА ────────────────────────────────────────────────────
    print("\n[CFG] Обновляем настройки сайта...")
    try:
        settings = SiteSettings.get_solo()
        # Из парсинга (если нашли)
        if site_settings_data.get("phone"):
            settings.phone = site_settings_data["phone"]
        if site_settings_data.get("email"):
            settings.email = site_settings_data["email"]
        if site_settings_data.get("hero_title"):
            settings.hero_title = site_settings_data["hero_title"]
        if site_settings_data.get("address"):
            settings.address = site_settings_data["address"]

        # SEO заполнение
        settings.fill_default_static_seo(overwrite=False)
        settings.save()
        print("  ✓ SiteSettings обновлены")
    except Exception as e:
        print(f"  [WARN] SiteSettings: {e}")

    # ── Итог ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  ИТОГ:")
    print(f"  Категорий: {Category.objects.count()}")
    print(f"  Товаров:   {Product.objects.count()}")
    try:
        print(f"  Отзывов:   {Review.objects.count()}")
    except:
        pass
    try:
        print(f"  Статей:    {Article.objects.count()}")
    except:
        pass
    print("=" * 65)
    print("  ✅ Готово! Данные загружены в БД.")
    print("=" * 65)


if __name__ == "__main__":
    main()

