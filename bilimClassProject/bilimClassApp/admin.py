# bilimClassApp/admin.py

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group

from .models import School, Subject, SchoolClass, Teacher, Schedule, Assessment, Holiday, Attendance, Homework, HomeworkSubmission, Profile

# -----------------------------------------------------------------------------
# ЧАСТЬ 1: Кастомизация админки для стандартной модели User
# (Этот код у вас уже должен быть, оставляем его как есть)
# -----------------------------------------------------------------------------
class UserChangeForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        widget=forms.RadioSelect,
        required=False,
        empty_label=None,
        label="Роль"
    )
    class Meta:
        model = User
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['role'].initial = self.instance.groups.first()
    def save(self, commit=True):
        self.instance.groups.clear()
        selected_role = self.cleaned_data.get('role')
        if selected_role:
            self.instance.groups.add(selected_role)
        return super().save(commit)

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Роль', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # ... (здесь могут быть ваши экшены, если вы их добавляли)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Настройки админ-панели для модели Оценок."""
    
    # Поля для отображения в списке оценок
    list_display = ('student', 'subject', 'grade', 'date', 'assessment_type', 'school_class', 'teacher')
    
    # Фильтры, которые появятся справа
    list_filter = ('date', 'school_class', 'subject', 'teacher', 'assessment_type')
    
    # Поля, по которым можно будет искать
    search_fields = (
        'student__username', 
        'student__first_name', 
        'student__last_name',
        'subject__name',
        'grade'
    )
    
    # Превращаем выпадающие списки в удобные поля с поиском
    autocomplete_fields = ('student', 'school_class', 'subject', 'teacher')
    
    # Позволяет редактировать дату в списке (если нужно быстро исправить)
    # list_editable = ('grade',) # Можно раскомментировать для быстрого редактирования оценки прямо в списке

    # Это полезная функция: когда вы ставите оценку,
    # поле teacher автоматически заполнится текущим пользователем.
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'teacher':
            try:
                # Пытаемся найти профиль учителя для залогиненного админа
                teacher = request.user.teacher
                kwargs['initial'] = teacher.pk
            except Exception:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Перерегистрация модели User с нашими настройками
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# -----------------------------------------------------------------------------
# ЧАСТЬ 2: Регистрация НАШИХ моделей с улучшенными настройками
# (Это заменяет старые admin.site.register(...))
# -----------------------------------------------------------------------------

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address']
    list_display = ('name', 'address')

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):

    search_fields = ['name', 'school__name']
    
    autocomplete_fields = ['school']
    filter_horizontal = ['students']
    list_display = ('name', 'school')
    list_filter = ('school',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['name']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'school')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ['user', 'school', 'subjects']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    # --- ДОБАВЛЯЕМ ЭТУ СТРОКУ, ЧТОБЫ ПО УРОКАМ МОЖНО БЫЛО ИСКАТЬ ---
    search_fields = (
        'subject__name',              # Искать по названию предмета (Математика)
        'school_class__name',         # Искать по названию класса (9А)
        'school_class__school__name', # Искать по названию школы (100 школа)
        'teacher__user__first_name',  # Искать по имени учителя
        'teacher__user__last_name',   # Искать по фамилии учителя
    )

    list_display = ('__str__', 'teacher')
    list_filter = ('school_class__school', 'school_class', 'teacher', 'day_of_week')
    autocomplete_fields = ['school_class', 'subject', 'teacher']

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Админка для праздничных дней."""
    list_display = ('date', 'name')
    search_fields = ('name',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    ИСПРАВЛЕННАЯ Настройка для управления Посещаемостью.
    Все ссылки на несуществующее поле 'lesson' убраны.
    """
    # Поля, которые реально существуют в модели
    list_display = ('date', 'student', 'subject', 'school_class', 'status')
    
    # Фильтры, которые ссылаются на существующие поля
    list_filter = ('date', 'status', 'school_class__school', 'school_class', 'subject')
    
    # Поля для поиска
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject__name')
    
    # Удобный поиск для полей ForeignKey
    autocomplete_fields = ['student', 'subject', 'school_class']
    
    # Сортировка по умолчанию
    ordering = ('-date',)

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'school_class', 'teacher', 'due_date')
    list_filter = ('school_class__school', 'subject', 'school_class')
    search_fields = ('title', 'description', 'teacher__user__last_name')
    autocomplete_fields = ['school_class', 'subject', 'teacher']

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('homework', 'student', 'submitted_at', 'grade')
    list_filter = ('homework__school_class__school', 'homework__subject', 'grade')
    search_fields = ('student__username', 'homework__title')
    autocomplete_fields = ['homework', 'student']

admin.site.register(Profile)