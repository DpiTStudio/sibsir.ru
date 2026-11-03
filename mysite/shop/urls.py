from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    # Документы по ID
    path("order/<int:order_id>/receipt/", views.order_receipt, name="order_receipt"),
    path("order/<int:order_id>/waybill/", views.order_waybill, name="order_waybill"),
    path("order/<int:order_id>/torg12/", views.order_torg12, name="order_torg12"),
    path("order/<int:order_id>/bill/", views.order_bill, name="order_bill"),

    # Документы по токену (для клиентов после оформления)
    path("doc/<str:token>/<str:doc_type>/", views.order_document_by_token, name="order_token_doc"),

    # API промокодов и скидок
    path("api/promocode/apply/", views.apply_promocode_api, name="apply_promocode_api"),
]
