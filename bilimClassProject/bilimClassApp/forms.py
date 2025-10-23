# bilimClassApp/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Homework, SchoolClass, Subject, School, Profile, HomeworkSubmission # Импортируем нужные модели

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'location', 'birth_date')

class CustomLoginForm(AuthenticationForm):
    # Переопределяем поля, чтобы добавить виджеты с атрибутами
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Ваш логин', 
        'class': 'form-control-custom' # Можно добавить класс, если нужно
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': '*********',
        'class': 'form-control-custom'
    }))

# class HomeworkForm(forms.ModelForm):
#     class Meta:
#         model = Homework
#         fields = ['title', 'description', 'school_class', 'subject', 'due_date', 'attached_file']
#         # Указываем виджеты для полей, чтобы Django использовал правильные типы в HTML
#         widgets = {
#             'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }

#     def __init__(self, *args, **kwargs):
#         # Получаем учителя из view, чтобы автоматически его подставить
#         teacher = kwargs.pop('teacher', None)
#         super().__init__(*args, **kwargs)

#         if teacher:
#             # Фильтруем предметы, чтобы учитель видел только те, которые он ведет
#             self.fields['subject'].queryset = teacher.subjects.all()
#             # Фильтруем классы, чтобы учитель видел только классы своей школы
#             self.fields['school_class'].queryset = SchoolClass.objects.filter(school=teacher.school)

class HomeworkForm(forms.ModelForm):
    # Указываем тип поля для даты и времени для удобного виджета
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Срок сдачи"
    )

    class Meta:
        model = Homework
        fields = ['title', 'school_class', 'subject', 'due_date', 'description', 'attached_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Например, "Анализ произведения" '}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишите, что нужно сделать ученикам...'}),
        }
        labels = {
            'title': "Название задания",
            'school_class': "Класс",
            'subject': "Предмет",
            'description': "Описание задания",
            'attached_file': "Прикрепить файл (необязательно)",
        }

    def __init__(self, *args, **kwargs):
        # 1. Извлекаем учителя, которого мы передали из views.py
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # 2. Если учитель был передан...
        if teacher:
            # 3. ...фильтруем queryset для полей 'school_class' и 'subject'
            
            # Находим все классы, в которых учитель ведет уроки по расписанию
            self.fields['school_class'].queryset = SchoolClass.objects.filter(
                schedule__teacher=teacher
            ).distinct().order_by('name')
            
            # Ограничиваем выбор предметов только теми, которые преподает учитель
            self.fields['subject'].queryset = teacher.subjects.all().order_by('name')
            
            # Добавляем пустой элемент "---------" для обоих полей
            self.fields['school_class'].empty_label = "Выберите класс"
            self.fields['subject'].empty_label = "Выберите предмет"

class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        # Указываем только те поля, которые заполняет ученик
        fields = ['submission_text', 'submission_file']