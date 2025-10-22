# bilimClassApp/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

ROLES = ['Ученик', 'Учитель', 'Завуч', 'Администратор']

@receiver(post_migrate)
def create_roles(sender, **kwargs):
    # Убеждаемся, что мы работаем с миграциями нашего приложения
    if sender.name == 'bilimClassApp':
        for role_name in ROLES:
            # get_or_create пытается найти группу, и если ее нет - создает
            # Возвращает кортеж (объект_группы, был_ли_он_создан_True/False)
            Group.objects.get_or_create(name=role_name)
        print("Роли успешно созданы/проверены.")