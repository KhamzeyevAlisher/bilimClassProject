# bilimClassApp/admin.py

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group

# Убедитесь, что все ваши модели импортированы
from .models import (
    School, Subject, SchoolClass, Teacher, Schedule, Assessment, Holiday,
    Attendance, Homework, HomeworkSubmission, Profile, TeacherAssignment
)

# -----------------------------------------------------------------------------
# ЧАСТЬ 1: Кастомизация админки для стандартной модели User
# (Этот код у вас уже был, он остается без изменений)
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

# Перерегистрация модели User с нашими настройками
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# -----------------------------------------------------------------------------
# ЧАСТЬ 2: Регистрация НАШИХ моделей с улучшенными настройками
# (Существующие регистрации остаются, добавлены новые)
# -----------------------------------------------------------------------------

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address']
    list_display = ('name', 'address')

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    search_fields = ['name', 'school__name']
    autocomplete_fields = ['school', 'class_teacher'] # Добавлено поле class_teacher для удобного поиска
    filter_horizontal = ['students']
    list_display = ('name', 'school', 'class_teacher') # Добавлено отображение классного руководителя
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

# =============================================================================
# === НОВАЯ ЧАСТЬ: Регистрация модели TeacherAssignment (Назначения учителей) ===
# =============================================================================
@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    """
    Админка для модели "Назначения учителей".
    Это ключевая модель, которая связывает Учителя, Класс и Предмет.
    """
    # Поля для отображения в списке
    list_display = ('teacher', 'school_class', 'subject', 'hours_per_week')

    # Фильтры для удобной навигации
    list_filter = ('school_class__school', 'teacher', 'school_class', 'subject')

    # Поля для поиска (позволяет искать по имени учителя, названию класса и т.д.)
    search_fields = (
        'teacher__user__first_name',
        'teacher__user__last_name',
        'school_class__name',
        'subject__name'
    )
    
    # Использование полей с поиском вместо гигантских выпадающих списков
    autocomplete_fields = ['teacher', 'school_class', 'subject']
    
    # Сортировка по умолчанию
    ordering = ('teacher', 'school_class')

# =============================================================================

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    search_fields = (
        'subject__name',
        'school_class__name',
        'school_class__school__name',
        'teacher__user__first_name',
        'teacher__user__last_name',
    )
    list_display = ('__str__', 'teacher')
    list_filter = ('school_class__school', 'school_class', 'teacher', 'day_of_week')
    autocomplete_fields = ['school_class', 'subject', 'teacher']

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade', 'date', 'assessment_type', 'school_class', 'teacher')
    list_filter = ('date', 'school_class', 'subject', 'teacher', 'assessment_type')
    search_fields = (
        'student__username', 'student__first_name', 'student__last_name',
        'subject__name', 'grade'
    )
    autocomplete_fields = ('student', 'school_class', 'subject', 'teacher', 'submission')
    ordering = ('-date',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    search_fields = ('name',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'subject', 'school_class', 'status')
    list_filter = ('date', 'status', 'school_class__school', 'school_class', 'subject')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject__name')
    autocomplete_fields = ['student', 'subject', 'school_class']
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
    ordering = ('-submitted_at',)

# =============================================================================
# === УЛУЧШЕННАЯ ЧАСТЬ: Регистрация модели Profile ===
# =============================================================================
# Вместо простого admin.site.register(Profile) используем класс для лучшей настройки
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админка для Профилей пользователей."""
    list_display = ('user', 'get_full_name', 'role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('role',)
    autocomplete_fields = ('user',)

    # Добавляем метод для отображения полного имени в списке
    @admin.display(description='Полное имя', ordering='user__first_name')
    def get_full_name(self, obj):
        return obj.user.get_full_name()
# =============================================================================