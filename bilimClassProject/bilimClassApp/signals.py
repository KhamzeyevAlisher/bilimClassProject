# bilimClassApp/signals.py

from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import Profile
from django.dispatch import Signal



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
def create_user_profile(sender, instance, created, **kwargs):
    """
    Создает профиль, если пользователь новый.
    Роль берется из временного атрибута, прикрепленного в форме.
    """
    if created:
        # 1. Устанавливаем роль по умолчанию на всякий случай 
        # (например, если пользователь создается через админку).
        role_to_set = 'student' 
        
        # 2. ПРОВЕРЯЕМ, "прикрепила" ли форма какую-то роль к пользователю.
        if hasattr(instance, '_role_to_set'):
            # 3. Если да, ИСПОЛЬЗУЕМ ЭТУ РОЛЬ.
            role_to_set = instance._role_to_set

        # 4. Создаем профиль с правильной ролью.
        Profile.objects.create(user=instance, role=role_to_set)


# user_registered_with_role = Signal()

# @receiver(user_registered_with_role)
# def create_profile_with_role(sender, user, role, **kwargs):
#     """
#     Создает профиль для нового пользователя с указанной ролью.
#     """
#     # Проверяем на всякий случай, чтобы не создать дубликат профиля
#     if not hasattr(user, 'profile'):
#         Profile.objects.create(user=user, role=role)