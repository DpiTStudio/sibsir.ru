from django.db import models
from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone


class SiteSettings(models.Model):
    brand_name = models.CharField(
        max_length=150, 
        default="ТМ «Сибсыр» ИП Нахшкарян А.Л.", 
        verbose_name="Полное наименование бренда"
    )
    brand_short_name = models.CharField(
        max_length=50,
        default="Сибсыр",
        verbose_name="Краткое название бренда"
    )
    logo = models.FileField(
        upload_to="branding/",
        blank=True,
        null=True,
        verbose_name="Логотип сайта (PNG, SVG, JPG, WebP)",
        help_text="Отображается в шапке сайта, подвале и печатных документах. Рекомендуется прозрачный фон."
    )
    favicon = models.FileField(
        upload_to="branding/",
        blank=True,
        null=True,
        verbose_name="Фавикон сайта (ICO, PNG, SVG)",
        help_text="Иконка во вкладке браузера (.ico, .png, .svg)"
    )
    hero_title = models.CharField(
        max_length=200, 
        default="Здесь делают сыр", 
        verbose_name="Главный заголовок"
    )
    hero_subtitle = models.TextField(
        default="Компания «СибСыр» уже более 25 лет поставляет натуральные сыры, сливочное масло и кисломолочную продукцию высочайшего качества.", 
        verbose_name="Подзаголовок"
    )
    hero_badge_text = models.CharField(
        max_length=150, 
        default="Собственное производство • 100% натуральное молоко", 
        verbose_name="Текст бейджа на главном баннере"
    )
    hero_image = models.ImageField(
        upload_to="hero/", 
        blank=True, 
        null=True, 
        verbose_name="Главное фото (Hero)"
    )
    cta_button_text = models.CharField(
        max_length=50, 
        default="Перейти в каталог", 
        verbose_name="Текст главной кнопки (CTA)"
    )
    phone = models.CharField(
        max_length=50, 
        default="8 (3812) 43-35-36", 
        blank=True, 
        verbose_name="Контактный телефон"
    )
    email = models.CharField(
        max_length=100, 
        default="sibs@list.ru", 
        blank=True, 
        verbose_name="Контактный E-mail"
    )
    address = models.CharField(
        max_length=255, 
        default="г. Омск, ул. Зеленая, 16", 
        blank=True, 
        verbose_name="Адрес производства и офиса"
    )
    working_hours = models.CharField(
        max_length=150,
        default="Пн-Пт: 8:00 - 17:00, Сб: 8:00 - 14:00",
        blank=True,
        verbose_name="Режим работы"
    )
    inn_kpp = models.CharField(
        max_length=150,
        default="ИП Нахшкарян А.Л. / ТМ «Сибсыр»",
        blank=True,
        verbose_name="Реквизиты (Юр. лицо)"
    )
    # Расширенные реквизиты для накладных, счетов и чеков
    seller_inn = models.CharField(
        max_length=30,
        default="550119874521",
        blank=True,
        verbose_name="ИНН продавца"
    )
    seller_ogrn = models.CharField(
        max_length=30,
        default="318554300045612",
        blank=True,
        verbose_name="ОГРНИП / ОГРН"
    )
    seller_bank = models.CharField(
        max_length=200,
        default="Омское отделение №8634 ПАО Сбербанк г. Омск",
        blank=True,
        verbose_name="Банк продавца"
    )
    seller_bik = models.CharField(
        max_length=20,
        default="045209673",
        blank=True,
        verbose_name="БИК банка"
    )
    seller_account = models.CharField(
        max_length=30,
        default="40802810445000012345",
        blank=True,
        verbose_name="Расчетный счет (р/с)"
    )
    seller_corr_account = models.CharField(
        max_length=30,
        default="30101810900000000673",
        blank=True,
        verbose_name="Корреспондентский счет (к/с)"
    )
    seller_okpo = models.CharField(
        max_length=20,
        default="01928374",
        blank=True,
        verbose_name="Код ОКПО"
    )
    seller_director = models.CharField(
        max_length=150,
        default="Нахшкарян А.Л.",
        blank=True,
        verbose_name="ФИО руководителя / ИП"
    )
    seller_accountant = models.CharField(
        max_length=150,
        default="Нахшкарян А.Л.",
        blank=True,
        verbose_name="Главный бухгалтер"
    )
    about_hero_badge = models.CharField(
        max_length=150,
        default="ТМ «Сибсыр» • Сыродельное производство в Омске с 1999 года",
        verbose_name="Бейдж шапки «О компании»"
    )
    about_heading = models.CharField(
        max_length=200,
        default="О компании «Сибсыр» — качество и традиции",
        verbose_name="Заголовок блока «О компании»"
    )
    about_text = models.TextField(
        default="Компания «СибСыр» уже более 25 лет поставляет кисломолочные продукты, рассольные и мягкие сыры, сливочное и топленое масло высочайшего качества. Вся наша продукция изготавливается исключительно из натурального отборного молока от проверенных фермерских хозяйств с применением классических и авторских технологий.",
        verbose_name="Текст о компании"
    )
    about_image = models.ImageField(
        upload_to="about/",
        blank=True,
        null=True,
        verbose_name="Фото раздела «О компании» (производство/сыроварня)"
    )
    about_stat_1_val = models.CharField(max_length=50, default="25+", verbose_name="Статистика 1: Значение")
    about_stat_1_label = models.CharField(max_length=100, default="Лет на рынке", verbose_name="Статистика 1: Подпись")
    about_stat_2_val = models.CharField(max_length=50, default="47", verbose_name="Статистика 2: Значение")
    about_stat_2_label = models.CharField(max_length=100, default="Видов товаров", verbose_name="Статистика 2: Подпись")
    about_stat_3_val = models.CharField(max_length=50, default="100%", verbose_name="Статистика 3: Значение")
    about_stat_3_label = models.CharField(max_length=100, default="Свежее молоко", verbose_name="Статистика 3: Подпись")
    about_stat_4_val = models.CharField(max_length=50, default=">500", verbose_name="Статистика 4: Значение")
    about_stat_4_label = models.CharField(max_length=100, default="Партнеров", verbose_name="Статистика 4: Подпись")
    about_tech_heading = models.CharField(
        max_length=200,
        default="Современные технологии и вековые традиции сыроварения",
        verbose_name="Заголовок блока технологий и оборудования"
    )
    about_tech_text_1 = models.TextField(
        default="Сыроварня ТМ «Сибсыр» расположена в экологически чистом регионе Западной Сибири (г. Омск). Производственный комплекс оснащен высокотехнологичным оборудованием: закрытыми сыроизготовителями, пастеризационно-охладительными установками и специализированными климатическими камерами созревания сыра.",
        verbose_name="Текст технологий (абзац 1)"
    )
    about_tech_text_2 = models.TextField(
        default="Мы принципиально не используем искусственные красители, консерванты, стабилизаторы или растительные заменители молочного жира (пальмовое масло). В основе рецептур — классические стандарты ГОСТ и многолетний практический опыт наших мастеров-сыроваров.",
        verbose_name="Текст технологий (абзац 2)"
    )
    about_safety_heading = models.CharField(
        max_length=200,
        default="Сертификация ГОСТ и ТУ",
        verbose_name="Заголовок блока безопасности и сертификатов"
    )
    about_safety_text = models.TextField(
        default="Вся выпускаемая продукция сертифицирована в соответствии с техническими регламентами Таможенного союза ТР ТС 033/2013 «О безопасности молока и молочной продукции» и ТР ТС 021/2011 «О безопасности пищевой продукции».",
        verbose_name="Текст регламентов и безопасности"
    )

    # ------------------ ДОСТАВКА И ОПЛАТА ------------------
    delivery_hero_badge = models.CharField(
        max_length=150,
        default="Контроль холодовой цепи (+2...+4 °C) • Собственные рефрижераторы",
        verbose_name="Бейдж страницы доставки"
    )
    delivery_hero_title = models.CharField(
        max_length=200,
        default="Условия доставки и оплаты продукции «Сибсыр»",
        verbose_name="Заголовок страницы доставки"
    )
    delivery_text = models.TextField(
        default="Доставка продукции осуществляется специализированным автотранспортом с соблюдением строгого температурного режима по Омску, Омской области и регионам РФ. Для оптовых покупателей и сетей действуют индивидуальные условия и гибкий график поставок.",
        verbose_name="Условия доставки и оплаты"
    )
    delivery_cold_chain_title = models.CharField(
        max_length=200,
        default="Как мы сохраняем свежесть сыров при доставке",
        verbose_name="Заголовок блока холодовой цепи"
    )
    delivery_cold_chain_text = models.TextField(
        default="Сыры и молочная продукция — живые скоропортящиеся продукты. Разрыв температурной цепочки недопустим. Именно поэтому на заводе ТМ «Сибсыр» выстроена комплексная система контроля качества на всех этапах перевозки.",
        verbose_name="Текст блока холодовой цепи"
    )
    delivery_cold_chain_image = models.ImageField(
        upload_to="delivery/",
        blank=True,
        null=True,
        verbose_name="Иллюстрация / фото доставки"
    )
    price_list_file = models.FileField(
        upload_to="documents/",
        blank=True,
        null=True,
        verbose_name="Файл прайс-листа (Excel/PDF)"
    )
    wholesale_email_subject = models.CharField(
        max_length=255,
        default="Оптовый прайс-лист ТМ «Сибсыр» и коммерческие условия",
        verbose_name="Тема письма с оптовым прайс-листом"
    )
    wholesale_email_body = models.TextField(
        default=(
            "Здравствуйте, {name}!\n\n"
            "Благодарим вас за интерес к сыроваренной продукции ТМ «Сибсыр».\n\n"
            "Направляем вам актуальный оптовый прайс-лист на всю производимую линейку продукции "
            "(рассольные и полутвердые сыры, сливочное масло, снеки).\n\n"
            "Наши ключевые преимущества для оптовых партнеров и сетей:\n"
            "• Прямые поставки от завода-производителя без посредников;\n"
            "• Соблюдение холодовой цепи (+2...+4°C) специализированным автотранспортом;\n"
            "• Полный пакет закрывающих документов, ветеринарные справки ФГИС «Меркурий»;\n"
            "• Гибкие индивидуальные условия и график отгрузок при регулярных объемах.\n\n"
            "Для согласования заказа, графика поставок и индивидуальных условий свяжитесь с отделом продаж:\n"
            "Телефон: {phone}\n"
            "E-mail: {email}\n"
            "Адрес производства и склада: {address}\n\n"
            "С уважением, отдел оптовых продаж ТМ «Сибсыр»"
        ),
        verbose_name="Шаблон письма с оптовым прайс-листом",
        help_text="Доступные переменные: {name}, {company}, {phone}, {email}, {address}, {date}"
    )

    # ------------------ ОТЗЫВЫ ------------------
    reviews_hero_badge = models.CharField(
        max_length=150,
        default="Доверие покупателей и розничных сетей • Более 25 лет качества",
        verbose_name="Бейдж страницы отзывов"
    )
    reviews_hero_title = models.CharField(
        max_length=200,
        default="Отзывы о продукции ТМ «Сибсыр»",
        verbose_name="Заголовок страницы отзывов"
    )
    reviews_hero_subtitle = models.TextField(
        default="Мы гордимся тем, что сыры и масло ТМ «Сибсыр» выбирают тысячи семей, шеф-поваров и владельцев магазинов в Омске и по всей России. Ознакомьтесь с отзывами или поделитесь своим мнением о нашей продукции.",
        verbose_name="Подзаголовок страницы отзывов"
    )
    reviews_recommend_percent = models.CharField(
        max_length=20,
        default="98%",
        verbose_name="Процент рекомендаций (бейдж рейтинга)"
    )

    # ------------------ КОНТАКТЫ ------------------
    contacts_hero_badge = models.CharField(
        max_length=150,
        default="Официальные контакты ТМ «Сибсыр» • Омск",
        verbose_name="Бейдж страницы контактов"
    )
    contacts_hero_title = models.CharField(
        max_length=200,
        default="Контакты завода и отдела продаж «Сибсыр»",
        verbose_name="Заголовок страницы контактов"
    )
    contacts_hero_subtitle = models.TextField(
        default="Производственная площадка, центральный склад и офис компании расположены в Омске. Мы осуществляем прямые оптовые поставки сыров и молочной продукции по Сибири, Уралу и всем регионам РФ, а также работаем с розничными клиентами.",
        verbose_name="Подзаголовок страницы контактов"
    )
    yandex_map_iframe_url = models.TextField(
        default="https://yandex.ru/map-widget/v1/?ll=73.3682%2C54.9893&z=15&pt=73.3682%2C54.9893~pm2wtm",
        verbose_name="Ссылка для iframe виджета Яндекс Карт"
    )
    pickup_coordinates = models.CharField(
        max_length=50,
        default="54.9893, 73.3682",
        verbose_name="GPS-координаты завода"
    )
    pickup_instructions_truck = models.TextField(
        default="Удобный съезд, широкая маневровая площадка перед пандусами отгрузки. Оформление пропусков на КПП.",
        verbose_name="Инструкция проезда для грузового транспорта"
    )
    pickup_instructions_car = models.TextField(
        default="Бесплатная парковка для легковых автомобилей рядом с административным корпусом.",
        verbose_name="Инструкция проезда для легкового транспорта"
    )

    # ------------------ КАТАЛОГ ------------------
    catalog_badge_text = models.CharField(
        max_length=150,
        default="Прямые поставки с сыродельного завода • Омск",
        verbose_name="Бейдж шапки каталога"
    )
    catalog_title = models.CharField(
        max_length=200,
        default="Каталог продукции ТМ «Сибсыр»",
        verbose_name="Главный заголовок каталога"
    )
    catalog_subtitle = models.TextField(
        default="Полный ассортимент натуральных сыров, свежего сливочного масла и традиционных кисломолочных напитков. Изготовлено по ГОСТ и ТУ из отборного молока.",
        verbose_name="Описание каталога"
    )
    catalog_search_placeholder = models.CharField(
        max_length=150,
        default="Название сыра, фасовка, жирность...",
        verbose_name="Плейсхолдер поиска в каталоге"
    )
    catalog_banner_image = models.ImageField(
        upload_to="catalog/",
        blank=True,
        null=True,
        verbose_name="Фоновый баннер каталога"
    )

    # ------------------ ПРЕИМУЩЕСТВА ------------------
    features_badge = models.CharField(
        max_length=150,
        default="Наши стандарты",
        verbose_name="Бейдж секции преимуществ"
    )
    features_title = models.CharField(
        max_length=200,
        default="Почему выбирают ТМ «Сибсыр»",
        verbose_name="Заголовок секции преимуществ"
    )

    # Настройки капчи и защиты от спама
    captcha_enabled = models.BooleanField(
        default=True,
        verbose_name="Включить защиту капчей (глобально)",
        help_text="Если отключено, проверка капчи не будет требоваться ни в одной из форм"
    )
    captcha_type = models.CharField(
        max_length=20,
        choices=[
            ("math", "Математический пример (14 + 7 = ?)"),
            ("image", "Графический буквенно-цифровой код (картинка с искажением)"),
        ],
        default="math",
        verbose_name="Тип проверки капчи",
        help_text="Выберите подходящий формат капчи для ваших клиентов"
    )
    captcha_on_register = models.BooleanField(
        default=True,
        verbose_name="Капча при регистрации (физлица и юрлица)",
        help_text="Защита формы создания аккаунта розничного покупателя и B2B кабинета"
    )
    captcha_on_login = models.BooleanField(
        default=True,
        verbose_name="Капча при входе в личный кабинет",
        help_text="Защита формы авторизации от подбора паролей (брутфорса)"
    )
    captcha_on_admin_login = models.BooleanField(
        default=True,
        verbose_name="Капча при входе в панель администратора",
        help_text="Защита формы авторизации в панель управления /admin/ от подбора паролей"
    )
    captcha_on_callback = models.BooleanField(
        default=True,
        verbose_name="Капча при отправке сообщений и заявок на звонок",
        help_text="Защита модальных окон и форм обратной связи от спам-ботов"
    )
    captcha_on_guest_order = models.BooleanField(
        default=True,
        verbose_name="Капча при оформлении заказа незарегистрированными клиентами",
        help_text="Защита быстрого заказа и корзины для гостей сайта (авторизованные пользователи оформляют без капчи)"
    )

    # ------------------ SEO И ПОИСКОВАЯ ОПТИМИЗАЦИЯ ------------------
    # Общие параметры поисковой оптимизации
    seo_title_template = models.CharField(
        max_length=200, 
        default="{title} — ТМ «Сибсыр» | Омск", 
        verbose_name="Шаблон Meta Title",
        help_text="Используйте переменные {title} и {brand}. Например: {title} — {brand} | Омск"
    )
    seo_default_description = models.TextField(
        default="Производитель сыров, сливочного масла, кисломолочной и молочной продукции Сибсыр в Омске. Оптовые и розничные поставки по всей России. Гарантия качества по ГОСТ.",
        verbose_name="Meta Description по умолчанию",
        help_text="Базовое описание сайта для поисковиков (если на странице не задано персональное)"
    )
    seo_default_keywords = models.TextField(
        default="Сибсыр, аревтур, сыр омск, купить сыр оптом, производитель сыра, сулугуни, адыгейский, брынза, масло сливочное гост, тан, айран",
        verbose_name="Meta Keywords по умолчанию",
        help_text="Базовые ключевые слова через запятую"
    )
    site_base_url = models.CharField(
        max_length=150,
        default="https://sibsir.ru",
        verbose_name="Основной домен сайта (для Sitemap и Canonical)",
        help_text="Например: https://sibsir.ru (без завершающего слэша)"
    )
    seo_og_image = models.ImageField(
        upload_to="seo/",
        blank=True,
        null=True,
        verbose_name="Изображение для соцсетей по умолчанию (OpenGraph)",
        help_text="Используется при отправке ссылок в Telegram, WhatsApp, VK. Рекомендуется 1200x630 px"
    )
    robots_txt_content = models.TextField(
        blank=True,
        verbose_name="Пользовательский файл robots.txt",
        help_text="Если поле пустое, сайт генерирует рекомендуемый правильный robots.txt автоматически со ссылкой на sitemap.xml"
    )
    is_indexing_enabled = models.BooleanField(
        default=True,
        verbose_name="Разрешить индексацию сайта поисковыми системами",
        help_text="Если выключено, robots.txt и метатеги запретят индексацию роботам (noindex, nofollow)"
    )

    # Вебмастер и веб-аналитика
    yandex_verification_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Код подтверждения Яндекс.Вебмастер",
        help_text="Значение из тега <meta name=\"yandex-verification\" content=\"...\">"
    )
    google_verification_code = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Код подтверждения Google Search Console",
        help_text="Значение из тега <meta name=\"google-site-verification\" content=\"...\">"
    )
    yandex_metrika_id = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Номер счетчика Яндекс.Метрики",
        help_text="Например: 98765432. Если заполнено, код Метрики с вебвизором будет встроен автоматически"
    )
    custom_head_scripts = models.TextField(
        blank=True,
        verbose_name="Пользовательские скрипты в <head>",
        help_text="HTML/JS-код счетчиков, пикселей (VK, Mail.ru) или Google Tag Manager"
    )
    custom_body_scripts = models.TextField(
        blank=True,
        verbose_name="Пользовательские скрипты перед </body>",
        help_text="HTML/JS-код онлайн-консультантов, виджетов звонков или отслеживания"
    )

    # Индивидуальные SEO-теги статических страниц сайта
    seo_home_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Главная: Meta Title",
        help_text="Заголовок главной страницы во вкладке браузера и выдаче поисковиков"
    )
    seo_home_description = models.TextField(
        blank=True, 
        verbose_name="Главная: Meta Description",
        help_text="Краткое описание главной страницы для сниппета Яндекса и Google"
    )
    seo_home_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Главная: Meta Keywords"
    )

    seo_catalog_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Каталог: Meta Title"
    )
    seo_catalog_description = models.TextField(
        blank=True, 
        verbose_name="Каталог: Meta Description"
    )
    seo_catalog_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Каталог: Meta Keywords"
    )

    seo_categories_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Категории: Meta Title"
    )
    seo_categories_description = models.TextField(
        blank=True, 
        verbose_name="Категории: Meta Description"
    )
    seo_categories_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Категории: Meta Keywords"
    )

    seo_about_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="О компании: Meta Title"
    )
    seo_about_description = models.TextField(
        blank=True, 
        verbose_name="О компании: Meta Description"
    )
    seo_about_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="О компании: Meta Keywords"
    )

    seo_delivery_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Доставка и оплата: Meta Title"
    )
    seo_delivery_description = models.TextField(
        blank=True, 
        verbose_name="Доставка и оплата: Meta Description"
    )
    seo_delivery_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Доставка и оплата: Meta Keywords"
    )

    seo_contacts_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Контакты: Meta Title"
    )
    seo_contacts_description = models.TextField(
        blank=True, 
        verbose_name="Контакты: Meta Description"
    )
    seo_contacts_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Контакты: Meta Keywords"
    )

    seo_reviews_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Отзывы: Meta Title"
    )
    seo_reviews_description = models.TextField(
        blank=True, 
        verbose_name="Отзывы: Meta Description"
    )
    seo_reviews_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Отзывы: Meta Keywords"
    )

    seo_articles_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Статьи и блог: Meta Title"
    )
    seo_articles_description = models.TextField(
        blank=True, 
        verbose_name="Статьи и блог: Meta Description"
    )
    seo_articles_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Статьи и блог: Meta Keywords"
    )

    seo_faq_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Вопрос-ответ (FAQ): Meta Title"
    )
    seo_faq_description = models.TextField(
        blank=True, 
        verbose_name="Вопрос-ответ (FAQ): Meta Description"
    )
    seo_faq_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Вопрос-ответ (FAQ): Meta Keywords"
    )

    def is_captcha_required(self, form_type, user=None):
        """Проверяет, требуется ли прохождение капчи для указанной формы."""
        if not self.captcha_enabled:
            return False
        if form_type == "register":
            return bool(self.captcha_on_register)
        elif form_type == "login":
            return bool(self.captcha_on_login)
        elif form_type == "admin_login":
            return bool(getattr(self, "captcha_on_admin_login", True))
        elif form_type in ("callback", "review"):
            return bool(self.captcha_on_callback)
        elif form_type == "order":
            if user and getattr(user, "is_authenticated", False):
                return False
            return bool(self.captcha_on_guest_order)
        return False

    def fill_default_static_seo(self, overwrite=False):
        """
        Заполняет SEO-теги для всех статических страниц высококонверсионными
        стандартными значениями для продвижения в Омске и РФ.
        """
        brand = self.brand_short_name or "Сибсыр"
        full_brand = self.brand_name or "ТМ «Сибсыр»"

        defaults = {
            "seo_home_title": f"{full_brand} — Производитель сыров и молочной продукции в Омске | Купить оптом и в розницу",
            "seo_home_description": f"Официальный сайт сыродельного предприятия {full_brand} в Омске. Натуральные рассольные и мягкие сыры, сливочное масло ГОСТ, тан, айран. Собственное производство, оптовые поставки по РФ.",
            "seo_home_keywords": f"{brand}, сибсыр омск, аревтур, производитель сыра, сыры оптом, рассольный сыр, сулугуни, адыгейский, масло сливочное гост, кисломолочные напитки",

            "seo_catalog_title": f"Каталог продукции {full_brand} — Сыры, масло ГОСТ и кисломолочные напитки в Омске",
            "seo_catalog_description": f"Полный каталог натуральных сыров (сулугуни, брынза, адыгейский, косичка, чечил), сливочного масла и кисломолочной продукции {brand} в Омске. Выгодные цены производителя.",
            "seo_catalog_keywords": f"каталог сыров, сыры омск каталог, купить сыр оптом, сулугуни омск, адыгейский сыр, масло сливочное сибсыр, сибсыр каталог",

            "seo_categories_title": f"Категории продукции — Сыры, масло, напитки | {full_brand} Омск",
            "seo_categories_description": f"Категории натуральной молочной продукции завода {brand}: рассольные сыры, мягкие сыры, сливочное масло ГОСТ 72.5% и 82.5%, кисломолочные напитки тан и айран.",
            "seo_categories_keywords": f"категории сыров, рассольные сыры, мягкие сыры, сыр косичка, сливочное масло омск, кисломолочная продукция сибсыр",

            "seo_about_title": f"О компании {full_brand} — История сыроварни, производство и стандарты качества в Омске",
            "seo_about_description": f"История сыродельного производства {full_brand} (ИП Нахшкарян А.Л.) в Омске: более 25 лет опыта, отборное фермерское молоко, контроль качества ХАССП, отсутствие пальмового масла.",
            "seo_about_keywords": f"о компании сибсыр, сыроварня омск, сыродельный завод омск, нахшкарян сибсыр, производство сыра омск, гост сыры",

            "seo_delivery_title": f"Доставка и оплата продукции {full_brand} — Условия для оптовых и розничных клиентов",
            "seo_delivery_description": f"Условия доставки сыров и молочной продукции {brand}: авторефрижераторы с контролем температуры +2...+4°C, самовывоз со склада завода в Омске, доставка по всей России, безналичный расчет с НДС.",
            "seo_delivery_keywords": f"доставка сыра омск, оптовые поставки сыра, рефрижератор сыр, самовывоз сибсыр омск, оплата сыров",

            "seo_contacts_title": f"Контакты сыродельного завода {full_brand} в Омске — Адрес, отдел продаж, реквизиты",
            "seo_contacts_description": f"Контакты сыродельного завода {full_brand}: г. Омск, ул. Зеленая, 16. Телефоны отдела продаж, email, режим работы, схема проезда и официальные банковские реквизиты ИП Нахшкарян А.Л.",
            "seo_contacts_keywords": f"контакты сибсыр, адрес завода сибсыр омск, телефон отдела продаж сыра, зеленая 16 омск сибсыр, реквизиты сибсыр",

            "seo_reviews_title": f"Отзывы о продукции {full_brand} — Оценки покупателей и розничных сетей",
            "seo_reviews_description": f"Отзывы розничных покупателей, магазинов и шеф-поваров о сырах, сливочном масле и напитках {brand}. Реальные оценки качества и вкуса продукции омского сыродельного завода.",
            "seo_reviews_keywords": f"отзывы сибсыр, отзывы о сырах омск, сыр сибсыр отзывы, качество продукции сибсыр",

            "seo_articles_title": f"Статьи и база знаний о сыре — Советы сыроделов | {full_brand}",
            "seo_articles_description": f"Полезные статьи, рецепты и гид по сырам от мастеров сыроделия завода {brand}: как выбрать натуральный сыр, условия хранения, традиции приготовления и гастрономические сочетания.",
            "seo_articles_keywords": f"статьи о сыре, блог сыродела, как хранить сыр, рецепты с сыром, польза сыра, производство сыра сибсыр",
        }

        updated = False
        for field_name, def_val in defaults.items():
            current_val = getattr(self, field_name, "")
            if not current_val or overwrite:
                setattr(self, field_name, def_val)
                updated = True

        if updated and self.pk:
            self.save()

    @property
    def catalog_banner_image_url(self):
        """Безопасный URL фонового баннера каталога."""
        if self.catalog_banner_image:
            try:
                return self.catalog_banner_image.url
            except (ValueError, AttributeError):
                return ""
        return ""

    def get_page_seo(self, page_name):
        """
        Возвращает словарь с оптимизированными тегами title, description, keywords
        для указанной страницы с умными автоматическими фолбэками.
        """
        brand = self.brand_short_name or "Сибсыр"
        full_brand = self.brand_name or "ТМ «Сибсыр»"

        title_field = f"seo_{page_name}_title"
        desc_field = f"seo_{page_name}_description"
        kw_field = f"seo_{page_name}_keywords"

        title = getattr(self, title_field, "").strip()
        description = getattr(self, desc_field, "").strip()
        keywords = getattr(self, kw_field, "").strip()

        if not title:
            title = f"{self.hero_title or full_brand} — {brand}"
        if not description:
            description = self.seo_default_description
        if not keywords:
            keywords = self.seo_default_keywords

        return {
            "title": title,
            "description": description,
            "keywords": keywords,
        }

    def get_robots_txt(self):
        """
        Возвращает актуальный robots.txt: либо пользовательский из админки,
        либо автоматически сформированный по строгим правилам поисковой оптимизации.
        """
        if not self.is_indexing_enabled:
            return "User-agent: *\nDisallow: /\n"

        if self.robots_txt_content and self.robots_txt_content.strip():
            content = self.robots_txt_content.strip()
            # Добавим Host и Sitemap если отсутствуют
            base_url = (self.site_base_url or "https://sibsir.ru").rstrip('/')
            clean_host = base_url.replace("https://", "").replace("http://", "")
            if "Sitemap:" not in content:
                content += f"\n\nSitemap: {base_url}/sitemap.xml"
            if "Host:" not in content:
                content += f"\nHost: {clean_host}"
            return content + "\n"

        base_url = (self.site_base_url or "https://sibsir.ru").rstrip('/')
        clean_host = base_url.replace("https://", "").replace("http://", "")

        return (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin/\n"
            "Disallow: /accounts/\n"
            "Disallow: /api/\n"
            "Disallow: /tinymce/\n"
            "Disallow: /admin-tinymce-upload/\n"
            "Disallow: /captcha/\n"
            "Disallow: /order/create/\n"
            "Disallow: /callback/create/\n"
            "Disallow: /reviews/create/\n"
            "Disallow: /search/?*\n"
            "Allow: /catalog/\n"
            "Allow: /categories/\n"
            "Allow: /about/\n"
            "Allow: /delivery/\n"
            "Allow: /reviews/\n"
            "Allow: /contacts/\n"
            "Allow: /articles/\n"
            "\n"
            "User-agent: Yandex\n"
            "Allow: /\n"
            "Disallow: /admin/\n"
            "Disallow: /accounts/\n"
            "Disallow: /api/\n"
            "Disallow: /tinymce/\n"
            "Disallow: /admin-tinymce-upload/\n"
            "Disallow: /captcha/\n"
            "Disallow: /order/create/\n"
            "Disallow: /callback/create/\n"
            "Disallow: /reviews/create/\n"
            "Clean-param: utm_source&utm_medium&utm_campaign&utm_term&utm_content&yclid&gclid&fbclid /catalog/\n"
            "\n"
            f"Host: {clean_host}\n"
            f"Sitemap: {base_url}/sitemap.xml\n"
        )


    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return f"{self.brand_short_name} — Настройки"

    @property
    def hero_image_url(self):
        if self.hero_image:
            return self.hero_image.url
        return static("images/hero_cheese.jpg")

    @property
    def about_image_url(self):
        if self.about_image:
            return self.about_image.url
        return None

    @property
    def logo_url(self):
        if self.logo:
            return self.logo.url
        return None

    @property
    def favicon_url(self):
        if self.favicon:
            return self.favicon.url
        return static("images/favicon.svg")

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class ProductionFeature(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок преимущества")
    subtitle = models.CharField(max_length=255, blank=True, verbose_name="Описание / Подзаголовок")
    badge = models.CharField(max_length=80, blank=True, verbose_name="Метка / Бейдж (например: 100% ГОСТ, ХИТ)")
    icon = models.CharField(
        max_length=60, 
        default="bi-check2-circle", 
        verbose_name="CSS-класс иконки Bootstrap", 
        help_text="Например: bi-award, bi-droplet-half, bi-shield-check, bi-clock-history, bi-truck, bi-gear, bi-shop"
    )
    image = models.ImageField(
        upload_to="features/", 
        blank=True, 
        null=True, 
        verbose_name="Изображение / Иллюстрация (опционально)"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Отображать на сайте")

    class Meta:
        verbose_name = "Преимущество / Особенность"
        verbose_name_plural = "Преимущества и особенности"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class CompanyTimeline(models.Model):
    year = models.CharField(max_length=50, verbose_name="Год / Период", help_text="Например: 1999 год, 2016 год, Сегодня")
    title = models.CharField(max_length=150, verbose_name="Заголовок события")
    description = models.TextField(verbose_name="Описание этапа")
    color_class = models.CharField(
        max_length=50,
        choices=[
            ("border-warning", "Желтый / Оранжевый (Сибсыр)"),
            ("border-primary", "Синий (Инновации)"),
            ("border-success", "Зеленый (Качество)"),
            ("border-danger", "Красный (Масштаб)"),
            ("border-dark", "Темно-серый"),
        ],
        default="border-warning",
        verbose_name="Цвет акцентной полосы"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Отображать в истории")

    class Meta:
        verbose_name = "Этап истории (О компании)"
        verbose_name_plural = "История развития (О компании)"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.year}: {self.title}"


class QualityCertificate(models.Model):
    title = models.CharField(max_length=150, verbose_name="Стандарт / ГОСТ / ТУ", help_text="Например: ГОСТ Р 53437-2009")
    subtitle = models.CharField(max_length=255, verbose_name="Категории продукции", help_text="Например: Сыры рассольные («Сулугуни», «Брынза», «Чечил»)")
    icon = models.CharField(max_length=60, default="bi-check-circle-fill", verbose_name="Иконка Bootstrap")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Стандарт / Сертификат (О компании)"
        verbose_name_plural = "Стандарты и ГОСТ (О компании)"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} — {self.subtitle}"


class DeliveryMethod(models.Model):
    title = models.CharField(max_length=150, verbose_name="Название способа доставки")
    description = models.TextField(verbose_name="Краткое описание")
    details = models.TextField(
        blank=True,
        verbose_name="Пункты преимуществ (каждый с новой строки)",
        help_text="Каждая строчка будет отображаться отдельным пунктом с галочкой."
    )
    badge = models.CharField(max_length=100, blank=True, verbose_name="Нижний бейдж", help_text="Например: Собственный автопарк, 0 ₽ • Без ограничений")
    icon = models.CharField(max_length=60, default="bi-truck", verbose_name="Иконка Bootstrap")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Способ доставки"
        verbose_name_plural = "Способы доставки"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def details_list(self):
        if not self.details:
            return []
        return [line.strip() for line in self.details.splitlines() if line.strip()]


class PaymentMethod(models.Model):
    title = models.CharField(max_length=150, verbose_name="Название способа оплаты")
    description = models.TextField(verbose_name="Краткое описание")
    details = models.TextField(
        blank=True,
        verbose_name="Условия и особенности (каждый пункт с новой строки)",
        help_text="Каждая строчка будет отображаться отдельным пунктом с галочкой."
    )
    note = models.CharField(max_length=150, blank=True, verbose_name="Нижняя плашка / примечание", help_text="Например: Р/с в ПАО Сбербанк г. Омск")
    icon = models.CharField(max_length=60, default="bi-credit-card", verbose_name="Иконка Bootstrap")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def details_list(self):
        if not self.details:
            return []
        return [line.strip() for line in self.details.splitlines() if line.strip()]


class DeliveryFaq(models.Model):
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Вопрос-ответ (Доставка)"
        verbose_name_plural = "Вопросы и ответы (Доставка)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class ContactDepartment(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название отдела")
    description = models.TextField(blank=True, verbose_name="Описание деятельности")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон отдела")
    email = models.CharField(max_length=100, blank=True, verbose_name="E-mail отдела")
    extra_info = models.CharField(max_length=150, blank=True, verbose_name="Дополнительная инфо / пандус", help_text="Например: Пандус №1 и №2")
    icon = models.CharField(max_length=60, default="bi-building", verbose_name="Иконка Bootstrap")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Отдел предприятия (Контакты)"
        verbose_name_plural = "Отделы предприятия (Контакты)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class CallbackRequest(models.Model):
    REQUEST_TYPES = [
        ("call", "Заказ обратного звонка"),
        ("wholesale", "Запрос оптового прайс-листа"),
        ("question", "Вопрос по продукции"),
    ]

    APPROVAL_STATUS = [
        ("pending", "⏳ Ожидает одобрения"),
        ("approved", "✅ Одобрено (Прайс отправлен)"),
        ("rejected", "❌ Отклонено"),
    ]

    name = models.CharField(max_length=150, verbose_name="Имя / Контактное лицо")
    company_name = models.CharField(max_length=200, blank=True, verbose_name="Организация / Компания")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    email = models.CharField(max_length=100, blank=True, verbose_name="E-mail")
    request_type = models.CharField(
        max_length=30, 
        choices=REQUEST_TYPES, 
        default="call", 
        verbose_name="Тип обращения"
    )
    message = models.TextField(blank=True, verbose_name="Сообщение / Комментарий")
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default="pending",
        verbose_name="Статус одобрения"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_wholesale_requests",
        verbose_name="Администратор, одобривший отправку"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата и время одобрения"
    )
    price_list_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата отправки прайс-листа"
    )
    admin_comment = models.TextField(
        blank=True,
        verbose_name="Заметка администратора"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Заявка / Обратная связь"
        verbose_name_plural = "Заявки и обратная связь"
        ordering = ["-created_at"]

    def __str__(self):
        status = "✓ Обработано" if self.is_processed else "⌛ Новая"
        comp = f" ({self.company_name})" if self.company_name else ""
        return f"{self.get_request_type_display()} от {self.name}{comp} ({self.phone}) — {status}"

    @property
    def is_wholesale(self):
        return self.request_type == "wholesale"


class WholesalePriceRequestManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(request_type="wholesale")


class WholesalePriceRequest(CallbackRequest):
    objects = WholesalePriceRequestManager()

    class Meta:
        proxy = True
        verbose_name = "Заявка на оптовый прайс-лист"
        verbose_name_plural = "Заявки на оптовый прайс-лист (B2B)"


class FaqCategory(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название категории")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="URL-идентификатор (slug)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Категория FAQ"
        verbose_name_plural = "Категории FAQ"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class FaqItem(models.Model):
    category = models.ForeignKey(
        FaqCategory,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Категория"
    )
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Вопрос-ответ (FAQ)"
        verbose_name_plural = "Вопросы и ответы (FAQ)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class SocialLink(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Название соцсети",
        help_text="Например: ВКонтакте, Одноклассники, Telegram, Instagram, WhatsApp"
    )
    url = models.URLField(
        max_length=300,
        verbose_name="Ссылка на профиль / группу",
        help_text="Полная ссылка, включая https://, например: https://vk.com/sibsir"
    )
    icon = models.ImageField(
        upload_to="social_icons/",
        blank=True,
        null=True,
        verbose_name="Иконка (файл изображения)",
        help_text="Рекомендуется PNG или SVG с прозрачным фоном (квадратная, например 64x64 px)"
    )
    bootstrap_icon = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Иконка Bootstrap Icons (запасная)",
        help_text="Например: bi-telegram, bi-whatsapp, bi-youtube, bi-globe (если файл не загружен)"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Чем меньше число, тем левее отображается иконка"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Отображать на сайте"
    )
    open_in_new_tab = models.BooleanField(
        default=True,
        verbose_name="Открывать в новой вкладке (target='_blank')"
    )

    class Meta:
        verbose_name = "Социальная сеть"
        verbose_name_plural = "Социальные сети"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def get_icon_url(self):
        if self.icon:
            try:
                return self.icon.url
            except Exception:
                pass
        slug_map = {
            "vk": "images/social/vk.png",
            "vkontakte": "images/social/vk.png",
            "вконтакте": "images/social/vk.png",
            "вк": "images/social/vk.png",
            "ok": "images/social/ok.png",
            "odnoklassniki": "images/social/ok.png",
            "одноклассники": "images/social/ok.png",
            "ок": "images/social/ok.png",
            "instagram": "images/social/instagram.png",
            "инстаграм": "images/social/instagram.png",
            "инста": "images/social/instagram.png",
            "facebook": "images/social/facebook.png",
            "фейсбук": "images/social/facebook.png",
            "linkedin": "images/social/linkedin.png",
            "линкедин": "images/social/linkedin.png",
        }
        name_key = self.name.lower().strip()
        if name_key in slug_map:
            return static(slug_map[name_key])
        return ""


