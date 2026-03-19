class DatabaseRouter:
    # Указываем метку приложения, для которого применяется особая маршрутизация
    route_app_labels = {"development"}

    def db_for_read(self, model, **hints):
        """
        Определяет, из какой базы данных читать данные для модели.
        Если модель принадлежит приложению 'development', читаем из базы 'development_db'.
        Иначе — из базы данных по умолчанию 'default'.
        """
        if model._meta.app_label in self.route_app_labels:
            return "development_db"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Определяет, в какую базу данных записывать данные для модели.
        Если модель принадлежит приложению 'development', запись идет в 'development_db'.
        Иначе — в базу данных по умолчанию 'default'.
        """
        if model._meta.app_label in self.route_app_labels:
            return "development_db"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Определяет, разрешены ли отношения между двумя объектами.
        Возвращает True, если:
        - оба объекта находятся в одной базе данных (одинаковое значение obj._state.db)
        - хотя бы один из объектов относится к приложению 'development' (можно разрешить связь между 'default' и 'development_db')
        """
        if obj1._state.db == obj2._state.db:
            return True
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Определяет, разрешена ли миграция модели в указанную базу данных.
        Если модель из приложения 'development', миграция разрешена только в 'development_db'.
        Для всех остальных приложений миграция выполняется в базу данных 'default'.
        """
        if app_label in self.route_app_labels:
            return db == "development_db"
        return db == "default"
