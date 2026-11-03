from django import template
from main.models import SiteSettings
from main.captcha import generate_captcha

register = template.Library()


@register.inclusion_tag('captcha/captcha_field.html', takes_context=True)
def render_captcha(context, form_type="register", form=None, input_class="form-control rounded-pill px-3"):
    """
    Универсальный тег отрисовки капчи:
    - form_type: 'register', 'login', 'callback', 'order'
    - form: опциональный экземпляр Django-формы для вывода ошибок валидации
    - input_class: CSS-классы поля ввода
    """
    request = context.get("request")
    user = getattr(request, "user", None) if request else None

    site_settings = context.get("site_settings")
    if not site_settings:
        try:
            site_settings = SiteSettings.get_solo()
        except Exception:
            return {"is_required": False}

    if not site_settings.is_captcha_required(form_type, user=user):
        return {"is_required": False}

    captcha_data = generate_captcha(captcha_type=site_settings.captcha_type)

    error = None
    if form and hasattr(form, "errors"):
        errors_list = form.errors.get("captcha_answer")
        if errors_list:
            error = errors_list[0]

    return {
        "is_required": True,
        "key": captcha_data["key"],
        "image_url": captcha_data["image_url"],
        "placeholder": captcha_data["placeholder"],
        "captcha_type": site_settings.captcha_type,
        "input_class": input_class,
        "error": error,
        "form_type": form_type,
    }
