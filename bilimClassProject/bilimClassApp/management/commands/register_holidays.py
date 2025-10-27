import datetime
import calendar  # <--- 1. Импортируем модуль calendar
from django.core.management.base import BaseCommand
from bilimClassApp.models import Holiday

class Command(BaseCommand):
    """
    Пользовательская команда Django для регистрации всех выходных
    (суббота, воскресенье) и летних каникул для указанного года.
    
    Автоматически определяет високосный год.
    
    Пример использования:
    python manage.py register_holidays 2024
    """
    help = 'Регистрирует все субботы, воскресенья и летние месяцы как выходные дни для заданного года.'

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, help='Год, для которого нужно зарегистрировать выходные и каникулы.')

    def handle(self, *args, **options):
        year = options['year']
        
        # --- 2. Автоматически определяем количество дней в году ---
        if calendar.isleap(year):
            days_in_year = 366
            self.stdout.write(self.style.SUCCESS(f'Обнаружен високосный год ({year}). Будет обработано 366 дней.'))
        else:
            days_in_year = 365
            self.stdout.write(self.style.SUCCESS(f'Год {year} не високосный. Будет обработано 365 дней.'))
        
        self.stdout.write(f'Начинаю регистрацию выходных и летних каникул на {year} год...')

        start_date = datetime.date(year, 1, 1)
        total_created = 0

        # --- 3. Используем правильное количество дней в цикле ---
        for day_num in range(days_in_year):
            current_date = start_date + datetime.timedelta(days=day_num)
            
            holiday_name = None
            
            # 1. Проверяем, является ли месяц летним
            if current_date.month in [6, 7, 8]: # Июнь, Июль, Август
                holiday_name = "Летние каникулы"
            # 2. Если не лето, проверяем, является ли день субботой или воскресеньем
            elif current_date.weekday() in [5, 6]:  # 5 = Суббота, 6 = Воскресенье
                holiday_name = "Выходной день"

            # Если день подходит под одно из условий, создаем запись
            if holiday_name:
                obj, created = Holiday.objects.get_or_create(
                    date=current_date,
                    defaults={'name': holiday_name}
                )
                
                if created:
                    total_created += 1

        if total_created > 0:
            self.stdout.write(self.style.SUCCESS(f'Успешно добавлено {total_created} новых выходных/каникулярных дней.'))
        else:
            self.stdout.write(self.style.WARNING(f'Новых выходных дней для {year} года не добавлено (возможно, они уже были зарегистрированы).'))
            
        self.stdout.write(self.style.SUCCESS(f'Процесс для {year} года завершен.'))