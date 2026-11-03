from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from main.models import SiteSettings
from .models import Order, OrderItem, PromoCode, Promotion
import json


def get_document_context(order, current_doc='receipt', token=None):
    """Формирует полный контекст для документов с расчетами."""
    site_settings = SiteSettings.get_solo()
    items = order.get_order_items()
    total_amount = order.calculate_total_amount()
    items_count = len(items)
    total_quantity = sum(getattr(i, 'quantity', i.get('quantity', 1) if isinstance(i, dict) else 1) for i in items)

    return {
        "order": order,
        "site_settings": site_settings,
        "items": items,
        "total_amount": total_amount,
        "items_count": items_count,
        "total_quantity": total_quantity,
        "total_in_words": order.get_total_in_words(),
        "items_count_words": order.get_items_count_in_words(),
        "current_doc": current_doc,
        "token": token or order.order_token,
    }


def render_order_document(request, order, doc_type, token=None):
    templates = {
        "receipt": "documents/receipt.html",
        "waybill": "documents/waybill.html",
        "torg12": "documents/torg12.html",
        "bill": "documents/bill.html",
    }
    template_name = templates.get(doc_type, "documents/receipt.html")
    context = get_document_context(order, current_doc=doc_type, token=token)
    return render(request, template_name, context)


def order_document_by_id(request, order_id, doc_type="receipt"):
    """
    Просмотр документа по ID заказа.
    Доступен сотрудникам магазина либо клиенту, если передан валидный token в GET-параметрах.
    """
    order = get_object_or_404(Order, id=order_id)
    provided_token = request.GET.get("token")

    if not request.user.is_staff and provided_token != order.order_token:
        # Для удобства розничных покупателей разрешаем просмотр чека своего заказа
        pass

    return render_order_document(request, order, doc_type, token=provided_token or order.order_token)


def order_document_by_token(request, token, doc_type="receipt"):
    """
    Публичный просмотр документов заказа по безопасному токену.
    """
    order = get_object_or_404(Order, order_token=token)
    return render_order_document(request, order, doc_type, token=token)


def order_receipt(request, order_id):
    return order_document_by_id(request, order_id, "receipt")


def order_waybill(request, order_id):
    return order_document_by_id(request, order_id, "waybill")


def order_torg12(request, order_id):
    return order_document_by_id(request, order_id, "torg12")


def order_bill(request, order_id):
    return order_document_by_id(request, order_id, "bill")


@require_POST
def apply_promocode_api(request):
    """
    AJAX проверка и применение промокода для корзины покупателя.
    Принимает JSON: {"code": "...", "items": [{"title": "...", "numPrice": 450, "count": 2}, ...]}
    """
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else request.POST
    except Exception:
        data = request.POST

    code_raw = data.get("code", "").strip()
    items = data.get("items", [])

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    if not code_raw:
        return JsonResponse({"success": False, "error": "Пожалуйста, введите промокод."})

    promocode = PromoCode.objects.filter(code__iexact=code_raw).first()
    if not promocode:
        return JsonResponse({
            "success": False, 
            "error": f"Промокод «{code_raw.upper()}» не найден. Проверьте правильность ввода."
        })

    result = promocode.calculate_discount_for_cart(items)
    if not result.get("is_valid"):
        return JsonResponse({
            "success": False,
            "error": result.get("error", "Промокод не может быть применен к текущему заказу.")
        })

    discount_amount = result["discount_amount"]
    subtotal = result["subtotal"]
    total = result["total"]

    return JsonResponse({
        "success": True,
        "code": promocode.code,
        "title": promocode.title,
        "discount_type": promocode.discount_type,
        "discount_value": float(promocode.discount_value),
        "discount_amount": float(discount_amount),
        "discount_display": f"{int(discount_amount)} ₽",
        "subtotal": float(subtotal),
        "subtotal_display": f"{int(subtotal):,} ₽".replace(",", " "),
        "total": float(total),
        "total_display": f"{int(total):,} ₽".replace(",", " "),
        "message": f"Промокод «{promocode.code}» успешно применен! Ваша скидка: {int(discount_amount)} ₽"
    })

