from django import forms
from django.db import models
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from .models import UserProfile
from main.models import SiteSettings
from main.captcha import verify_captcha
import re

User = get_user_model()


class UserLoginForm(forms.Form):
    login = forms.CharField(
        label="Логин или E-mail",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg rounded-pill px-4",
            "placeholder": "Введите логин или адрес электронной почты",
            "autofocus": True,
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg rounded-pill px-4",
            "placeholder": "Введите ваш пароль",
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label="Запомнить меня на этом устройстве",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    captcha_key = forms.CharField(widget=forms.HiddenInput, required=False)
    captcha_answer = forms.CharField(
        required=False,
        label="Проверочный код",
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-4",
            "placeholder": "Код с картинки",
            "autocomplete": "off"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        login_val = cleaned_data.get("login", "").strip()
        password = cleaned_data.get("password")

        # Проверка капчи
        site_settings = SiteSettings.get_solo()
        if site_settings.is_captcha_required("login"):
            c_key = cleaned_data.get("captcha_key") or self.data.get("captcha_key", "")
            c_ans = cleaned_data.get("captcha_answer") or self.data.get("captcha_answer", "")
            is_valid, err_msg = verify_captcha(c_key, c_ans)
            if not is_valid:
                self.add_error("captcha_answer", err_msg or "Неверный проверочный код.")

        if login_val and password:
            # Ищем сначала по username, затем по email
            user = authenticate(username=login_val, password=password)
            if not user:
                user_obj = User.objects.filter(email__iexact=login_val).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)

            if not user:
                raise ValidationError("Неверный логин (email) или пароль. Проверьте правильность введенных данных.")
            if not user.is_active:
                raise ValidationError("Данный аккаунт деактивирован. Обратитесь к администрации магазина.")

            cleaned_data["user"] = user
        return cleaned_data


class IndividualRegistrationForm(forms.Form):
    first_name = forms.CharField(
        label="Ваше имя",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Иван"
        })
    )
    last_name = forms.CharField(
        label="Фамилия",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Иванов"
        })
    )
    email = forms.EmailField(
        label="E-mail (будет логином для входа)",
        widget=forms.EmailInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "name@example.ru"
        })
    )
    phone = forms.CharField(
        label="Номер телефона",
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "+7 (999) 000-00-00"
        })
    )
    delivery_address = forms.CharField(
        label="Адрес доставки по умолчанию",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "г. Омск, ул. Ленина, д. 10, кв. 25"
        })
    )
    password = forms.CharField(
        label="Придумайте пароль",
        min_length=6,
        widget=forms.PasswordInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Не менее 6 символов"
        })
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Повторите пароль"
        })
    )
    captcha_key = forms.CharField(widget=forms.HiddenInput, required=False)
    captcha_answer = forms.CharField(
        required=False,
        label="Проверочный код",
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Код с картинки",
            "autocomplete": "off"
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован в системе.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", "Пароли не совпадают.")

        # Проверка капчи при регистрации
        site_settings = SiteSettings.get_solo()
        if site_settings.is_captcha_required("register"):
            c_key = cleaned_data.get("captcha_key") or self.data.get("captcha_key", "")
            c_ans = cleaned_data.get("captcha_answer") or self.data.get("captcha_answer", "")
            is_valid, err_msg = verify_captcha(c_key, c_ans)
            if not is_valid:
                self.add_error("captcha_answer", err_msg or "Неверный проверочный код.")

        return cleaned_data

    def save(self):
        email = self.cleaned_data["email"].strip().lower()
        first_name = self.cleaned_data["first_name"].strip()
        last_name = self.cleaned_data.get("last_name", "").strip()
        phone = self.cleaned_data.get("phone", "").strip()
        delivery_address = self.cleaned_data.get("delivery_address", "").strip()
        password = self.cleaned_data["password"]

        # Генерируем username на основе email
        base_username = email.split("@")[0]
        base_username = re.sub(r"[^a-zA-Z0-9_.-]", "", base_username) or "user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.customer_type = "individual"
        profile.phone = phone
        profile.delivery_address = delivery_address
        profile.save()

        # Привязываем прошлые заказы по email или телефону, если такие были
        from shop.models import Order
        Order.objects.filter(user__isnull=True).filter(
            models.Q(email__iexact=email) | (models.Q(phone=phone) if phone else models.Q(pk=None))
        ).update(user=user)

        return user


class LegalRegistrationForm(forms.Form):
    company_name = forms.CharField(
        label="Наименование организации / ИП",
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "ООО «Сырная Лавка» или ИП Смирнов И.И."
        })
    )
    inn = forms.CharField(
        label="ИНН организации / ИП",
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "10 или 12 цифр"
        })
    )
    kpp = forms.CharField(
        label="КПП (для юр. лиц)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "9 цифр (для ООО)"
        })
    )
    ogrn = forms.CharField(
        label="ОГРН / ОГРНИП",
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "13 или 15 цифр"
        })
    )
    legal_address = forms.CharField(
        label="Юридический адрес",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "г. Омск, ул. Мира, д. 15, офис 401"
        })
    )
    delivery_address = forms.CharField(
        label="Фактический адрес доставки / Склад",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "г. Омск, ул. Заводская, склад №3"
        })
    )

    # Банковские реквизиты
    bank_name = forms.CharField(
        label="Наименование банка",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "ПАО СБЕРБАНК, АО Т-БАНК и т.д."
        })
    )
    bik = forms.CharField(
        label="БИК банка",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "9 цифр"
        })
    )
    account_number = forms.CharField(
        label="Расчетный счет",
        max_length=35,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "20 цифр (40702810...)"
        })
    )
    corr_account = forms.CharField(
        label="Корреспондентский счет",
        max_length=35,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "20 цифр (30101810...)"
        })
    )

    # Контакты
    contact_person = forms.CharField(
        label="Контактное лицо (ФИО представителя)",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Иванов Иван Иванович"
        })
    )
    phone = forms.CharField(
        label="Рабочий телефон",
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "+7 (999) 000-00-00"
        })
    )
    email = forms.EmailField(
        label="Корпоративный E-mail (логин для входа)",
        widget=forms.EmailInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "b2b@company.ru"
        })
    )
    password = forms.CharField(
        label="Придумайте пароль",
        min_length=6,
        widget=forms.PasswordInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Не менее 6 символов"
        })
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Повторите пароль"
        })
    )
    captcha_key = forms.CharField(widget=forms.HiddenInput, required=False)
    captcha_answer = forms.CharField(
        required=False,
        label="Проверочный код",
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-pill px-3",
            "placeholder": "Код с картинки",
            "autocomplete": "off"
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean_inn(self):
        inn = self.cleaned_data.get("inn", "").strip()
        digits = re.sub(r"\D", "", inn)
        if len(digits) not in [10, 12]:
            raise ValidationError("ИНН должен содержать 10 цифр (для юридических лиц) или 12 цифр (для ИП).")
        return digits

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", "Пароли не совпадают.")

        # Проверка капчи при регистрации юрлица / ИП
        site_settings = SiteSettings.get_solo()
        if site_settings.is_captcha_required("register"):
            c_key = cleaned_data.get("captcha_key") or self.data.get("captcha_key", "")
            c_ans = cleaned_data.get("captcha_answer") or self.data.get("captcha_answer", "")
            is_valid, err_msg = verify_captcha(c_key, c_ans)
            if not is_valid:
                self.add_error("captcha_answer", err_msg or "Неверный проверочный код.")

        return cleaned_data

    def save(self):
        email = self.cleaned_data["email"].strip().lower()
        contact_person = self.cleaned_data.get("contact_person", "").strip()
        password = self.cleaned_data["password"]

        # Делим контактное лицо на имя и фамилию
        parts = contact_person.split()
        first_name = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
        last_name = parts[0] if len(parts) > 1 else ""

        base_username = email.split("@")[0]
        base_username = re.sub(r"[^a-zA-Z0-9_.-]", "", base_username) or "legal"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.customer_type = "legal"
        profile.company_name = self.cleaned_data["company_name"].strip()
        profile.inn = self.cleaned_data["inn"].strip()
        profile.kpp = self.cleaned_data.get("kpp", "").strip()
        profile.ogrn = self.cleaned_data.get("ogrn", "").strip()
        profile.legal_address = self.cleaned_data.get("legal_address", "").strip()
        profile.delivery_address = self.cleaned_data.get("delivery_address", "").strip()
        profile.bank_name = self.cleaned_data.get("bank_name", "").strip()
        profile.bik = self.cleaned_data.get("bik", "").strip()
        profile.account_number = self.cleaned_data.get("account_number", "").strip()
        profile.corr_account = self.cleaned_data.get("corr_account", "").strip()
        profile.contact_person = contact_person
        profile.phone = self.cleaned_data["phone"].strip()
        profile.save()

        # Привязываем прошлые заказы по ИНН, email или телефону
        from shop.models import Order
        Order.objects.filter(user__isnull=True).filter(
            models.Q(inn=profile.inn) | models.Q(email__iexact=email) | models.Q(phone=profile.phone)
        ).update(user=user)

        return user


class IndividualProfileEditForm(forms.Form):
    first_name = forms.CharField(
        label="Имя",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    last_name = forms.CharField(
        label="Фамилия",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    phone = forms.CharField(
        label="Номер телефона",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    delivery_address = forms.CharField(
        label="Основной адрес доставки",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        profile = getattr(user, "profile", None)
        initial = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": profile.phone if profile else "",
            "delivery_address": profile.delivery_address if profile else "",
        }
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Этот e-mail уже используется другим аккаунтом.")
        return email

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data.get("last_name", "").strip()
        self.user.email = self.cleaned_data["email"].strip().lower()
        self.user.save()

        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.phone = self.cleaned_data.get("phone", "").strip()
        profile.delivery_address = self.cleaned_data.get("delivery_address", "").strip()
        profile.save()
        return self.user


class LegalProfileEditForm(forms.Form):
    company_name = forms.CharField(
        label="Наименование организации / ИП",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    inn = forms.CharField(
        label="ИНН",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    kpp = forms.CharField(
        label="КПП (для ООО)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    ogrn = forms.CharField(
        label="ОГРН / ОГРНИП",
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    legal_address = forms.CharField(
        label="Юридический адрес",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    delivery_address = forms.CharField(
        label="Фактический адрес / Склад доставки",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )

    # Банковские реквизиты
    bank_name = forms.CharField(
        label="Банк",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    bik = forms.CharField(
        label="БИК",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    account_number = forms.CharField(
        label="Расчетный счет",
        max_length=35,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    corr_account = forms.CharField(
        label="Корреспондентский счет",
        max_length=35,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )

    # Контакты
    contact_person = forms.CharField(
        label="Контактное лицо",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    phone = forms.CharField(
        label="Рабочий телефон",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill px-3"})
    )
    email = forms.EmailField(
        label="Корпоративный E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control rounded-pill px-3"})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        profile = getattr(user, "profile", None)
        initial = {
            "email": user.email,
            "company_name": profile.company_name if profile else "",
            "inn": profile.inn if profile else "",
            "kpp": profile.kpp if profile else "",
            "ogrn": profile.ogrn if profile else "",
            "legal_address": profile.legal_address if profile else "",
            "delivery_address": profile.delivery_address if profile else "",
            "bank_name": profile.bank_name if profile else "",
            "bik": profile.bik if profile else "",
            "account_number": profile.account_number if profile else "",
            "corr_account": profile.corr_account if profile else "",
            "contact_person": profile.contact_person if profile else (f"{user.first_name} {user.last_name}".strip()),
            "phone": profile.phone if profile else "",
        }
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Этот e-mail уже используется другим аккаунтом.")
        return email

    def save(self):
        self.user.email = self.cleaned_data["email"].strip().lower()
        contact_person = self.cleaned_data.get("contact_person", "").strip()
        parts = contact_person.split()
        if len(parts) > 1:
            self.user.last_name = parts[0]
            self.user.first_name = parts[1]
        elif parts:
            self.user.first_name = parts[0]
        self.user.save()

        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.company_name = self.cleaned_data["company_name"].strip()
        profile.inn = self.cleaned_data["inn"].strip()
        profile.kpp = self.cleaned_data.get("kpp", "").strip()
        profile.ogrn = self.cleaned_data.get("ogrn", "").strip()
        profile.legal_address = self.cleaned_data.get("legal_address", "").strip()
        profile.delivery_address = self.cleaned_data.get("delivery_address", "").strip()
        profile.bank_name = self.cleaned_data.get("bank_name", "").strip()
        profile.bik = self.cleaned_data.get("bik", "").strip()
        profile.account_number = self.cleaned_data.get("account_number", "").strip()
        profile.corr_account = self.cleaned_data.get("corr_account", "").strip()
        profile.contact_person = contact_person
        profile.phone = self.cleaned_data["phone"].strip()
        profile.save()
        return self.user
