from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Позволяет получать значение из словаря по ключу в шаблоне Django.
    Использование: {{ my_dictionary|get_item:my_key }}
    """
    # Проверяем, что первый аргумент - это словарь
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

