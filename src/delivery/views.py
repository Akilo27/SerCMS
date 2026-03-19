import requests
from django.contrib import messages
from django.http import HttpResponseRedirect

from .models import DeliveryType
from payment.models import Order


def check_courier(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, key=request.GET.get("order_id"))

        delivery_method = DeliveryType.objects.get(
            type=1, site__domain=request.get_host(), turn_on=True
        )
        url = "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/performer-position"
        headers = {
            "Accept-Language": "ru",
            "Authorization": f"{delivery_method.key_1}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response_data = response.json()

            return print(response_data)
        else:
            messages.success(
                request,
                "Ошибка при отслеживании круьера .Повторите позже или обратитесь в поддержку ",
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
