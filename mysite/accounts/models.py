from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ("individual", "Физическое лицо (Обычный покупатель)"),
        ("legal", "Юридическое лицо / ИП"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default="individual",
        verbose_name="Тип клиента",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Номер телефона",
    )
    delivery_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Основной адрес доставки",
    )

    # Реквизиты для Юр. Лиц и ИП
    company_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Наименование организации / ИП",
        help_text="Например: ООО «Сырная Лавка» или ИП Смирнов И.И.",
    )
    inn = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="ИНН",
    )
    kpp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="КПП (для юр. лиц)",
    )
    ogrn = models.CharField(
        max_length=25,
        blank=True,
        verbose_name="ОГРН / ОГРНИП",
    )
    legal_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Юридический адрес",
    )
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Наименование банка",
    )
    bik = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="БИК банка",
    )
    account_number = models.CharField(
        max_length=35,
        blank=True,
        verbose_name="Расчетный счет",
    )
    corr_account = models.CharField(
        max_length=35,
        blank=True,
        verbose_name="Корреспондентский счет",
    )
    contact_person = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Контактное лицо",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        type_str = "Юр. лицо" if self.is_legal else "Физ. лицо"
        name = self.display_name
        return f"{name} ({type_str}) — {self.user.username}"

    @property
    def is_legal(self):
        return self.customer_type == "legal"

    @property
    def display_name(self):
        if self.is_legal and self.company_name:
            return self.company_name
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        if full:
            return full
        if self.contact_person:
            return self.contact_person
        return self.user.username

    def get_orders(self):
        """Возвращает QuerySet заказов пользователя."""
        from shop.models import Order
        return Order.objects.filter(user=self.user).order_by("-created_at")

    def get_orders_count(self):
        return self.get_orders().count()

    def get_total_spent(self):
        from decimal import Decimal
        orders = self.get_orders().exclude(status="cancelled")
        return sum(o.total_price for o in orders) if orders.exists() else Decimal("0.00")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль при создании пользователя."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Для обратной совместимости, если профиль еще не создан
        UserProfile.objects.get_or_create(user=instance)
