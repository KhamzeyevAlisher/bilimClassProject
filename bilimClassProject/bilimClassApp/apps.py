# bilimClassApp/apps.py

from django.apps import AppConfig

class BilimclassappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bilimClassApp'

    # Добавляем метод ready для выполнения кода при запуске приложения
    def ready(self):
        # Импортируем наш обработчик сигналов здесь, чтобы избежать AppRegistryNotReady
        import bilimClassApp.signals