# ==============================================================================
# ДИНАМИЧЕСКИЕ СТРАНИЦЫ И ПОЛНОЦЕННОЕ SEO-УПРАВЛЕНИЕ
# ==============================================================================

RESERVED_PAGE_SLUGS = {
    'admin', 'catalog', 'categories', 'about', 'delivery', 'reviews',
    'contacts', 'faq', 'company', 'articles', 'article', 'search',
    'order', 'callback', 'captcha', 'shop', 'accounts', 'tinymce',
    'static', 'media', 'robots.txt', 'sitemap.xml', 'api', 'pages',
    'cart', 'checkout', 'login', 'logout', 'register', 'profile',
}


def validate_page_slug(value):
    from django.core.exceptions import ValidationError
    import re
    if not value:
        return
    val = value.strip().lower()
    if val in RESERVED_PAGE_SLUGS:
        raise ValidationError(f"URL-адрес (слаг) '{val}' зарезервирован системой и не может быть использован.")
    if not re.match(r'^[a-z0-9_-]+$', val):
        raise ValidationError("URL-адрес (слаг) может содержать только строчные латинские буквы, цифры, дефис и подчеркивание.")


class Page(models.Model):
    """
    Модель динамических страниц произвольного контентного типа с полноценным
    управлением через панель администратора и профессиональным набором инструментов
    поискового продвижения (SEO, OpenGraph, Schema.org, Sitemap.xml, аудит).
    """
    LAYOUT_CHOICES = [
        ('standard', 'Стандартный контентный (сбалансированная ширина статьи)'),
        ('narrow', 'Узкий документный (для регламентов, оферт, соглашений)'),
        ('fullwidth', 'Широкий промо-лендинг (для акций, спецпредложений и презентаций)'),
    ]

    ROBOTS_CHOICES = [
        ('index, follow', 'Индексировать и переходить по ссылкам (index, follow) — Рекомендуется'),
        ('noindex, follow', 'Не индексировать страницу, но переходить по ссылкам (noindex, follow)'),
        ('index, nofollow', 'Индексировать страницу, не переходить по ссылкам (index, nofollow)'),
        ('noindex, nofollow', 'Полностью закрыть от поисковых систем (noindex, nofollow)'),
    ]

    SITEMAP_PRIORITY_CHOICES = [
        ('1.0', '1.0 — Наивысший приоритет'),
        ('0.9', '0.9 — Очень высокий'),
        ('0.8', '0.8 — Высокий (рекомендуется)'),
        ('0.7', '0.7 — Средне-высокий'),
        ('0.6', '0.6 — Средний'),
        ('0.5', '0.5 — Обычный'),
        ('0.3', '0.3 — Низкий'),
    ]

    SITEMAP_CHANGEFREQ_CHOICES = [
        ('always', 'Всегда (always)'),
        ('hourly', 'Каждый час (hourly)'),
        ('daily', 'Ежедневно (daily)'),
        ('weekly', 'Еженедельно (weekly)'),
        ('monthly', 'Ежемесячно (monthly)'),
        ('yearly', 'Ежегодно (yearly)'),
    ]

    SCHEMA_TYPE_CHOICES = [
        ('WebPage', 'WebPage — Стандартная веб-страница'),
        ('AboutPage', 'AboutPage — Страница о компании / презентация'),
        ('ContactPage', 'ContactPage — Страница контактов / представительств'),
        ('Article', 'Article — Информационный материал / публикация'),
        ('FAQPage', 'FAQPage — Справочник вопросов и ответов'),
        ('ItemPage', 'ItemPage — Презентация продукта или сервиса'),
    ]

    # --- 1. Основная информация о странице ---
    title = models.CharField(
        max_length=255, 
        verbose_name="Заголовок страницы (H1)",
        help_text="Главный заголовок, отображается на странице и используется в сниппетах."
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        validators=[validate_page_slug],
        verbose_name="URL-адрес (Слаг)",
        help_text="Латинские буквы, цифры и дефис. Доступна по адресам: /slug/ и /pages/slug/."
    )
    menu_title = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Название для меню и навигации",
        help_text="Короткое название для шапки/подвала. Если не заполнено, будет использован основной заголовок."
    )
    badge = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Бейдж над заголовком",
        help_text="Например: «Спецпредложение», «HoReCa и Опт», «Документы», «Акции»"
    )
    subtitle = models.TextField(
        blank=True, 
        verbose_name="Краткое описание / Подзаголовок (Lead)",
        help_text="Вводный акцентный абзац, отображается под основным заголовком."
    )
    content = models.TextField(
        blank=True, 
        verbose_name="Основной контент страницы (HTML)",
        help_text="Визуальный редактор TinyMCE: заголовки, таблицы, форматирование, иллюстрации, ссылки."
    )
    featured_image = models.ImageField(
        upload_to="pages/", 
        blank=True, 
        null=True, 
        verbose_name="Главное фото / Обложка баннера",
        help_text="Используется как промо-иллюстрация страницы и сниппет для соцсетей."
    )

    # --- 2. Внешний вид и макет страницы ---
    template_layout = models.CharField(
        max_length=30, 
        choices=LAYOUT_CHOICES, 
        default='standard', 
        verbose_name="Макет страницы"
    )
    show_hero_banner = models.BooleanField(
        default=True, 
        verbose_name="Отображать фирменную промо-шапку (Hero)",
        help_text="Стильный темно-синий блок с заголовком, бейджем и цепочкой навигации."
    )
    show_cta_block = models.BooleanField(
        default=True, 
        verbose_name="Отображать блок призыва к действию (CTA) внизу",
        help_text="Баннер быстрой связи с менеджером, кнопка звонка и переход в каталог сыров."
    )
    show_breadcrumbs = models.BooleanField(
        default=True, 
        verbose_name="Отображать цепочку навигации (хлебные крошки)"
    )

    # --- 3. Навигация и меню сайта ---
    show_in_header = models.BooleanField(
        default=False, 
        verbose_name="Отображать в верхнем меню (шапке сайта)",
        help_text="Добавляет ссылку на данную страницу в навигацию шапки сайта."
    )
    show_in_footer = models.BooleanField(
        default=False, 
        verbose_name="Отображать в нижнем меню (подвале сайта)",
        help_text="Добавляет ссылку на данную страницу в футер сайта."
    )
    order = models.PositiveIntegerField(
        default=10, 
        verbose_name="Порядок сортировки в меню",
        help_text="Чем меньше число, тем выше ссылка в списках и меню."
    )

    # --- 4. Инструменты поискового продвижения (SEO) ---
    focus_keyword = models.CharField(
        max_length=150, 
        blank=True, 
        verbose_name="Фокусное ключевое слово (Focus Keyword)",
        help_text="Главный поисковый запрос страницы (например: «купить сыр оптом омск»). Используется для SEO-аудита и автогенерации."
    )
    meta_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Заголовок (Meta Title)",
        help_text="Рекомендуемая длина 45–65 символов. Если не заполнено, генерируется автоматически."
    )
    meta_description = models.TextField(
        blank=True, 
        verbose_name="SEO Описание (Meta Description)",
        help_text="Сниппет для выдачи Яндекса и Google (140–180 символов). Если пусто, сформируется из подзаголовка или текста."
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="SEO Ключевые слова (Keywords)",
        help_text="Ключевые слова через запятую. Если пусто, формируются автоматически."
    )
    canonical_url = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Канонический URL (Canonical)",
        help_text="Оставьте пустым для автогенерации текущего URL страницы."
    )
    meta_robots_index = models.CharField(
        max_length=50, 
        choices=ROBOTS_CHOICES, 
        default='index, follow', 
        verbose_name="Директива для роботов (Robots)"
    )

    # --- 5. Социальные сети и мессенджеры (Open Graph & Twitter Cards) ---
    og_title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Заголовок для соцсетей (OG Title)",
        help_text="Отображается при отправке ссылки в Telegram, ВКонтакте, WhatsApp. Если пусто, берется Meta Title."
    )
    og_description = models.TextField(
        blank=True, 
        verbose_name="Описание для соцсетей (OG Description)",
        help_text="Краткое описание для карточек в соцсетях. Если пусто, берется Meta Description."
    )
    og_image = models.ImageField(
        upload_to="pages/og/", 
        blank=True, 
        null=True, 
        verbose_name="Изображение для соцсетей (OG Image)",
        help_text="Рекомендуемый размер 1200x630 px. Если не загружено, используется обложка страницы или логотип завода."
    )
    og_type = models.CharField(
        max_length=30, 
        default="website", 
        choices=[('website', 'Веб-сайт (website)'), ('article', 'Статья / публикация (article)')], 
        verbose_name="Тип Open Graph (og:type)"
    )

    # --- 6. Карта сайта (Sitemap XML) ---
    sitemap_include = models.BooleanField(
        default=True, 
        verbose_name="Включать страницу в sitemap.xml",
        help_text="Позволяет поисковым роботам быстро индексировать новые материалы."
    )
    sitemap_priority = models.CharField(
        max_length=5, 
        choices=SITEMAP_PRIORITY_CHOICES, 
        default='0.8', 
        verbose_name="Приоритет в sitemap.xml"
    )
    sitemap_changefreq = models.CharField(
        max_length=20, 
        choices=SITEMAP_CHANGEFREQ_CHOICES, 
        default='weekly', 
        verbose_name="Частота обновления в sitemap.xml"
    )

    # --- 7. Микроразметка Schema.org и коды отслеживания ---
    schema_type = models.CharField(
        max_length=50, 
        choices=SCHEMA_TYPE_CHOICES, 
        default='WebPage', 
        verbose_name="Тип микроразметки Schema.org"
    )
    custom_schema_json = models.TextField(
        blank=True, 
        verbose_name="Пользовательский JSON-LD Schema.org",
        help_text="Дополнительный код структурированных данных. Если не указан, микроразметка формируется автоматически."
    )
    custom_head_code = models.TextField(
        blank=True, 
        verbose_name="HTML/JS код для вставки в <head>",
        help_text="Индивидуальные пиксели ретаргетинга, верификационные мета-теги или стили страницы."
    )
    custom_body_code = models.TextField(
        blank=True, 
        verbose_name="HTML/JS код для вставки перед </body>",
        help_text="Индивидуальные скрипты конверсий, виджеты или калькуляторы."
    )

    # --- 8. Публикация и статистика ---
    is_published = models.BooleanField(
        default=True, 
        verbose_name="Опубликовано",
        help_text="Если флаг снят, страница скрыта от посетителей (видна только авторизованным администраторам)."
    )
    published_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Дата публикации"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Дата последнего обновления"
    )
    views_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="Количество просмотров"
    )

    class Meta:
        verbose_name = "Динамическая страница"
        verbose_name_plural = "Динамические страницы (SEO & Контент)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        try:
            if self.slug in ['consent', 'soglasie']:
                return reverse("main:company_page_detail", kwargs={"slug": self.slug})
            return reverse("main:page_detail", kwargs={"slug": self.slug})
        except Exception:
            if self.slug in ['consent', 'soglasie']:
                return f"/company/{self.slug}/"
            return f"/pages/{self.slug}/"

    def get_direct_url(self):
        if self.slug in ['consent', 'soglasie']:
            return f"/company/{self.slug}/"
        return f"/{self.slug}/"

    def get_company_url(self):
        return f"/company/{self.slug}/"

    def get_display_title(self):
        return self.menu_title.strip() if self.menu_title else self.title

    def get_clean_text(self):
        """Возвращает чистый текст без HTML-тегов для формирования сниппетов."""
        import re
        raw = self.subtitle or self.content or ""
        clean = re.sub(r'<[^>]+>', ' ', raw)
        clean = clean.replace('&nbsp;', ' ').replace('&mdash;', '—').replace('&laquo;', '«').replace('&raquo;', '»').replace('&quot;', '"')
        return " ".join(clean.split())

    def get_meta_title(self):
        if self.meta_title:
            return self.meta_title
        return f"{self.title} — ТМ «Сибсыр»"

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        clean = self.get_clean_text()
        if clean:
            return (clean[:160] + "...") if len(clean) > 160 else clean
        return f"{self.title} — официальная страница производителя сыров и молочной продукции ТМ «Сибсыр» в Омске."

    def get_meta_keywords(self):
        if self.meta_keywords:
            return self.meta_keywords
        kw = [self.title.lower(), "сибсыр", "сыроварня омск", "производство сыра", "купить сыр"]
        if self.focus_keyword:
            kw.insert(0, self.focus_keyword.lower().strip())
        return ", ".join(dict.fromkeys(kw))

    def get_og_title(self):
        return self.og_title or self.get_meta_title()

    def get_og_description(self):
        return self.og_description or self.get_meta_description()

    def get_og_image_url(self):
        if self.og_image:
            return self.og_image.url
        if self.featured_image:
            return self.featured_image.url
        return ""

    def generate_seo(self, overwrite=False):
        """
        Автоматическая интеллектуальная генерация полного комплекса SEO-тегов:
        Meta Title, Meta Description, Meta Keywords, OG Title, OG Description.
        Учитывает фокусную ключевую фразу при наличии.
        """
        clean_text = self.get_clean_text()
        title_clean = self.title.strip()
        kw_focus = self.focus_keyword.strip() if self.focus_keyword else ""

        # 1. Meta Title (Оптимально 50-65 символов)
        if not self.meta_title or overwrite:
            if kw_focus and kw_focus.lower() not in title_clean.lower():
                candidate_title = f"{title_clean} | {kw_focus.capitalize()} — ТМ «Сибсыр»"
            else:
                candidate_title = f"{title_clean} — ТМ «Сибсыр»"
            self.meta_title = candidate_title[:65]

        # 2. Meta Description (Оптимально 140-175 символов)
        if not self.meta_description or overwrite:
            if clean_text:
                words = clean_text.split()
                snippet = " ".join(words[:22])
                if not snippet.endswith(('.', '!', '?')):
                    snippet += "."
                desc = f"{snippet} Подробнее на официальном сайте ТМ «Сибсыр» в Омске."
            else:
                desc = f"{title_clean} — подробная информация от сыродельного завода «Сибсыр». Высокое качество, натуральное сырье, оптовые и розничные поставки."
            self.meta_description = desc[:175]

        # 3. Meta Keywords
        if not self.meta_keywords or overwrite:
            kw_list = []
            if kw_focus:
                kw_list.append(kw_focus.lower())
            kw_list.extend([
                title_clean.lower(),
                "тм сибсыр",
                "сыроварня омск",
                "производство сыра",
                "натуральные сыры",
                "сыр оптом",
            ])
            seen = set()
            uniq_kw = [x for x in kw_list if not (x in seen or seen.add(x))]
            self.meta_keywords = ", ".join(uniq_kw)[:250]

        # 4. Open Graph
        if not self.og_title or overwrite:
            self.og_title = self.meta_title or title_clean
        if not self.og_description or overwrite:
            self.og_description = self.meta_description

    def get_seo_analysis(self):
        """
        Вычисляет рейтинг поисковой оптимизации страницы (0-100%)
        и формирует детальный чек-лист готовности к продвижению.
        """
        checks = []
        score = 0
        total_possible = 100

        # 1. Meta Title (max 20 pts)
        title_len = len(self.meta_title.strip()) if self.meta_title else 0
        if 40 <= title_len <= 70:
            score += 20
            checks.append({"status": "pass", "label": f"Title идеальной длины ({title_len} симв.)"})
        elif 20 <= title_len < 40:
            score += 12
            checks.append({"status": "warn", "label": f"Title слишком короткий ({title_len} симв., рекоменд. 45–65)"})
        elif title_len > 70:
            score += 10
            checks.append({"status": "warn", "label": f"Title превышает длину ({title_len} симв., поиск может обрезать)"})
        else:
            checks.append({"status": "fail", "label": "Title не заполнен (генерируется авто-шаблон)"})

        # 2. Meta Description (max 20 pts)
        desc_len = len(self.meta_description.strip()) if self.meta_description else 0
        if 130 <= desc_len <= 185:
            score += 20
            checks.append({"status": "pass", "label": f"Description идеальной длины ({desc_len} симв.)"})
        elif 70 <= desc_len < 130:
            score += 12
            checks.append({"status": "warn", "label": f"Description короткий ({desc_len} симв., рекоменд. 140–180)"})
        elif desc_len > 185:
            score += 10
            checks.append({"status": "warn", "label": f"Description слишком длинный ({desc_len} симв., будет обрезан)"})
        else:
            checks.append({"status": "fail", "label": "Description не заполнен"})

        # 3. Focus Keyword (max 20 pts)
        kw = self.focus_keyword.strip().lower() if self.focus_keyword else ""
        if kw:
            score += 5
            in_title = kw in (self.meta_title or self.title).lower()
            in_desc = kw in (self.meta_description or "").lower()
            in_content = kw in (self.content or "").lower()

            if in_title:
                score += 5
                checks.append({"status": "pass", "label": f"Ключ «{kw}» найден в Title"})
            else:
                checks.append({"status": "warn", "label": f"Ключ «{kw}» отсутствует в Title"})

            if in_desc:
                score += 5
                checks.append({"status": "pass", "label": f"Ключ «{kw}» найден в Description"})
            else:
                checks.append({"status": "warn", "label": f"Ключ «{kw}» отсутствует в Description"})

            if in_content:
                score += 5
                checks.append({"status": "pass", "label": f"Ключ «{kw}» найден в тексте страницы"})
            else:
                checks.append({"status": "warn", "label": f"Ключ «{kw}» отсутствует в тексте"})
        else:
            checks.append({"status": "warn", "label": "Фокусный ключевой запрос не задан"})

        # 4. Длина контента (max 15 pts)
        clean_len = len(self.get_clean_text())
        if clean_len >= 800:
            score += 15
            checks.append({"status": "pass", "label": f"Объемный контент ({clean_len} симв.)"})
        elif clean_len >= 250:
            score += 10
            checks.append({"status": "pass", "label": f"Базовый объем контента ({clean_len} симв.)"})
        elif clean_len > 0:
            score += 5
            checks.append({"status": "warn", "label": f"Слишком мало текста ({clean_len} симв.)"})
        else:
            checks.append({"status": "fail", "label": "Контент страницы пуст"})

        # 5. Изображение для соцсетей OpenGraph (max 15 pts)
        if self.og_image or self.featured_image:
            score += 15
            checks.append({"status": "pass", "label": "Иллюстрация для соцсетей и поиска задана"})
        else:
            checks.append({"status": "warn", "label": "Изображение страницы не загружено"})

        # 6. Индексация и карта сайта (max 10 pts)
        if self.sitemap_include and "noindex" not in self.meta_robots_index:
            score += 10
            checks.append({"status": "pass", "label": "Страница открыта для индексации и включена в Sitemap"})
        elif "noindex" in self.meta_robots_index:
            checks.append({"status": "warn", "label": "Страница закрыта от поисковиков тегом noindex"})
        else:
            checks.append({"status": "warn", "label": "Страница исключена из sitemap.xml"})

        grade = "success" if score >= 80 else ("warning" if score >= 50 else "danger")
        return {
            "score": min(100, score),
            "grade": grade,
            "checks": checks,
        }



