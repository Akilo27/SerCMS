class DatabaseRouter:
    route_app_labels = {"ecommerce", "parsing_info"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return model._meta.app_label + "_db"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return model._meta.app_label + "_db"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        # Разрешаем отношения в рамках одной базы данных
        if obj1._state.db == obj2._state.db:
            return True
        # Разрешаем отношения между маршрутизируемыми приложениями и default
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == app_label + "_db"
        return db == "default"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == "useraccount":
            return "default"
        if model._meta.app_label in self.route_app_labels:
            return model._meta.app_label + "_db"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "useraccount":
            return "default"
        if model._meta.app_label in self.route_app_labels:
            return model._meta.app_label + "_db"
        return "default"
