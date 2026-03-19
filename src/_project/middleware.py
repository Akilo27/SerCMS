from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthFromCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем токен из cookies
        token = request.COOKIES.get("Authorization")
        if token:
            try:
                # Проверка и аутентификация пользователя через JWT токен
                token = token.split(" ")[
                    1
                ]  # Извлекаем токен из формата "Bearer <token>"
                user, _ = JWTAuthentication().authenticate(request)
                request.user = user
            except Exception as e:
                print(f"Token authentication failed: {e}")
        return self.get_response(request)
