# bilimClassApp/signals.py

from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import Profile


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

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Создает профиль для нового пользователя или просто сохраняет существующий.
    """
    if created:
        # Если пользователь был только что СОЗДАН, создаем для него профиль
        Profile.objects.create(user=instance)
    # Для существующих пользователей просто сохраняем профиль
    # Это полезно, если в профиле есть поля, которые зависят от User
    instance.profile.save()


