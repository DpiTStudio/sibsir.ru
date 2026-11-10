from django.test import TestCase, Client
from django.urls import reverse
from shop.models import Category, Product
from main.models import SiteSettings, FooterStatBanner


class CatalogPaginationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Тестовые сыры", slug="test-cheese", is_active=True)
        # Create 20 products
        for i in range(1, 21):
            Product.objects.create(
                category=self.cat,
                title=f"Продукт {i}",
                slug=f"product-{i}",
                price_display=f"{100 * i} ₽",
                price_numeric=100 * i,
                is_active=True,
                order=i,
            )

    def test_catalog_page_1(self):
        res = self.client.get(reverse("main:catalog"), HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["page_size"], 9)
        self.assertEqual(res.context["current_page"], 1)
        self.assertEqual(res.context["total_pages"], 3)  # 20 items / 9 = 3 pages
        self.assertEqual(res.context["start_product_idx"], 1)
        self.assertEqual(res.context["end_product_idx"], 9)
        html = res.content.decode("utf-8")
        self.assertIn("catalogPaginationNav", html)
        self.assertIn("9 товаров на страницу", html)
        self.assertIn("goToPage", html)
        self.assertIn("ITEMS_PER_PAGE = 9", html)

    def test_catalog_page_2(self):
        res = self.client.get(reverse("main:catalog") + "?page=2", HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_page"], 2)
        self.assertEqual(res.context["start_product_idx"], 10)
        self.assertEqual(res.context["end_product_idx"], 18)

    def test_catalog_page_3(self):
        res = self.client.get(reverse("main:catalog") + "?page=3", HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_page"], 3)
        self.assertEqual(res.context["start_product_idx"], 19)
        self.assertEqual(res.context["end_product_idx"], 20)

    def test_catalog_category_filtering(self):
        res_cat = self.client.get(reverse("main:catalog") + "?cat=test-cheese", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_cat.status_code, 200)
        self.assertEqual(res_cat.context["selected_cat"], "test-cheese")

        res_category = self.client.get(reverse("main:catalog") + "?category=test-cheese", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_category.status_code, 200)
        self.assertEqual(res_category.context["selected_cat"], "test-cheese")


class CoreSiteEndpointsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_favicon_ico(self):
        res = self.client.get("/favicon.ico", HTTP_HOST="127.0.0.1")
        self.assertIn(res.status_code, [200, 302])

    def test_robots_txt(self):
        res = self.client.get("/robots.txt", HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("User-agent", res.content.decode("utf-8"))

    def test_sitemap_xml(self):
        res = self.client.get("/sitemap.xml", HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("urlset", res.content.decode("utf-8"))


class FooterStatBannerTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_stat_banner_rendering_in_footer(self):
        # 1. Создаем активный баннер-информер с HTML кодом
        banner_code = FooterStatBanner.objects.create(
            name="Яндекс Метрика Информер",
            banner_type=FooterStatBanner.BANNER_TYPE_HTML,
            html_code='<a id="ym-informer" href="https://metrika.yandex.ru"><img src="https://informer.yandex.ru/informer" alt="Яндекс.Метрика" /></a>',
            order=1,
            is_active=True
        )

        # 2. Создаем активный графический баннер со ссылкой
        banner_img = FooterStatBanner.objects.create(
            name="LiveInternet",
            banner_type=FooterStatBanner.BANNER_TYPE_IMAGE,
            url="https://www.liveinternet.ru/click",
            alt_text="LiveInternet: число просмотров за 24 часа",
            order=2,
            is_active=True
        )

        # 3. Создаем неактивный баннер (не должен отображаться)
        banner_hidden = FooterStatBanner.objects.create(
            name="Скрытый баннер",
            banner_type=FooterStatBanner.BANNER_TYPE_HTML,
            html_code='<span id="hidden-counter">Hidden</span>',
            order=3,
            is_active=False
        )

        # Запрашиваем страницу сайта
        res = self.client.get(reverse("main:index"), HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
        
        # Проверяем, что контекст-процессор передал список баннеров
        banners_in_context = res.context["footer_stat_banners"]
        self.assertEqual(len(banners_in_context), 2)
        self.assertIn(banner_code, banners_in_context)
        self.assertIn(banner_img, banners_in_context)
        self.assertNotIn(banner_hidden, banners_in_context)

        # Проверяем HTML-вывод в подвале
        content = res.content.decode("utf-8")
        self.assertIn('ym-informer', content)
        self.assertIn('https://www.liveinternet.ru/click', content)
        self.assertIn('LiveInternet: число просмотров за 24 часа', content)
        self.assertNotIn('hidden-counter', content)

