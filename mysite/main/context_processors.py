from django.templatetags.static import static
from .models import SiteSettings, SocialLink


def site_settings(request):
    """
    Глобальный процессор контекста для шаблонов сайта:
    передает объект SiteSettings, канонический URL, метатеги по умолчанию,
    домен, данные для соцсетей (OpenGraph) и список активных соцсетей.
    """
    try:
        settings_obj = SiteSettings.get_solo()
    except Exception:
        settings_obj = None

    site_base_url = "https://sibsir.ru"
    if settings_obj and settings_obj.site_base_url:
        site_base_url = settings_obj.site_base_url.rstrip('/')
    elif hasattr(request, "scheme") and hasattr(request, "get_host"):
        site_base_url = f"{request.scheme}://{request.get_host()}".rstrip('/')

    canonical_url = f"{site_base_url}{request.path}" if hasattr(request, "path") else site_base_url

    # Изображение для соцсетей по умолчанию
    og_image_url = f"{site_base_url}{static('images/hero_cheese.jpg')}"
    if settings_obj and settings_obj.seo_og_image:
        og_image_url = f"{site_base_url}{settings_obj.seo_og_image.url}"
    elif settings_obj and settings_obj.hero_image:
        og_image_url = f"{site_base_url}{settings_obj.hero_image.url}"

    brand_name = settings_obj.brand_name if settings_obj else "ТМ «Сибсыр»"
    brand_short = settings_obj.brand_short_name if settings_obj else "Сибсыр"

    try:
        from shop.models import Category
        nav_categories = list(Category.objects.filter(is_active=True).order_by('order', 'id'))
    except Exception:
        nav_categories = []

    try:
        social_links = list(SocialLink.objects.filter(is_active=True).order_by('order', 'id'))
    except Exception:
        social_links = []

    try:
        from .models import Page, FooterStatBanner
        header_pages = list(Page.objects.filter(is_published=True, show_in_header=True).order_by('order', 'id'))
        footer_pages = list(Page.objects.filter(is_published=True, show_in_footer=True).order_by('order', 'id'))
        footer_stat_banners = list(FooterStatBanner.objects.filter(is_active=True).order_by('order', 'id'))
    except Exception:
        header_pages = []
        footer_pages = []
        footer_stat_banners = []

    return {
        "site_settings": settings_obj,
        "site_base_url": site_base_url,
        "canonical_url": canonical_url,
        "site_og_image_url": og_image_url,
        "brand_name": brand_name,
        "brand_short_name": brand_short,
        "nav_categories": nav_categories,
        "social_links": social_links,
        "header_pages": header_pages,
        "footer_pages": footer_pages,
        "footer_stat_banners": footer_stat_banners,
    }
