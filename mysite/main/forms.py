from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from main.models import SiteSettings
from main.captcha import verify_captcha


class AdminCaptchaAuthenticationForm(AdminAuthenticationForm):
    """
    Форма входа в панель администратора Django с интеграцией антиспам-капчи.
    Защищает от подбора паролей и автоматизированных брутфорс-атак.
    """
    captcha_answer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "class": "sib-input captcha-answer-input",
            "placeholder": "Код с картинки",
        })
    )
    captcha_key = forms.CharField(
        required=False, 
        widget=forms.HiddenInput(attrs={"class": "captcha-key-input"})
    )

    def clean(self):
        # 1. Проверяем капчу перед попыткой авторизации
        site_settings = SiteSettings.get_solo()
        if site_settings.is_captcha_required("admin_login"):
            c_key = self.cleaned_data.get("captcha_key") or self.data.get("captcha_key", "")
            c_ans = self.cleaned_data.get("captcha_answer") or self.data.get("captcha_answer", "")
            is_valid, err_msg = verify_captcha(c_key, c_ans)
            if not is_valid:
                self.add_error("captcha_answer", err_msg or "Неверный проверочный код или ответ на пример.")
                return self.cleaned_data

        # 2. Проверяем учетные данные администратора
        return super().clean()
