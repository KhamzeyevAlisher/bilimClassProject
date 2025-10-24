# bilimClassApp/models.py

# --- 1. ОБЪЕДИНЕННЫЕ ИМПОРТЫ ---
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 2. ОСНОВНЫЕ СПРАВОЧНИКИ ---

class School(models.Model):
    """Модель Школы."""
    name = models.CharField(max_length=200, unique=True, verbose_name="Название школы")
    address = models.CharField(max_length=255, blank=True, verbose_name="Адрес")

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школы"

    def __str__(self):
        return self.name

class Subject(models.Model):
    """Модель Учебного предмета."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название предмета")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return self.name

# --- 3. МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ И СТРУКТУРЫ ШКОЛЫ ---

class Teacher(models.Model):
    """Модель Учителя, расширяющая стандартного User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Школа")
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name="Предметы, которые преподает")
    
    class Meta:
        verbose_name = "Учитель"
        verbose_name_plural = "Учителя"

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Profile(models.Model):
    """Профиль пользователя для дополнительной информации."""
    # user = models.OneToOneField(User, on_delete=models.CASCADE)

    ROLE_CHOICES = (
        ('teacher', 'Учитель'),
        ('student', 'Ученик'),
        ('headteacher', 'Завуч'),
        ('admin', 'Администратор'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    location = models.CharField(max_length=30, blank=True, verbose_name="Местоположение")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")

    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        verbose_name="Роль",
        # Добавляем blank=True и null=True, чтобы существующие профили не вызвали ошибку
        blank=True, 
        null=True
    )

    def __str__(self):
        return self.user.username
        
class SchoolClass(models.Model):
    """Модель Школьного класса."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name="Школа")
    name = models.CharField(max_length=10, verbose_name="Название класса (например, 9А)")
    students = models.ManyToManyField(User, related_name='school_classes', blank=True, verbose_name="Ученики")
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Классный руководитель")

    # === НАЧАЛО НОВОГО КОДА ===
    # @property
    # def student_count(self):
    #     """Возвращает количество учеников в классе."""
    #     return self.students.count()
    # === КОНЕЦ НОВОГО КОДА ===

    class Meta:
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        unique_together = ('school', 'name')
        ordering = ['school', 'name']
        
    def __str__(self):
        return f"{self.school.name} - {self.name}"

# --- 4. МОДЕЛИ ДЕЯТЕЛЬНОСТИ И РАБОТ ---

class Schedule(models.Model):
    """Модель Расписания."""
    DAY_CHOICES = ((1, "Понедельник"), (2, "Вторник"), (3, "Среда"), (4, "Четверг"), (5, "Пятница"), (6, "Суббота"), (7, "Воскресенье"))
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Учитель")
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала урока")
    end_time = models.TimeField(verbose_name="Время окончания урока")
    classroom = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")

    class Meta:
        verbose_name = "Запись в расписании"
        verbose_name_plural = "Расписание"
        unique_together = ('school_class', 'day_of_week', 'start_time')
        ordering = ['school_class', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.school_class} - {self.subject}"

class Homework(models.Model):
    """Модель для самого Домашнего Задания, создаваемого учителем."""
    title = models.CharField(max_length=255, verbose_name="Заголовок/Тема задания")
    description = models.TextField(verbose_name="Описание задания")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='homeworks', verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homeworks_by_subject', verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_homeworks', verbose_name="Учитель (автор)")
    attached_file = models.FileField(upload_to='homework_attachments/', blank=True, null=True, verbose_name="Прикрепленный файл")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    due_date = models.DateTimeField(verbose_name="Срок сдачи (дедлайн)")
    
    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        ordering = ['-due_date']

    def __str__(self):
        return f'ДЗ по "{self.subject.name}" для {self.school_class.name} (до {self.due_date.strftime("%d.%m.%Y")})'

class HomeworkSubmission(models.Model):
    """Модель для Ответа/Сдачи домашнего задания конкретным учеником."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions', verbose_name="Домашнее задание")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homework_submissions', verbose_name="Ученик", limit_choices_to={'groups__name': 'Ученик'})
    submission_text = models.TextField(blank=True, verbose_name="Текстовый ответ ученика")
    submission_file = models.FileField(upload_to='submission_files/', blank=True, null=True, verbose_name="Прикрепленный файл ответа")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата сдачи")
    grade = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True, verbose_name="Оценка за работу")
    teacher_comment = models.TextField(blank=True, verbose_name="Комментарий учителя")
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата проверки")

    class Meta:
        verbose_name = "Ответ на ДЗ"
        verbose_name_plural = "Ответы на ДЗ"
        unique_together = ('homework', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Ответ от {self.student.username} на "{self.homework.title}"'

# --- 5. МОДЕЛИ УЧЕТА И ОЦЕНИВАНИЯ ---

class Assessment(models.Model):
    """Централизованная модель для всех видов оценок."""
    class AssessmentType(models.TextChoices):
        LESSON = 'lesson', 'За урок'
        HOMEWORK = 'homework', 'За домашнее задание'
        QUARTER = 'quarter', 'За четверть'
        EXAM = 'exam', 'За экзамен'

    submission = models.OneToOneField(HomeworkSubmission, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Сданная работа")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Ученик", related_name='assessments', limit_choices_to={'groups__name': 'Ученик'})
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Учитель")
    date = models.DateField(verbose_name="Дата оценки")
    assessment_type = models.CharField(max_length=10, choices=AssessmentType.choices, default=AssessmentType.LESSON, verbose_name="Тип работы")
    grade = models.PositiveIntegerField(verbose_name="Оценка", validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    was_absent = models.BooleanField(default=False, verbose_name="Пропустил урок (Н/Б)")
    comment = models.TextField(blank=True, verbose_name="Комментарий учителя")
    
    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ['-date', 'student']

    def __str__(self):
        if self.was_absent:
            return f"{self.student.username} - {self.subject.name}: Н/Б ({self.date})"
        return f"{self.student.username} - {self.subject.name}: {self.grade} ({self.date})"

class Attendance(models.Model):
    """Модель для хранения статуса посещаемости ученика на уроке."""
    class Status(models.TextChoices):
        PRESENT = 'P', 'Присутствовал'
        ABSENT = 'A', 'Отсутствовал'
        LATE = 'L', 'Опоздал'

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PRESENT)
    
    class Meta:
        unique_together = ('student', 'subject', 'school_class', 'date')
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"

    def __str__(self):
        return f"{self.student.username} - {self.subject.name} ({self.date}): {self.get_status_display()}"

# --- 6. ВСПОМОГАТЕЛЬНЫЕ МОДЕЛИ ---

class Holiday(models.Model):
    """Модель для хранения праздничных и других нерабочих дней."""
    date = models.DateField(unique=True, verbose_name="Дата")
    name = models.CharField(max_length=200, verbose_name="Название праздника / причина")

    class Meta:
        verbose_name = "Праздничный/Нерабочий день"
        verbose_name_plural = "Праздничные/Нерабочие дни"
        ordering = ['date']

    def __str__(self):
        return f"{self.date.strftime('%d-%m-%Y')} - {self.name}"

# --- 7. СИГНАЛЫ DJANGO ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Устанавливаем роль по умолчанию для всех новых пользователей.
        # Вы можете выбрать любую, например, 'student'.
        Profile.objects.create(user=instance, role='student')

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """Сохраняет профиль пользователя при сохранении пользователя."""
#     instance.profile.save()