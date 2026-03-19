from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from shop.models import Manufacturers


class ManufacturerTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Извлечение токена из заголовка
        token = request.headers.get('Authorization')
        if not token:
            return None

        token = token.split(' ')[1]  # Извлекаем токен
        try:
            manufacturer = Manufacturers.objects.get(token=token)
        except Manufacturers.DoesNotExist:
            raise AuthenticationFailed('Неверный токен или магазин не найден.')

        return (manufacturer, None)



