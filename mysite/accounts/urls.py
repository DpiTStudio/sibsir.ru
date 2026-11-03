from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("orders/", views.orders_view, name="orders"),
    path("orders/<int:order_id>/", views.order_detail_view, name="order_detail"),
    path("password/change/", views.password_change_view, name="password_change"),
]
