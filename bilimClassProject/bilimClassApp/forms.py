# bilimClassApp/forms.py

from django import forms
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import Homework, SchoolClass, Subject, School, Profile, HomeworkSubmission, Teacher, Schedule,  Holiday, LessonPlan # Импортируем нужные модели

class ProfileForm(forms.ModelForm):
    
    birth_date = forms.DateField(label='Туылған күні',required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Profile
        fields = ('bio', 'location', 'birth_date', 'phone_number','iin',)


    def clean_phone_number(self):
        # Получаем данные из поля
        phone = self.cleaned_data.get('phone_number')

        # Если поле пустое, ничего не делаем, так как оно необязательное
        if not phone:
            return phone

        # Очищаем номер от лишних символов для проверки
        cleaned_phone = ''.join(filter(str.isdigit, phone))

        # Проверяем, что после очистки остались только цифры и их достаточное количество
        # Например, от 10 (без кода страны) до 12 (с кодом страны)
        if not cleaned_phone.isdigit() or not (10 <= len(cleaned_phone) <= 12):
            # Если проверка не пройдена, вызываем ошибку валидации
            raise forms.ValidationError("Пожалуйста, введите корректный номер телефона (например, +77071234567).")
            
        # Если все хорошо, возвращаем исходное (неочищенное) значение
        return phone
    
    # 2. --- НОВЫЙ МЕТОД ВАЛИДАЦИИ ДЛЯ ИИН ---
    def clean_iin(self):
        iin = self.cleaned_data.get('iin')

        # Если поле пустое, ничего не делаем
        if not iin:
            return iin

        # Проверяем, что в поле только цифры
        if not iin.isdigit():
            raise forms.ValidationError("ИИН должен состоять только из цифр.")

        # Проверяем, что длина поля ровно 12 символов
        if len(iin) != 12:
            raise forms.ValidationError("ИИН должен состоять ровно из 12 цифр.")
            
        # Если все проверки пройдены, возвращаем значение
        return iin

# --- НОВЫЙ КЛАСС ФОРМЫ ДЛЯ СМЕНЫ ПАРОЛЯ ---
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        # Сначала вызываем родительский конструктор
        super().__init__(*args, **kwargs)
        
        # Убираем атрибут 'autofocus' из виджета поля old_password
        if 'autofocus' in self.fields['old_password'].widget.attrs:
            del self.fields['old_password'].widget.attrs['autofocus']

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
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': ''}),
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
            self.fields['school_class'].empty_label = "Тандаңыз"
            self.fields['subject'].empty_label = "Тандаңыз"

class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        # Указываем только те поля, которые заполняет ученик
        fields = ['submission_text', 'submission_file']


class UserManagementForm(forms.Form):
    # Поля из User
    full_name = forms.CharField(label="ФИО", max_length=150, required=True)
    # === НАЧАЛО ИЗМЕНЕНИЙ ===
    username = forms.CharField(label="Логин (Username)", max_length=150, required=True)
    # === КОНЕЦ ИЗМЕНЕНИЙ ===
    email = forms.EmailField(label="Email", required=True)
    is_active = forms.ChoiceField(label="Статус", choices=[(True, 'Активен'), (False, 'Заблокирован')])

    # Поля из Profile
    phone_number = forms.CharField(label="Телефон", max_length=20, required=False)
    role = forms.ChoiceField(label="Роль", choices=Profile.ROLE_CHOICES)

    # Поля для специфичных ролей
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Класс", required=False
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        label="Предметы", required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}) # для удобства
    )

    # Скрытое поле для ID при редактировании
    user_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    @transaction.atomic
    def save(self):
        # Используем transaction.atomic, чтобы все изменения либо прошли успешно, либо откатились
        user_id = self.cleaned_data.get('user_id')
        user = User.objects.get(id=user_id) if user_id else None

        # --- 1. Обработка User ---
        if not user:
            # === НАЧАЛО ИЗМЕНЕНИЙ ===
            # Создание нового пользователя. Теперь username берется из формы.
            username = self.cleaned_data['username']
            # === КОНЕЦ ИЗМЕНЕНИЙ ===
            user = User.objects.create_user(username=username, email=self.cleaned_data['email'])
            # Устанавливаем временный пароль. В реальной системе лучше отправлять email.
            user.set_password('password123')

        user._role_to_set = self.cleaned_data['role']
        
        # Обновление данных User
        name_parts = self.cleaned_data['full_name'].split()
        user.first_name = name_parts[0] if len(name_parts) > 0 else ''
        user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        # === НАЧАЛО ИЗМЕНЕНИЙ ===
        user.username = self.cleaned_data['username'] # Обновляем username и при редактировании
        # === КОНЕЦ ИЗМЕНЕНИЙ ===
        user.email = self.cleaned_data['email']
        user.is_active = self.cleaned_data['is_active'] == 'True'
        user.save()

        # --- 2. Обработка Profile ---
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = self.cleaned_data['role']
        profile.phone_number = self.cleaned_data.get('phone_number', '') # Добавим сохранение номера телефона
        profile.save()

        # --- 3. Обработка в зависимости от роли ---
        role = self.cleaned_data['role']

        if role == 'student':
            # Удаляем пользователя из всех классов, где он мог быть
            user.school_classes.clear()
            # Добавляем в выбранный класс
            selected_class = self.cleaned_data.get('school_class')
            if selected_class:
                selected_class.students.add(user)
            # Убеждаемся, что для этого юзера нет записи Teacher
            Teacher.objects.filter(user=user).delete()

        elif role == 'teacher':
            # Создаем или получаем запись Teacher
            teacher, _ = Teacher.objects.get_or_create(user=user)
            # Обновляем его предметы
            selected_subjects = self.cleaned_data.get('subjects')
            if selected_subjects:
                teacher.subjects.set(selected_subjects)
            else:
                teacher.subjects.clear()
            # Убеждаемся, что ученик удален из всех классов
            user.school_classes.clear()
        
        else: # Если роль - админ, завуч или другая
            # Очищаем все связи на всякий случай
            user.school_classes.clear()
            Teacher.objects.filter(user=user).delete()

        return user
    
    # === НАЧАЛО ИЗМЕНЕНИЙ ===
    def clean_username(self):
        """Проверяет уникальность username."""
        username = self.cleaned_data.get('username')
        user_id = self.cleaned_data.get('user_id')

        # При создании нового пользователя (user_id еще нет)
        if not user_id:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Этот логин уже занят.")
        # При редактировании существующего
        else:
            # Проверяем, существует ли пользователь с таким username, исключая текущего
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                raise forms.ValidationError("Этот логин уже занят.")
        
        return username
    # === КОНЕЦ ИЗМЕНЕНИЙ ===
    
