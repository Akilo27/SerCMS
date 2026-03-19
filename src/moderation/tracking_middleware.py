from django.utils.deprecation import MiddlewareMixin


class PageViewTrackingMiddleware(MiddlewareMixin):
    pass
    # def process_view(self, request, view_func, view_args, view_kwargs):
    #     user = request.user if request.user.is_authenticated else None
    #     ip_address = self.get_client_ip(request)
    #     browser = request.META.get('HTTP_USER_AGENT', 'Неизвестно')
    #     path = request.path
    #
    #     # Удаляем предыдущий ViewPage для данного IP и пользователя
    #     ViewPage.objects.filter(ip=ip_address, author=user).delete()
    #
    #     # Создаем новый экземпляр ViewPage
    #     view_page = ViewPage.objects.create(
    #         author=user,
    #         ip=ip_address,
    #         browser=browser,
    #         link=path
    #     )
    #
    #     # Обновляем ViewDayPage.jsoninformation
    #     today = date.today()
    #     view_day_page, created = ViewDayPage.objects.get_or_create(
    #         create__date=today,
    #         defaults={'author': user, 'jsoninformation': json.dumps([])}
    #     )
    #
    #     # Загружаем текущие данные из jsoninformation
    #     try:
    #         views_data = json.loads(view_day_page.jsoninformation)
    #     except json.JSONDecodeError:
    #         views_data = []
    #
    #     # Добавляем новую запись
    #     views_data.append({
    #         'ip': ip_address,
    #         'browser': browser,
    #         'link': path,
    #         'datetime': view_page.create.strftime('%Y-%m-%d %H:%M:%S')
    #     })
    #
    #     # Сохраняем обновленные данные
    #     view_day_page.jsoninformation = json.dumps(views_data, ensure_ascii=False)
    #     view_day_page.save(update_fields=['jsoninformation'])
    #
    # def get_client_ip(self, request):
    #     """Получаем IP-адрес клиента"""
    #     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    #     if x_forwarded_for:
    #         ip = x_forwarded_for.split(',')[0]
    #     else:
    #         ip = request.META.get('REMOTE_ADDR')
    #     return ip
