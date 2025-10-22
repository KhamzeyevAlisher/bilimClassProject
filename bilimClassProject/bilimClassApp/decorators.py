from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """Декоратор, который проверяет, входит ли пользователь в одну из указанных групп."""
    def check_perms(user):
        if user.groups.filter(name__in=group_names).exists() or user.is_superuser:
            return True
        # Если проверка не пройдена, вызываем исключение, которое приведет к ошибке 403 Forbidden
        raise PermissionDenied
    return user_passes_test(check_perms)