class SchoolClassForm(forms.ModelForm):
    """
    Форма для создания и редактирования школьного класса.
    """
    # Определяем поле для классного руководителя, чтобы можно было настроить его виджет и queryset
    class_teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.select_related('user').all(),
        required=False, # Классный руководитель может быть не назначен
        label="Классный руководитель",
        help_text="Выберите классного руководителя из списка учителей."
    )

    class Meta:
        model = SchoolClass
        # Указываем поля, которые будут в форме
        fields = ['name', 'class_teacher']
        # Задаем кастомные метки для полей
        labels = {
            'name': 'Класс (например, 9А)',
        }
        # Добавляем кастомные виджеты для лучшего отображения
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Введите название класса'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Переопределяем конструктор, чтобы добавить кастомную пустую метку
        для выбора классного руководителя.
        """
        super().__init__(*args, **kwargs)
        self.fields['class_teacher'].empty_label = "Не назначен"

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        # Укажите поля, которые пользователь может редактировать через форму
        fields = ['name', 'address'] # <-- Адаптируйте, если у вас другие поля
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Например, Гимназия №17'}),
            'address': forms.TextInput(attrs={'placeholder': 'Например, г. Астана, ул. Мира, 1'}),
        }


# class ScheduleForm(forms.ModelForm):
#     class Meta:
#         model = Schedule
#         fields = ['subject', 'teacher', 'start_time', 'end_time', 'classroom']
#         widgets = {
#             'start_time': forms.TimeInput(attrs={'type': 'time'}),
#             'end_time': forms.TimeInput(attrs={'type': 'time'}),
#         }

#     def __init__(self, *args, **kwargs):
#         # Получаем ID школы, переданный из view
#         school_id = kwargs.pop('school_id', None)
#         super().__init__(*args, **kwargs)
        
#         # Устанавливаем русские названия для полей
#         self.fields['subject'].label = "Предмет"
#         self.fields['teacher'].label = "Учитель"
#         self.fields['start_time'].label = "Время начала"
#         self.fields['end_time'].label = "Время окончания"
#         self.fields['classroom'].label = "Кабинет"

#         # Если школа выбрана, фильтруем учителей, которые к ней привязаны
#         if school_id:
#             self.fields['teacher'].queryset = Teacher.objects.filter(
#                 school_id=school_id
#             ).select_related('user').order_by('user__last_name')
#         else:
#             # Если школа не выбрана, показываем пустой список
#             self.fields['teacher'].queryset = Teacher.objects.none()

#         # Делаем все поля обязательными для заполнения
#         for field in self.fields:
#             self.fields[field].required = True

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['subject', 'teacher', 'start_time', 'end_time', 'classroom']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        # Извлекаем school_id и class_id из переданных аргументов
        school_id = kwargs.pop('school_id', None)
        class_id = kwargs.pop('class_id', None) # <== НОВОЕ
        
        super().__init__(*args, **kwargs)
        
        self.fields['subject'].label = "Пән"
        self.fields['teacher'].label = "Мұғалім"
        self.fields['start_time'].label = "Басталуы"
        self.fields['end_time'].label = "Аяқталуы"
        self.fields['classroom'].label = "Кабинет"

        # ЛОГИКА ФИЛЬТРАЦИИ
        if class_id:
            # Если выбран класс, показываем ТОЛЬКО назначенных учителей и предметы
            self.fields['teacher'].queryset = Teacher.objects.filter(
                teacherassignment__school_class_id=class_id
            ).distinct().select_related('user').order_by('user__last_name')
            
            self.fields['subject'].queryset = Subject.objects.filter(
                teacherassignment__school_class_id=class_id
            ).distinct().order_by('name')
            
        elif school_id:
            # Если класс не выбран, но выбрана школа - показываем всех учителей школы
            self.fields['teacher'].queryset = Teacher.objects.filter(
                school_id=school_id
            ).select_related('user').order_by('user__last_name')
            # Предметы оставляем все, или тоже можно как-то ограничить, если нужно
            self.fields['subject'].queryset = Subject.objects.all().order_by('name')
        else:
            # Если ничего не выбрано, показываем пустые списки (чтобы не перегружать страницу)
            self.fields['teacher'].queryset = Teacher.objects.none()
            # self.fields['subject'].queryset = Subject.objects.none() # Можно раскомментировать, если хотите скрывать и предметы

        for field in self.fields:
            self.fields[field].required = True

class SubjectForm(forms.ModelForm):
    """Форма для создания и редактирования учебного предмета."""
    class Meta:
        model = Subject
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Название предмета"
        self.fields['name'].widget.attrs.update({
            'placeholder': 'Например, Алгебра'
        })

class HolidayForm(forms.ModelForm):
    """Форма для создания и редактирования выходных дней."""
    class Meta:
        model = Holiday
        fields = ['date', 'name']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Например, День независимости'}),
        }

class LessonPlanForm(forms.ModelForm):
    # Мы переопределяем __init__, чтобы фильтровать классы и предметы
    # для конкретного учителя, который создает/редактирует план.
    def __init__(self, *args, **kwargs):
        # Извлекаем учителя из переданных аргументов
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Фильтруем queryset для поля 'school_class'. Показываем только те классы,
            # где у учителя есть назначение (TeacherAssignment).
            self.fields['school_class'].queryset = SchoolClass.objects.filter(
                teacherassignment__teacher=teacher
            ).distinct().order_by('name')

            # Фильтруем предметы аналогичным образом.
            self.fields['subject'].queryset = Subject.objects.filter(
                teacherassignment__school_class__teacherassignment__teacher=teacher
            ).distinct().order_by('name')

    class Meta:
        model = LessonPlan
        fields = [
            'name', 'date', 'school_class', 'subject', 'topic', 
            'goals_and_objectives', 'learning_materials'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'goals_and_objectives': forms.Textarea(attrs={'rows': 3}),
            # 'learning_materials': forms.Textarea(attrs={'rows': 3}),
        }


class UserNameChangeForm(forms.ModelForm):
    class Meta:
        model = User # Работаем с основной моделью User
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': 'Атыңыз',
            'last_name': 'Фамилияныз',
        }

class EmailChangeForm(forms.Form):
    # required=True гарантирует, что поле не будет пустым
    email = forms.EmailField(
        label="Жаңа email", 
        required=True,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'Введите новый email'})
    )
    # strip=False важно для паролей, чтобы не обрезались пробелы
    password = forms.CharField(
        label="Растау үшін ағымдағы құпия сөз", 
        required=True, 
        strip=False, 
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )