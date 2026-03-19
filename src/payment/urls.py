from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("purchase/", views.CheckoutView.as_view(), name="purchase"),
    path(
        "order/confirmation/<slug:key>/",
        views.CustomCheckoutUrl.as_view(),
        name="customcheckout",
    ),
    path(
        "payment_notification/", views.payment_notification, name="payment_notification"
    ),
    path(
        "payment_notification_alfa_bank/",
        views.payment_notification_alfa_bank,
        name="payment_notification",
    ),
    path(
        "notification_gateway/", views.notification_gateway, name="notification_gateway"
    ),
    path('calculate-shipping/', views.calculate_the_shipping_cost, name='calculate_the_shipping_cost'),

    path(
        "payments/callback/",
        views.universal_payment_callback,
        name="universal_payment_callback",
    ),
]
