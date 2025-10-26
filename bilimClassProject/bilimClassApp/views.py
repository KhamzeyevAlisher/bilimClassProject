# bilimClassApp/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import ProfileForm, HomeworkForm, HomeworkSubmission, HomeworkSubmissionForm, UserManagementForm, SchoolClassForm, SchoolForm, ScheduleForm, SubjectForm
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
import json
from datetime import date, timedelta
from .decorators import group_required
from .models import Schedule, Teacher, Assessment, Subject, Holiday, Attendance,Profile, SchoolClass, School, Homework, HomeworkSubmission, TeacherAssignment
from django.db.models import Avg, Q, Count
from django.views.decorators.http import require_POST
import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.contrib.auth.models import User

def _get_redirect_for_user(user):
    """
    Вспомогательная функция для определения URL для переадресации
    на основе роли пользователя.
    """
    # Безопасно проверяем, есть ли у пользователя профиль и установлена ли роль
    if hasattr(user, 'profile') and user.profile.role:
        role = user.profile.role

        print(user.profile.role)
        
        if role == 'admin':
            return redirect('admin_panel')
        elif role == 'headteacher':
            return redirect('school_schedule')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('dashboard')
            
    # Переадресация по умолчанию (например, для учеников без явно указанной роли
    # или на случай непредвиденных обстоятельств)
    return redirect('dashboard')

def custom_login_view(request):
    """
    Обрабатывает вход пользователя и перенаправляет его в зависимости от роли.
    """
    # 1. Если пользователь УЖЕ вошел в систему, сразу перенаправляем его.
    if request.user.is_authenticated:
        return _get_redirect_for_user(request.user)

    # 2. Если пользователь отправляет форму для входа.
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # После успешного входа определяем, куда его перенаправить.
                return _get_redirect_for_user(user)
    else:
        form = AuthenticationForm()
        
    return render(request, 'registration/login.html', {'form': form})

# def custom_login_view(request):
#     if request.user.is_authenticated:
#         # Если пользователь уже вошел, сразу перенаправляем
#         if hasattr(request.user, 'teacher'):
#             return redirect('teacher_dashboard')
#         # Добавьте здесь elif для ученика, если нужно
#         # elif hasattr(request.user, 'student'):
#         #     return redirect('student_dashboard')
#         return redirect('dashboard') # Запасной вариант

#     if request.method == 'POST':
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 # Логика перенаправления после успешного входа
#                 if hasattr(user, 'teacher'):
#                     return redirect('teacher_dashboard')
#                 # elif hasattr(user, 'student'):
#                 #     return redirect('student_dashboard')
#                 return redirect('/')
#     else:
#         form = AuthenticationForm()
        
#     return render(request, 'registration/login.html', {'form': form})


def home(request):
    return render(request, 'bilimClassApp/home.html')

@login_required # Декоратор, который требует, чтобы пользователь был авторизован
def profile_view(request):
    current_user = request.user
    
    # Шаг 2: Пытаемся найти профиль Учителя, связанный с этим пользователем.
    # Так как не каждый пользователь - учитель, используем try-except для безопасности.
    teacher_profile = None
    schedule = Schedule.objects.none() # Готовим пустой queryset
    
    try:
        # Django автоматически создает обратную связь `user.teacher` из OneToOneField
        teacher_profile = current_user.teacher
    except Teacher.DoesNotExist:
        # Если профиль не найден, значит этот пользователь не учитель.
        # teacher_profile останется None, и мы обработаем это в шаблоне.
        pass
        
    # Шаг 3: Если профиль учителя найден, ищем его расписание.
    if teacher_profile:
        # Это основной запрос: найти все записи в Schedule, где поле teacher
        # равно найденному профилю.
        # teacher.schedule_set.all() - это альтернативный способ сделать то же самое.
        schedule = Schedule.objects.filter(teacher=teacher_profile).order_by('day_of_week', 'start_time')

    print(schedule)

    if request.method == 'POST':
        # AJAX-запрос
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Извлекаем данные из тела запроса
            data = json.loads(request.body)
            form = ProfileForm(data, instance=request.user.profile)
            if form.is_valid():
                form.save()
                return JsonResponse({'status': 'success', 'message': 'Профиль успешно обновлен!'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors})
        else:
            # Обычный POST-запрос (без AJAX)
            form = ProfileForm(request.POST, instance=request.user.profile)
            if form.is_valid():
                form.save()
                return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'bilimClassApp/profile.html', {'form': form})

@login_required
@group_required('Учитель', 'Завуч')
def teacher_dashboard(request):
    return render(request, 'bilimClassApp/teacher_dashboard.html')

# @login_required
# def dashboard_view(request):
#     # allow opening a specific tab via ?tab=homework|dnevnik|schedule|profile
#     active_tab = request.GET.get('tab') or 'schedule'
#     # ===============================================================
#     # 1. ОСНОВНЫЕ ПЕРЕМЕННЫЕ И ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЯ
#     # ===============================================================
#     current_user = request.user
#     role = current_user.groups.first()
    
#     # --- Переменные, которые мы будем заполнять и передавать в шаблон ---
#     user_role_name = "Пользователь"
#     schedule_by_day = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [] }
#     average_grade, total_grades_count, total_absences = None, 0, 0
#     attendance_percentage = 100.0
#     grades_by_subject = []
#     recent_assessments = []

#     # ===============================================================
#     # 2. ОСНОВНАЯ ЛОГИКА В ЗАВИСИМОСТИ ОТ РОЛИ ПОЛЬЗОВАТЕЛЯ
#     # ===============================================================
#     if role:
#         user_role_name = role.name
        
#         # --- ЕСЛИ ЗАШЕЛ УЧЕНИК ---
#         if role.name == 'Ученик':
#             student_class = current_user.school_classes.first()
#             if student_class:
#                 # 2.1 Получаем РАСПИСАНИЕ
#                 schedule_list = Schedule.objects.filter(school_class=student_class).order_by('start_time')
#                 for lesson in schedule_list:
#                     if lesson.day_of_week in schedule_by_day:
#                         schedule_by_day[lesson.day_of_week].append(lesson)
            
#                 # 2.2 Получаем ОЦЕНКИ и считаем статистику
#                 all_assessments_records = Assessment.objects.filter(student=current_user)
#                 assessments_with_grade = all_assessments_records.filter(was_absent=False)
#                 if assessments_with_grade.exists():
#                     total_grades_count = assessments_with_grade.count()
#                     avg_dict = assessments_with_grade.aggregate(avg_grade=Avg('grade'))
#                     average_grade = avg_dict['avg_grade']
                    
#                     subjects_with_grades = Subject.objects.filter(assessment__in=assessments_with_grade).distinct().order_by('name')
                    
#                     for subject in subjects_with_grades:
#                         # Получаем все оценки по этому предмету
#                         subject_grades_qs = assessments_with_grade.filter(subject=subject).order_by('-date')
                        
#                         # Считаем средний балл
#                         subject_avg = subject_grades_qs.aggregate(avg=Avg('grade'))['avg']

#                         # --- ДОБАВЛЕНА ЛОГИКА ПОИСКА УЧИТЕЛЯ ---
#                         # Ищем запись в расписании, чтобы найти учителя для этого предмета в этом классе
#                         teacher_name = "Не назначен"
#                         schedule_entry = Schedule.objects.filter(school_class=student_class, subject=subject).first()
#                         if schedule_entry and schedule_entry.teacher:
#                             teacher_name = schedule_entry.teacher.user.get_full_name()
#                         # --- КОНЕЦ ЛОГИКИ ПОИСКА УЧИТЕЛЯ ---
                        
#                         # Собираем словарь в ФОРМАТЕ, КОТОРЫЙ ОЖИДАЕТ ШАБЛОН
#                         grades_by_subject.append({
#                             'subject_name': subject.name,      # ИСПРАВЛЕНО: 'name' -> 'subject_name'
#                             'teacher_name': teacher_name,      # ДОБАВЛЕНО: имя учителя
#                             'average': subject_avg,
#                             'grades': subject_grades_qs       # ИСПРАВЛЕНО: 'assessments' -> 'grades'
#                         })
#                 recent_assessments = all_assessments_records.order_by('-date')[:10]

#                 # 2.3 Получаем ДОМАШНИЕ ЗАДАНИЯ для таба homework
#                 # Получаем все ДЗ, назначенные классу этого ученика
#                 all_homeworks = Homework.objects.filter(school_class=student_class).order_by('due_date')
                
#                 # Получаем все сданные этим учеником работы
#                 submissions = HomeworkSubmission.objects.filter(student=current_user, homework__in=all_homeworks)
#                 submitted_homework_ids = submissions.values_list('homework_id', flat=True)

#                 # Разделяем ДЗ на категории
#                 not_submitted = all_homeworks.exclude(pk__in=submitted_homework_ids)
#                 in_review = submissions.filter(grade__isnull=True)
#                 checked = submissions.filter(grade__isnull=False)

#                 # 2.4 Считаем ПРОЦЕНТ ПОСЕЩАЕМОСТИ (ПО УРОКАМ)
#                 today = date.today()
#                 if today.month >= 9:
#                     start_of_school_year = date(today.year, 9, 1)
#                 else:
#                     start_of_school_year = date(today.year - 1, 9, 1)

#                 attendance_records = Attendance.objects.filter(
#                     student=current_user, date__gte=start_of_school_year, date__lte=today
#                 )
#                 total_absences = attendance_records.exclude(status='present').count()
                
#                 total_lessons_held = 0
#                 holidays = set(Holiday.objects.filter(date__gte=start_of_school_year).values_list('date', flat=True))
                
#                 class_schedule = Schedule.objects.filter(school_class=student_class)
#                 lessons_per_weekday = {i: 0 for i in range(7)}
#                 for lesson in class_schedule:
#                     lessons_per_weekday[lesson.day_of_week - 1] += 1
                
#                 current_day = start_of_school_year
#                 while current_day <= today:
#                     if current_day.weekday() < 5 and current_day not in holidays:
#                         total_lessons_held += lessons_per_weekday.get(current_day.weekday(), 0)
#                     current_day += timedelta(days=1)
                    
#                 if total_lessons_held > 0:
#                     attended_lessons = total_lessons_held - total_absences
#                     attendance_percentage = (attended_lessons / total_lessons_held) * 100

#         # --- ЕСЛИ ЗАШЕЛ УЧИТЕЛЬ ---
#         elif role.name == 'Учитель':
#             try:
#                 teacher_profile = current_user.teacher
#                 schedule_list = Schedule.objects.filter(teacher=teacher_profile).order_by('start_time')
#                 for lesson in schedule_list:
#                     if lesson.day_of_week in schedule_by_day:
#                         schedule_by_day[lesson.day_of_week].append(lesson)
#             except Teacher.DoesNotExist:
#                 pass
                
#     # ===============================================================
#     # 3. ФОРМИРОВАНИЕ КОНТЕКСТА И РЕНДЕРИНГ ШАБЛОНА
#     # ===============================================================
#     context = {
#         'user_role': user_role_name,
#         'schedule_by_day': schedule_by_day,
#         'average_grade': average_grade,
#         'total_grades_count': total_grades_count,
#         'total_absences': total_absences,
#         'attendance_percentage': attendance_percentage,
#         'grades_by_subject': grades_by_subject,
#         'recent_assessments': recent_assessments,
#         'active_tab': active_tab,
#         'not_submitted_list': not_submitted if role and role.name == 'Ученик' else [],
#         'in_review_list': in_review if role and role.name == 'Ученик' else [],
#         'checked_list': checked if role and role.name == 'Ученик' else [],
#     }
    
#     return render(request, 'bilimClassApp/dashboard.html', context)

@login_required
def dashboard_view(request):
    # ===============================================================
    # 1. ПОЛУЧЕНИЕ ПАРАМЕТРОВ И ПОЛЬЗОВАТЕЛЯ
    # ===============================================================
    active_tab = request.GET.get('tab', 'schedule')
    # НОВОЕ: Получаем период фильтрации, по умолчанию - 'week' (неделя)
    period = request.GET.get('period', 'week')
    
    current_user = request.user
    role = current_user.groups.first()
    
    user_role_name = "Пользователь"
    schedule_by_day = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    grades_by_subject = []
    not_submitted, in_review, checked = [], [], []
    average_grade, total_grades_count, total_absences = None, 0, 0
    attendance_percentage = 100.0

    # ===============================================================
    # 2. ОСНОВНАЯ ЛОГИКА В ЗАВИСИМОСТИ ОТ РОЛИ
    # ===============================================================
    if role:
        user_role_name = role.name
        
        if role.name == 'Ученик':
            student_class = current_user.school_classes.first()
            if student_class:
                # 2.1 Получаем РАСПИСАНИЕ (без изменений)
                schedule_list = Schedule.objects.filter(school_class=student_class).order_by('start_time')
                for lesson in schedule_list:
                    if lesson.day_of_week in schedule_by_day:
                        schedule_by_day[lesson.day_of_week].append(lesson)

                # ======================================================
                # НОВОЕ: ЛОГИКА ФИЛЬТРАЦИИ ОЦЕНОК ПО ПЕРИОДУ
                # ======================================================
                today = date.today()
                start_date, end_date = None, None

                if period == 'week':
                    # Начало недели (понедельник)
                    start_date = today - timedelta(days=today.weekday())
                    # Конец недели (воскресенье)
                    end_date = start_date + timedelta(days=6)
                elif period == 'month':
                    # Начало месяца
                    start_date = today.replace(day=1)
                    # Конец месяца (сложный, но надежный способ)
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    end_date = next_month - timedelta(days=next_month.day)

                # Получаем все оценки ученика
                all_assessments_records = Assessment.objects.filter(student=current_user)
                
                # Если период не "all", применяем фильтр по дате
                if period != 'all':
                    all_assessments_records = all_assessments_records.filter(date__range=[start_date, end_date])
                
                # Дальнейшие расчеты будут использовать уже отфильтрованный queryset
                assessments_with_grade = all_assessments_records.filter(was_absent=False)
                # ======================================================
                
                # 2.2 Считаем статистику на основе отфильтрованных данных
                if assessments_with_grade.exists():
                    total_grades_count = assessments_with_grade.count()
                    avg_dict = assessments_with_grade.aggregate(avg_grade=Avg('grade'))
                    average_grade = avg_dict['avg_grade']
                    
                    # Собираем данные по предметам, используя отфильтрованные оценки
                    subjects_with_grades = Subject.objects.filter(assessment__in=assessments_with_grade).distinct().order_by('name')
                    for subject in subjects_with_grades:
                        subject_grades_qs = assessments_with_grade.filter(subject=subject).order_by('-date')
                        subject_avg = subject_grades_qs.aggregate(avg=Avg('grade'))['avg']
                        
                        teacher_name = "Не назначен"
                        schedule_entry = Schedule.objects.filter(school_class=student_class, subject=subject).first()
                        if schedule_entry and schedule_entry.teacher:
                            teacher_name = schedule_entry.teacher.user.get_full_name()
                        
                        grades_by_subject.append({
                            'subject_name': subject.name,
                            'teacher_name': teacher_name,
                            'average': subject_avg,
                            'grades': subject_grades_qs
                        })
                
                # 2.3 Получаем ДОМАШНИЕ ЗАДАНИЯ (без изменений)
                all_homeworks = Homework.objects.filter(school_class=student_class).order_by('due_date')
                submissions = HomeworkSubmission.objects.filter(student=current_user, homework__in=all_homeworks)
                submitted_homework_ids = submissions.values_list('homework_id', flat=True)
                not_submitted = all_homeworks.exclude(pk__in=submitted_homework_ids)
                in_review = submissions.filter(grade__isnull=True)
                checked = submissions.filter(grade__isnull=False)

                # 2.4 Считаем ПОСЕЩАЕМОСТЬ (без изменений)
                start_of_school_year = date(today.year, 9, 1) if today.month >= 9 else date(today.year - 1, 9, 1)
                attendance_records = Attendance.objects.filter(student=current_user, date__gte=start_of_school_year, date__lte=today)
                total_absences = attendance_records.exclude(status='P').count()
                
                # (остальная логика посещаемости без изменений...)
                total_lessons_held = 0
                holidays = set(Holiday.objects.filter(date__gte=start_of_school_year).values_list('date', flat=True))
                class_schedule = Schedule.objects.filter(school_class=student_class)
                lessons_per_weekday = {i: 0 for i in range(7)}
                for lesson in class_schedule:
                    lessons_per_weekday[lesson.day_of_week - 1] += 1
                current_day = start_of_school_year
                while current_day <= today:
                    if current_day.weekday() < 6 and current_day not in holidays:
                        total_lessons_held += lessons_per_weekday.get(current_day.weekday(), 0)
                    current_day += timedelta(days=1)
                if total_lessons_held > 0:
                    attended_lessons = total_lessons_held - total_absences
                    attendance_percentage = (attended_lessons / total_lessons_held) * 100

    # ===============================================================
    # 3. ФОРМИРОВАНИЕ КОНТЕКСТА И РЕНДЕРИНГ
    # ===============================================================
    context = {
        'user_role': user_role_name,
        'schedule_by_day': schedule_by_day,
        'average_grade': average_grade,
        'total_grades_count': total_grades_count,
        'total_absences': total_absences,
        'attendance_percentage': attendance_percentage,
        'grades_by_subject': grades_by_subject,
        'active_tab': active_tab,
        'not_submitted_list': not_submitted,
        'in_review_list': in_review,
        'checked_list': checked,
        'active_period': period, # НОВОЕ: передаем активный период в шаблон
    }
    
    return render(request, 'bilimClassApp/dashboard.html', context)

@login_required
def teacher_dashboard_view(request):
    """
    Отображает главную страницу (дашборд) для учителя.
    """
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return render(request, 'error.html', {'message': 'Доступ только для учителей.'})

    # Получаем расписание учителя на сегодня
    today_weekday = datetime.date.today().isoweekday()
    schedule_today = Schedule.objects.filter(
        teacher=teacher,
        day_of_week=today_weekday
    ).order_by('start_time').select_related('subject', 'school_class')

    # В будущем здесь будет логика для подсчета статистики
    # непроверенных работ, посещаемости и т.д.

    context = {
        'teacher': teacher,
        'schedule_today': schedule_today,
        'today': datetime.date.today(),
        # Заглушки для статистики
        'lessons_this_week': 12,
        'unchecked_works': 5,
        'avg_attendance': 98,
    }
    return render(request, 'bilimClassApp/teacher_dashboard.html', context)


# --- VIEWS ДЛЯ ОБРАБОТКИ AJAX-ЗАПРОСОВ ---

@login_required
def get_class_journal_data(request):
    """
    Возвращает JSON с данными для журнала: список учеников, уроков
    и уже существующих оценок/отметок о посещаемости.
    """
    class_id = request.GET.get('class_id')
    date_str = request.GET.get('date')

    if not class_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    selected_date = date.fromisoformat(date_str)
    
    # Находим класс и его учеников
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    students = school_class.students.all().order_by('last_name', 'first_name')
    
    # Находим уроки этого класса в этот день недели
    day_of_week = selected_date.weekday() + 1 # Пн=1..Вс=7
    lessons = Schedule.objects.filter(school_class=school_class, day_of_week=day_of_week).order_by('start_time')

    # Собираем существующие данные
    assessments = Assessment.objects.filter(student__in=students, date=selected_date, lesson__in=lessons)
    attendances = Attendance.objects.filter(student__in=students, date=selected_date, lesson__in=lessons)

    # Упаковываем данные для удобной работы в JavaScript
    grades_data = {
        f"{a.student_id}_{a.lesson_id}": {'grade': a.grade, 'comment': a.comment} for a in assessments
    }
    attendance_data = {
        f"{att.student_id}_{att.lesson_id}": att.status for att in attendances
    }
    
    return JsonResponse({
        'students': [{'id': s.id, 'full_name': s.get_full_name()} for s in students],
        'lessons': [{'id': l.id, 'subject': l.subject.name, 'time': l.start_time.strftime('%H:%M')} for l in lessons],
        'grades': grades_data,
        'attendance': attendance_data
    })


@login_required
@require_POST # Эта view будет принимать только POST-запросы
def update_journal_entry(request):
    """
    Создает или обновляет оценку И/ИЛИ отметку о посещаемости.
    Принимает JSON с данными.
    """
    try:
        data = json.loads(request.body)
        student = get_object_or_404(User, pk=data.get('student_id'))
        lesson = get_object_or_404(Schedule, pk=data.get('lesson_id'))
        entry_date = date.fromisoformat(data.get('date'))
        entry_type = data.get('type') # 'grade', 'comment', or 'attendance'
        value = data.get('value')
        
        # Обновляем посещаемость
        if entry_type == 'attendance':
            Attendance.objects.update_or_create(
                student=student, lesson=lesson, date=entry_date,
                defaults={'status': value}
            )
            # Если поставили "Присутствовал", удаляем оценку, если она была "пропуском"
            if value == 'present':
                 Assessment.objects.filter(student=student, lesson=lesson, date=entry_date, was_absent=True).delete()
            else: # Если поставили пропуск/опоздание, создаем "пустую" оценку
                 Assessment.objects.update_or_create(
                     student=student, lesson=lesson, date=entry_date,
                     defaults={'was_absent': True, 'grade': None, 'comment': ''}
                 )

        # Обновляем оценку или комментарий
        elif entry_type in ['grade', 'comment']:
            # Используем get_or_create, чтобы не было ошибки, если оценки еще нет
            assessment, created = Assessment.objects.get_or_create(
                student=student, lesson=lesson, date=entry_date,
                defaults={
                    'school_class': lesson.school_class,
                    'subject': lesson.subject,
                    'teacher': request.user.teacher
                }
            )
            # Обновляем нужное поле
            if entry_type == 'grade':
                # Превращаем пустую строку в None для базы данных
                assessment.grade = int(value) if value else None
            elif entry_type == 'comment':
                assessment.comment = value
            
            assessment.was_absent = False # Если ставят оценку, значит не отсутствовал
            assessment.save()
            # Убедимся, что статус посещаемости "Присутствовал"
            Attendance.objects.update_or_create(
                student=student, lesson=lesson, date=entry_date,
                defaults={'status': 'present'}
            )
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
@group_required('Учитель', 'Завуч', 'Администратор')
def journal_view(request):
    """Отображает основную страницу журнала."""
    try:
        teacher_profile = request.user.teacher
        teacher_classes = SchoolClass.objects.filter(
            schedule__teacher=teacher_profile
        ).distinct().order_by('name')
    except Teacher.DoesNotExist:
        teacher_classes = SchoolClass.objects.none()

    context = { 'teacher_classes': teacher_classes }
    return render(request, 'bilimClassApp/journal_view.html', context)

@login_required
def get_journal_grid_data(request):
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'error': 'Не выбран класс'}, status=400)
    
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    students = school_class.students.all().order_by('last_name', 'first_name')
    
    dates = []
    current_date = date.today()
    holidays = set(Holiday.objects.values_list('date', flat=True))
    days_to_check = 0
    while len(dates) < 5 and days_to_check < 30:
        if current_date.weekday() < 5 and current_date not in holidays:
            dates.append(current_date)
        current_date -= timedelta(days=1)
        days_to_check += 1
    dates.reverse()

    all_assessments = Assessment.objects.filter(student__in=students, date__in=dates)
    all_attendances = Attendance.objects.filter(student__in=students, date__in=dates) # <-- Исправлено имя

    grades_data = {}
    attendance_data = {}

    for student in students:
        student_id = student.id
        
        # --- ГОТОВИМ ДАННЫЕ ДЛЯ ВКЛАДКИ "ОЦЕНКИ" ---
        grades_data[student_id] = {}
        student_assessments = all_assessments.filter(student=student, was_absent=False)
        avg = student_assessments.aggregate(avg=Avg('grade'))['avg']
        grades_data[student_id]['avg_grade'] = f"{avg:.2f}" if avg is not None else "0.00"

        for d in dates:
            grade_obj = all_assessments.filter(student=student, date=d).first()
            grades_data[student_id][d.isoformat()] = {
                'grade': grade_obj.grade if grade_obj and not grade_obj.was_absent else None,
                'comment': grade_obj.comment if grade_obj else None,
                'was_absent': grade_obj.was_absent if grade_obj else False,
            }
            
        # --- ГОТОВИМ ДАННЫЕ ДЛЯ ВКЛАДКИ "ПОСЕЩАЕМОСТЬ" ---
        attendance_data[student_id] = {}
        total_absences = all_attendances.filter(student=student).exclude(status='present').count()
        
        # Заглушка для процента, можно улучшить позже
        attendance_data[student_id]['percentage'] = 100 - (total_absences * 5)
        
        for d in dates:
            att_obj = all_attendances.filter(student=student, date=d).first()
            status = 'present' # Статус по умолчанию, если нет записи
            if att_obj:
                status = att_obj.status
            # Проверяем также "пропуск" из модели Оценок
            elif grades_data[student_id][d.isoformat()]['was_absent']:
                status = 'truant'

            attendance_data[student_id][d.isoformat()] = status

    return JsonResponse({
        'students': [{'id': s.id, 'full_name': s.get_full_name()} for s in students],
        'dates': [d.isoformat() for d in dates],
        'grades_data': grades_data,
        'attendance_data': attendance_data,
    })

# @login_required
# def teacher_journal_view(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return HttpResponseForbidden("Доступ к этой странице есть только у учителей.")

    all_schools = School.objects.all()
    selected_school_id = request.GET.get('school_id')
    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')

    teacher_classes = SchoolClass.objects.none()
    if selected_school_id:
        teacher_classes = SchoolClass.objects.filter(school_id=selected_school_id)

    teacher_subjects = teacher.subjects.all()

    context = {
        'teacher': teacher,
        'all_schools': all_schools,
        'teacher_classes': teacher_classes,
        'teacher_subjects': teacher_subjects,
        'selected_school_id': int(selected_school_id) if selected_school_id else None,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
        'journal_data': [],
        'date_range': []
    }

    if selected_school_id and selected_class_id and selected_subject_id:
        selected_class = get_object_or_404(SchoolClass, pk=selected_class_id)
        students = selected_class.students.all().order_by('last_name', 'first_name')
        
        date_range = [datetime.date.today() - datetime.timedelta(days=i) for i in range(5)][::-1]
        context['date_range'] = date_range

        all_grades = Assessment.objects.filter(
            school_class_id=selected_class_id,
            subject_id=selected_subject_id,
            date__in=date_range
        ).select_related('student')

        grades_by_student_and_date = {}
        for grade in all_grades:
            if grade.student_id not in grades_by_student_and_date:
                grades_by_student_and_date[grade.student_id] = {}
            grades_by_student_and_date[grade.student_id][grade.date] = grade

        journal_data = []
        for student in students:
            # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Создаем список словарей, где каждый словарь - это одна ячейка таблицы
            cells = []
            for date in date_range:
                cells.append({
                    'date': date,
                    'grade': grades_by_student_and_date.get(student.pk, {}).get(date)
                })
            
            average_grade = Assessment.objects.filter(
                student=student, subject_id=selected_subject_id, grade__isnull=False
            ).aggregate(avg=Avg('grade'))['avg']

            journal_data.append({
                'student': student,
                'cells': cells, # Передаем в шаблон готовый список ячеек
                'average': average_grade
            })
        
        context['journal_data'] = journal_data

        print(journal_data)
    
    
    return render(request, 'bilimClassApp/teacher_journal.html', context)

@login_required
def teacher_journal_view(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return HttpResponseForbidden("Доступ к этой странице есть только у учителей.")

    selected_school_id = request.GET.get('school_id')
    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')

    # 1. Получаем только те школы, в которых у учителя есть назначения.
    # Мы фильтруем школы через связанные модели SchoolClass и TeacherAssignment.
    teacher_schools = School.objects.filter(
        schoolclass__teacherassignment__teacher=teacher
    ).distinct()

    # 2. Если школа выбрана, получаем классы учителя только в этой школе.
    teacher_classes = SchoolClass.objects.none()
    if selected_school_id:
        teacher_classes = SchoolClass.objects.filter(
            school_id=selected_school_id,
            teacherassignment__teacher=teacher
        ).distinct()

    # 3. Если класс выбран, получаем предметы, которые учитель ведет в этом классе.
    teacher_subjects = Subject.objects.none()
    if selected_class_id:
        teacher_subjects = Subject.objects.filter(
            teacherassignment__school_class_id=selected_class_id,
            teacherassignment__teacher=teacher
        ).distinct()

    context = {
        'teacher': teacher,
        'all_schools': teacher_schools,        # Передаем отфильтрованный список школ
        'teacher_classes': teacher_classes,    # Передаем отфильтрованный список классов
        'teacher_subjects': teacher_subjects,  # Передаем отфильтрованный список предметов
        'selected_school_id': int(selected_school_id) if selected_school_id else None,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
        'journal_data': [],
        'date_range': []
    }

    # --- Остальная часть функции остается без изменений ---
    # Она корректно работает с уже выбранными и переданными ID
    if selected_school_id and selected_class_id and selected_subject_id:
        selected_class = get_object_or_404(SchoolClass, pk=selected_class_id)
        students = selected_class.students.all().order_by('last_name', 'first_name')
        
        date_range = [datetime.date.today() - datetime.timedelta(days=i) for i in range(5)][::-1]
        context['date_range'] = date_range

        all_grades = Assessment.objects.filter(
            school_class_id=selected_class_id,
            subject_id=selected_subject_id,
            date__in=date_range
        ).select_related('student')

        grades_by_student_and_date = {}
        for grade in all_grades:
            if grade.student_id not in grades_by_student_and_date:
                grades_by_student_and_date[grade.student_id] = {}
            grades_by_student_and_date[grade.student_id][grade.date] = grade

        journal_data = []
        for student in students:
            cells = []
            for date in date_range:
                cells.append({
                    'date': date,
                    'grade': grades_by_student_and_date.get(student.pk, {}).get(date)
                })
            
            average_grade = Assessment.objects.filter(
                student=student, subject_id=selected_subject_id, grade__isnull=False
            ).aggregate(avg=Avg('grade'))['avg']

            journal_data.append({
                'student': student,
                'cells': cells,
                'average': average_grade
            })
        
        context['journal_data'] = journal_data
    
    return render(request, 'bilimClassApp/teacher_journal.html', context)
@login_required
def set_grade_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User is not a teacher'}, status=403)

    data = json.loads(request.body)
    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    class_id = data.get('class_id')
    date_str = data.get('date')
    grade_val = data.get('grade')
    comment_val = data.get('comment', '') # Получаем комментарий, по умолчанию - пустая строка

    if not all([student_id, subject_id, class_id, date_str]):
        return JsonResponse({'status': 'error', 'message': 'Missing required data'}, status=400)

    assessment, created = Assessment.objects.update_or_create(
        student_id=student_id,
        subject_id=subject_id,
        school_class_id=class_id,
        date=date_str,
        # Добавляем comment в defaults
        defaults={
            'teacher': teacher, 
            'grade': grade_val if grade_val else None, 
            'was_absent': False,
            'comment': comment_val
        }
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Оценка сохранена',
        'grade': assessment.grade,
        'has_comment': bool(assessment.comment) # Возвращаем флаг, есть ли комментарий
    })

@login_required
def get_attendance_content(request):
    """
    Возвращает HTML-фрагмент с таблицей посещаемости.
    Теперь также подсчитывает пропуски.
    """
    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')
    
    if not (selected_class_id and selected_subject_id):
        return HttpResponse("Пожалуйста, выберите класс и предмет.")

    selected_class = get_object_or_404(SchoolClass, pk=selected_class_id)
    # Используем select_related('profile'), если у вас есть связь с профилем для ФИО
    students = selected_class.students.all().order_by('last_name', 'first_name')
    date_range = [datetime.date.today() - datetime.timedelta(days=i) for i in range(5)][::-1]

    all_records = Attendance.objects.filter(
        school_class_id=selected_class_id,
        subject_id=selected_subject_id,
        date__in=date_range
    )
    
    records_by_student_date = {
        (rec.student_id, rec.date): rec for rec in all_records
    }

    attendance_data = []
    for student in students:
        cells = [{'date': date, 'record': records_by_student_date.get((student.pk, date))} for date in date_range]
        
        # Подсчет пропусков (статусы 'A' - Absent)
        absent_count = Attendance.objects.filter(
            student=student,
            subject_id=selected_subject_id,
            status=Attendance.Status.ABSENT
        ).count()

        attendance_data.append({
            'student': student, 
            'cells': cells,
            'absent_count': absent_count
        })

    context = {
        'attendance_data': attendance_data,
        'date_range': date_range,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id
    }
    return render(request, 'partials/attendance_table.html', context) # Возвращаем пустой ответ, если фильтры не выбраны


@login_required
def set_attendance_api(request):
    """API для сохранения статуса посещаемости."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST is allowed'}, status=405)
    
    data = json.loads(request.body)
    
    # Используем update_or_create для удобства
    record, created = Attendance.objects.update_or_create(
        student_id=data.get('student_id'),
        subject_id=data.get('subject_id'),
        school_class_id=data.get('class_id'),
        date=data.get('date'),
        defaults={'status': data.get('status')}
    )
    
    return JsonResponse({'status': 'success', 'new_status': record.get_status_display(), 'new_status_code': record.status})

@login_required
def get_grades_content(request):
    """Возвращает HTML-фрагмент с таблицей ОЦЕНОК."""
    # Получаем параметры фильтрации
    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')

    journal_data = []
    date_range = []
    if selected_class_id and selected_subject_id:
        selected_class = get_object_or_404(SchoolClass, pk=selected_class_id)
        students = selected_class.students.all().order_by('last_name', 'first_name')
        date_range = [datetime.date.today() - datetime.timedelta(days=i) for i in range(5)][::-1]

        all_grades = Assessment.objects.filter(
            school_class_id=selected_class_id,
            subject_id=selected_subject_id,
            date__in=date_range
        ).select_related('student')
        
        grades_by_student_and_date = { (g.student_id, g.date): g for g in all_grades }

        for student in students:
            cells = [{'date': date, 'grade': grades_by_student_and_date.get((student.pk, date))} for date in date_range]
            average_grade = Assessment.objects.filter(student=student, subject_id=selected_subject_id, grade__isnull=False).aggregate(avg=Avg('grade'))['avg']
            journal_data.append({'student': student, 'cells': cells, 'average': average_grade})

    context = {
        'journal_data': journal_data,
        'date_range': date_range,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id,
    }
    # Эта функция рендерит ТОЛЬКО таблицу, а не всю страницу
    return render(request, 'partials/_grades_table.html', context)

@login_required
def teacher_homework_view(request):
    # Здесь в будущем будет логика для получения списка ДЗ из базы
    context = {}
    return render(request, 'bilimClassApp/teacher_homework.html', context)

@login_required
def teacher_homework_view(request):
    """
    Отображает страницу с домашними заданиями и формой для их создания.
    """
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return HttpResponseForbidden("Доступ только для учителей.")
        
    # Получаем все домашние задания, созданные этим учителем
    homeworks = Homework.objects.filter(teacher=teacher).annotate(
        submission_count=Count('submissions'),
        checked_count=Count('submissions', filter=Q(submissions__grade__isnull=False))
    ).prefetch_related('school_class', 'subject')

    # Создаем экземпляр формы, передавая в него учителя
    form = HomeworkForm(teacher=teacher)
    
    context = {
        'teacher': teacher,
        'homework_form': form, # Передаем форму в шаблон
        'homeworks': homeworks, # Передаем список ДЗ
    }
    return render(request, 'bilimClassApp/teacher_homework.html', context)

@login_required
def create_homework_api(request):
    """
    API эндпоинт для создания домашнего задания через AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User is not a teacher'}, status=403)

    # request.POST для текстовых данных, request.FILES для файлов
    form = HomeworkForm(request.POST, request.FILES, teacher=teacher)
    
    if form.is_valid():
        # Сохраняем форму, но пока не в базу данных
        homework = form.save(commit=False)
        # Присваиваем автора-учителя
        homework.teacher = teacher
        homework.save()
        
        # Если все успешно, возвращаем статус success
        return JsonResponse({'status': 'success', 'message': 'Домашнее задание успешно создано!'})
    else:
        # Если форма невалидна, возвращаем ошибки
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
def get_homework_details_api(request, pk):
    """
    API, возвращающий данные одного ДЗ для заполнения формы редактирования.
    """
    try:
        # Убедимся, что ДЗ существует и принадлежит текущему учителю
        homework = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher)
        
        data = {
            'title': homework.title,
            'description': homework.description,
            'school_class': homework.school_class_id,
            'subject': homework.subject_id,
            # Форматируем дату для поля datetime-local
            'due_date': homework.due_date.strftime('%Y-%m-%dT%H:%M'), 
            'file_url': homework.attached_file.url if homework.attached_file else '',
            'file_name': str(homework.attached_file).split('/')[-1] if homework.attached_file else ''
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Homework.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Homework not found'}, status=404)
    
@login_required
def update_homework_api(request, pk):
    """
    API для обновления существующего домашнего задания.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        homework = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher)
    except Homework.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Homework not found or access denied'}, status=404)

    # Передаем instance в форму, чтобы она знала, какой объект обновлять
    form = HomeworkForm(request.POST, request.FILES, instance=homework, teacher=request.user.teacher)

    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success', 'message': 'Задание успешно обновлено!'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@login_required
def student_homework_view(request):
    """
    Отображает домашние задания в дашборде.
    """
    return redirect(f"{reverse('dashboard')}?tab=homework")

@login_required
def submit_homework_api(request, pk):
    """
    API для сдачи домашнего задания.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    homework = get_object_or_404(Homework, pk=pk)
    
    # Проверяем, не сдавал ли ученик эту работу ранее
    if HomeworkSubmission.objects.filter(homework=homework, student=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'Вы уже сдали эту работу.'}, status=400)

    form = HomeworkSubmissionForm(request.POST, request.FILES)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.homework = homework
        submission.student = request.user
        submission.save()
        return JsonResponse({'status': 'success', 'message': 'Работа успешно отправлена!'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
# @login_required
# def get_homework_submissions_api(request, pk):
#     """
#     API, возвращающее список всех учеников класса и статусы их работ
#     по конкретному домашнему заданию.
#     """
#     try:
#         # Убеждаемся, что ДЗ существует и принадлежит текущему учителю
#         homework = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher)
        
#         # Получаем всех учеников из класса, которому было дано ДЗ
#         students_in_class = homework.school_class.students.all().order_by('last_name', 'first_name')
        
#         # Получаем все сданные работы по этому ДЗ
#         submissions = HomeworkSubmission.objects.filter(homework=homework)
        
#         # Для быстрого поиска создаем словарь {student_id: submission_object}
#         submissions_map = {sub.student.id: sub for sub in submissions}
        
#         response_data = []
#         for student in students_in_class:
#             student_data = {
#                 'student_id': student.id,
#                 'full_name': student.get_full_name(),
#                 'status': 'Ожидается',
#                 'submitted_at': None,
#                 'grade': None,
#             }
            
#             # Если ученик есть в словаре сданных работ
#             if student.id in submissions_map:
#                 submission = submissions_map[student.id]
#                 student_data['submitted_at'] = submission.submitted_at.strftime('%d.%m.%Y')
                
#                 # Если работа проверена (есть оценка)
#                 if submission.grade is not None:
#                     student_data['status'] = 'Проверено'
#                     student_data['grade'] = submission.grade
#                 else:
#                     student_data['status'] = 'Сдано'

#             response_data.append(student_data)
            
#         return JsonResponse({'status': 'success', 'submissions': response_data})
        
#     except Homework.DoesNotExist:
#         return JsonResponse({'status': 'error', 'message': 'Homework not found or access denied'}, status=404)
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

# @login_required
# def get_homework_submissions_api(request, pk):
#     homework = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher)
#     students_in_class = homework.school_class.students.all().order_by('last_name', 'first_name')
#     submissions = HomeworkSubmission.objects.filter(homework=homework)
#     submissions_map = {sub.student.id: sub for sub in submissions}
    
#     response_data = []
#     for student in students_in_class:
#         submission_obj = submissions_map.get(student.id)
#         status = 'Ожидается'
#         if submission_obj:
#             status = 'Проверено' if submission_obj.grade is not None else 'Сдано'

#         response_data.append({
#             'submission_id': submission_obj.id if submission_obj else None,
#             'student_id': student.id,
#             'full_name': student.get_full_name(),
#             'status': status,
#             'submitted_at': submission_obj.submitted_at.strftime('%d.%m.%Y') if submission_obj else None,
#             'grade': submission_obj.grade if submission_obj else None,
#             'teacher_comment': submission_obj.teacher_comment if submission_obj else "",
#         })
            
#     return JsonResponse({'status': 'success', 'submissions': response_data})

@login_required
def get_homework_submissions_api(request, pk):
    homework = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher)
    students_in_class = homework.school_class.students.all().order_by('last_name', 'first_name')
    submissions = HomeworkSubmission.objects.filter(homework=homework)
    submissions_map = {sub.student.id: sub for sub in submissions}
    
    response_data = []
    for student in students_in_class:
        submission_obj = submissions_map.get(student.id)
        status = 'Ожидается'
        if submission_obj:
            status = 'Проверено' if submission_obj.grade is not None else 'Сдано'

        response_data.append({
            'submission_id': submission_obj.id if submission_obj else None,
            'student_id': student.id,
            'full_name': student.get_full_name(),
            'status': status,
            'submitted_at': submission_obj.submitted_at.strftime('%d.%m.%Y') if submission_obj else None,
            'grade': submission_obj.grade if submission_obj else None,
            'teacher_comment': submission_obj.teacher_comment if submission_obj else "",
            
            # --- ДОБАВЛЕННЫЕ СТРОКИ ---
            'file_url': submission_obj.submission_file.url if submission_obj and submission_obj.submission_file else None,
            'submission_text': submission_obj.submission_text if submission_obj else None,
            # --- КОНЕЦ ДОБАВЛЕННЫХ СТРОК ---
        })
            
    return JsonResponse({'status': 'success', 'submissions': response_data})

# === НОВАЯ VIEW ДЛЯ СОХРАНЕНИЯ РЕЦЕНЗИИ ===
@login_required
@require_POST
def grade_submission_api(request, pk):
    """
    API для сохранения оценки и комментария к сданной работе.
    АВТОМАТИЧЕСКИ создает или обновляет запись в общей модели Assessment.
    """
    try:
        data = json.loads(request.body)
        submission = get_object_or_404(HomeworkSubmission, pk=pk)

        # Проверка безопасности
        if submission.homework.teacher != request.user.teacher:
            return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

        # 1. Обновляем саму сданную работу (HomeworkSubmission)
        grade = data.get('grade')
        comment = data.get('comment', '')

        submission.grade = int(grade) if grade not in [None, ''] else None
        submission.teacher_comment = comment
        submission.checked_at = timezone.now()
        submission.save()

        # 2. Создаем или обновляем связанную оценку в общем журнале (Assessment)
        if submission.grade is not None:
            # Используем update_or_create для избежания дубликатов.
            # Мы ищем оценку, которая напрямую связана с этой сданной работой.
            Assessment.objects.update_or_create(
                submission=submission,  # Это наша уникальная связь
                defaults={
                    'student': submission.student,
                    'school_class': submission.homework.school_class,
                    'subject': submission.homework.subject,
                    'teacher': request.user.teacher,
                    'date': submission.checked_at.date(),
                    'assessment_type': Assessment.AssessmentType.HOMEWORK,
                    'grade': submission.grade,
                    'comment': submission.teacher_comment,
                    'was_absent': False
                }
            )
        else:
            # Если оценку убрали (поставили "Без оценки"), удаляем ее из общего журнала.
            Assessment.objects.filter(submission=submission).delete()

        return JsonResponse({
            'status': 'success', 
            'message': 'Рецензия сохранена и оценка добавлена в журнал',
            'new_grade': submission.grade
        })
    except HomeworkSubmission.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Submission not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def is_staff_check(user):
    """
    Проверяет, является ли пользователь персоналом (staff),
    чтобы предоставить доступ к панели администратора.
    """
    return user.is_staff

# @login_required
# @user_passes_test(is_staff_check, login_url='/')
# def admin_user_list_view(request):
#     """
#     Отображает главную страницу панели администратора,
#     обрабатывает фильтрацию и поиск пользователей.
#     """
#     users_list = User.objects.select_related('profile').order_by('last_name', 'first_name')

#     # Получение параметров фильтрации из GET-запроса
#     search_query = request.GET.get('q', '')
#     role_filter = request.GET.get('role', '')
#     status_filter = request.GET.get('status', '')

#     # Применение фильтра по поисковому запросу
#     if search_query:
#         users_list = users_list.filter(
#             Q(first_name__icontains=search_query) |
#             Q(last_name__icontains=search_query) |
#             Q(email__icontains=search_query)
#         )

#     # Применение фильтра по роли
#     if role_filter:
#         users_list = users_list.filter(profile__role=role_filter)

#     # Применение фильтра по статусу
#     if status_filter:
#         if status_filter == 'active':
#             users_list = users_list.filter(is_active=True)
#         elif status_filter == 'inactive':
#             users_list = users_list.filter(is_active=False)

#     # Оптимизированный запрос для получения данных о классах для вкладки "Структура школы"
#     school_classes_for_structure = SchoolClass.objects.select_related(
#         'class_teacher__user'
#     ).annotate(student_count=Count('students')).order_by('name')

#     all_assignments = TeacherAssignment.objects.select_related(
#         'teacher__user', 
#         'school_class', 
#         'subject'
#     ).all()
    
#     context = {
#         'users': users_list,
#         'role_choices': Profile.ROLE_CHOICES,
        
#         # Данные для вкладки "Структура школы"
#         'structure_school_classes': school_classes_for_structure,
#         'all_teachers': Teacher.objects.select_related('user').all(), # <-- Добавлено: передаем всех учителей для модального окна
        
#         # Данные для модального окна создания/редактирования пользователя
#         'all_schools': School.objects.all().order_by('name'), 
#         'school_classes': SchoolClass.objects.all(),
#         'subjects': Subject.objects.all(),
        
#         # Текущие значения фильтров для отображения в форме
#         'search_query': search_query,
#         'role_filter': role_filter,
#         'status_filter': status_filter,
#     }
#     return render(request, 'bilimClassApp/admin_panel.html', context)

@login_required
@user_passes_test(is_staff_check, login_url='/')
def admin_user_list_view(request):
    """
    Отображает главную страницу панели администратора,
    обрабатывает фильтрацию и поиск пользователей.
    """
    users_list = User.objects.select_related('profile').order_by('last_name', 'first_name')

    # Получение параметров фильтрации из GET-запроса
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    # Применение фильтра по поисковому запросу
    if search_query:
        users_list = users_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Применение фильтра по роли
    if role_filter:
        users_list = users_list.filter(profile__role=role_filter)

    # Применение фильтра по статусу
    if status_filter:
        if status_filter == 'active':
            users_list = users_list.filter(is_active=True)
        elif status_filter == 'inactive':
            users_list = users_list.filter(is_active=False)

    # Оптимизированный запрос для получения данных о классах для вкладки "Структура школы"
    school_classes_for_structure = SchoolClass.objects.select_related(
        'class_teacher__user'
    ).annotate(student_count=Count('students')).order_by('name')

    # =====================================================================
    # === ИЗМЕНЕНИЕ №1: ДОБАВЛЯЕМ ЗАПРОС ДЛЯ ПОЛУЧЕНИЯ НАЗНАЧЕНИЙ ===
    # =====================================================================
    # Используем select_related для оптимизации запроса и предотвращения
    # лишних обращений к БД при отрисовке таблицы в шаблоне.
    all_assignments = TeacherAssignment.objects.select_related(
        'teacher__user',
        'school_class',
        'subject'
    ).all()
    # =====================================================================

    context = {
        'users': users_list,
        'role_choices': Profile.ROLE_CHOICES,
        
        # Данные для вкладки "Структура школы"
        'structure_school_classes': school_classes_for_structure,
        
        # =====================================================================
        # === ИЗМЕНЕНИЕ №2: ПЕРЕДАЕМ НАЗНАЧЕНИЯ В КОНТЕКСТ ШАБЛОНА ===
        # =====================================================================
        'all_assignments': all_assignments,
        # =====================================================================

        # Данные для модального окна создания/редактирования пользователя
        'all_teachers': Teacher.objects.select_related('user').all(),
        'all_schools': School.objects.all().order_by('name'),
        'school_classes': SchoolClass.objects.all(),
        'subjects': Subject.objects.all(),
        
        # Текущие значения фильтров для отображения в форме
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'bilimClassApp/admin_panel.html', context)

def get_user_details_view(request, user_id):
    """
    API-эндпоинт. Возвращает данные пользователя в формате JSON 
    для заполнения модальной формы редактирования.
    """
    try:
        user = User.objects.select_related('profile').get(id=user_id)
        
        data = {
            "id": user.id,
            "full_name": user.get_full_name(),
            "email": user.email,
            "is_active": user.is_active,
            "role": user.profile.role,
            "school_class_id": "",
            "subject_ids": [],
        }
        
        if user.profile.role == 'student' and user.school_classes.first():
            data['school_class_id'] = user.school_classes.first().id
        
        if user.profile.role == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                data['subject_ids'] = list(teacher.subjects.values_list('id', flat=True))
            except Teacher.DoesNotExist:
                pass 

        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

def manage_user_view(request):
    """
    API-эндпоинт. Создает или обновляет пользователя, используя данные из POST-запроса.
    """
    if request.method == 'POST':
        form = UserManagementForm(request.POST)

        if form.is_valid():
            form.save() 
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_class_details_view(request, class_id):
    """
    API-эндпоинт. Возвращает данные класса в формате JSON
    для заполнения модальной формы редактирования.
    """
    try:
        school_class = get_object_or_404(SchoolClass, id=class_id)
        student_count = school_class.students.count()
        
        data = {
            "id": school_class.id,
            "name": school_class.name,
            # === ДОБАВЛЕНО: Возвращаем ID школы ===
            "school_id": school_class.school_id,
            "class_teacher_id": school_class.class_teacher.user_id if school_class.class_teacher else "",
            "student_count": student_count,
        }
        return JsonResponse(data)
    except SchoolClass.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)


def manage_class_view(request):
    """
    API-эндпоинт. Создает или обновляет класс на основе данных из POST-запроса.
    """
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        instance = None
        if class_id:
            instance = get_object_or_404(SchoolClass, id=class_id)
        
        form = SchoolClassForm(request.POST, instance=instance)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def class_details_api(request, class_id):
    try:
        s_class = SchoolClass.objects.get(id=class_id)

        student_count = s_class.students.count()
        
        data = {
            'id': s_class.id,
            'name': s_class.name,
            'class_teacher_id': s_class.class_teacher.user.id if s_class.class_teacher else None,
            'student_count': student_count, # Предполагается, что это поле или метод в модели
        }
        return JsonResponse(data)
    except SchoolClass.DoesNotExist:
        return JsonResponse({'error': 'Class not found'}, status=404)
    
@require_POST
def manage_class_api(request):
    data = request.POST
    class_id = data.get('class_id')
    name = data.get('name')
    teacher_user_id = data.get('class_teacher')
    # === ДОБАВЛЕНО: Получаем ID школы из формы ===
    school_id = data.get('school')

    # === ДОБАВЛЕНО: Валидация на наличие школы ===
    if not name:
        return JsonResponse({'errors': {'name': 'Это поле обязательно'}}, status=400)
    if not school_id:
        return JsonResponse({'errors': {'school': 'Необходимо выбрать школу'}}, status=400)

    try:
        if class_id:
            # Редактирование
            s_class = get_object_or_404(SchoolClass, id=class_id)
            s_class.name = name
            s_class.school_id = school_id # Обновляем школу, если ее изменили
        else:
            # Создание
            # === ИЗМЕНЕНО: Создаем класс, указывая школу ===
            s_class = SchoolClass(name=name, school_id=school_id)

        # Назначение классного руководителя (без изменений)
        if teacher_user_id:
            teacher_profile = Teacher.objects.get(user__id=teacher_user_id)
            s_class.class_teacher = teacher_profile
        else:
            s_class.class_teacher = None
        
        s_class.save()
        return JsonResponse({'status': 'ok'})

    except Teacher.DoesNotExist:
        return JsonResponse({'errors': {'class_teacher': 'Учитель не найден'}}, status=400)
    except School.DoesNotExist:
        return JsonResponse({'errors': {'school': 'Выбранная школа не найдена'}}, status=400)
    except Exception as e:
        return JsonResponse({'errors': str(e)}, status=500)


@require_POST
@login_required
@user_passes_test(is_staff_check) # Доступ только для персонала
def toggle_user_status_api(request, user_id):
    """
    API-эндпоинт для блокировки/разблокировки пользователя (переключает is_active).
    """
    try:
        user = get_object_or_404(User, pk=user_id)
        # Не позволяем администратору заблокировать самого себя
        if user == request.user:
            return JsonResponse({'status': 'error', 'message': 'Вы не можете заблокировать себя.'}, status=403)
        
        # Переключаем статус
        user.is_active = not user.is_active
        user.save()
        
        return JsonResponse({'status': 'success', 'is_active': user.is_active})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
@login_required
@user_passes_test(is_staff_check) # Доступ только для персонала
def delete_user_api(request, user_id):
    """
    API-эндпоинт для полного удаления пользователя.
    """
    try:
        user = get_object_or_404(User, pk=user_id)
        # Не позволяем администратору удалить самого себя
        if user == request.user:
            return JsonResponse({'status': 'error', 'message': 'Вы не можете удалить себя.'}, status=403)
        
        user.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@require_POST
@login_required
@user_passes_test(is_staff_check)
def manage_assignment_api(request):
    """API для создания нового назначения."""
    teacher_id = request.POST.get('teacher')
    class_id = request.POST.get('school_class')
    subject_id = request.POST.get('subject')
    hours = request.POST.get('hours_per_week', 1) # По умолчанию 1 час

    if not all([teacher_id, class_id, subject_id]):
        return JsonResponse({'status': 'error', 'message': 'Все поля обязательны для заполнения.'}, status=400)

    try:
        TeacherAssignment.objects.create(
            teacher_id=teacher_id,
            school_class_id=class_id,
            subject_id=subject_id,
            hours_per_week=hours
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        # Это может быть ошибка IntegrityError, если такое назначение уже существует
        return JsonResponse({'status': 'error', 'message': 'Не удалось создать назначение. Возможно, оно уже существует.'}, status=400)


@require_POST
@login_required
@user_passes_test(is_staff_check)
def delete_assignment_api(request, assignment_id):
    """API для удаления назначения."""
    try:
        assignment = get_object_or_404(TeacherAssignment, pk=assignment_id)
        assignment.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
@user_passes_test(is_staff_check)
def school_details_api(request, school_id):
    """Возвращает детали школы для заполнения формы редактирования."""
    school = get_object_or_404(School, pk=school_id)
    data = {
        'id': school.id,
        'name': school.name,
        'address': school.address, # <-- Адаптируйте, если поле называется иначе
    }
    return JsonResponse(data)

@require_POST
@login_required
@user_passes_test(is_staff_check)
def manage_school_api(request):
    """Создает или обновляет школу."""
    school_id = request.POST.get('school_id')
    instance = get_object_or_404(School, pk=school_id) if school_id else None
    
    form = SchoolForm(request.POST, instance=instance)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@require_POST
@login_required
@user_passes_test(is_staff_check)
def delete_school_api(request, school_id):
    """Удаляет школу."""
    school = get_object_or_404(School, pk=school_id)
    school.delete()
    return JsonResponse({'status': 'success'})

# === КОНЕЦ НОВЫХ ФУНКЦИЙ ===

@login_required
def school_schedule_view(request):
    """
    Отображает страницу с расписанием школы с возможностью фильтрации
    по школе и классу.
    """
    all_schools = School.objects.all().order_by('name')
    selected_school_id = request.GET.get('school_id')
    selected_class_id = request.GET.get('class_id')

    classes_in_school = SchoolClass.objects.none()
    schedule_by_day = {
        1: [], 2: [], 3: [], 4: [], 5: [], 6: []
    }
    
    # Инициализируем форму с указанием school_id, если он есть
    schedule_form = ScheduleForm(school_id=selected_school_id, class_id=selected_class_id)
    all_subjects = Subject.objects.all().order_by('name')


    if selected_school_id:
        classes_in_school = SchoolClass.objects.filter(school_id=selected_school_id).order_by('name')

    if selected_class_id:
        schedule_items = Schedule.objects.filter(
            school_class_id=selected_class_id
        ).select_related('subject', 'teacher__user').order_by('start_time')
        
        for item in schedule_items:
            if item.day_of_week in schedule_by_day:
                schedule_by_day[item.day_of_week].append(item)

    context = {
        'all_schools': all_schools,
        'classes_in_school': classes_in_school,
        'selected_school_id': int(selected_school_id) if selected_school_id else None,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'schedule_by_day': schedule_by_day,
        'days_of_week': {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"},
        'schedule_form': schedule_form, # Передаем форму в шаблон
        'all_subjects': all_subjects, # Передаем все предметы для модального окна
    }
    return render(request, 'bilimClassApp/head_school.html', context)


@login_required
def get_classes_for_school_api(request, school_id):
    """
    API, возвращающее список классов для указанной школы.
    """
    classes = SchoolClass.objects.filter(school_id=school_id).order_by('name')
    data = [{'id': c.id, 'name': c.name} for c in classes]
    return JsonResponse(data, safe=False)


# === НАЧАЛО НОВЫХ VIEW ДЛЯ УПРАВЛЕНИЯ РАСПИСАНИЕМ ===

@require_POST
@login_required
def manage_schedule_item_api(request):
    """API для создания или обновления урока в расписании."""
    schedule_id = request.POST.get('schedule_id')
    instance = get_object_or_404(Schedule, pk=schedule_id) if schedule_id else None
    
    # Получаем все нужные ID из запроса
    school_id = request.POST.get('school_id')
    class_id = request.POST.get('school_class_id')
    
    # === ИСПРАВЛЕНИЕ ЗДЕСЬ ===
    # Теперь передаем в форму и school_id, и class_id для корректной валидации
    form = ScheduleForm(request.POST, instance=instance, school_id=school_id, class_id=class_id)
    # ==========================

    if form.is_valid():
        item = form.save(commit=False)
        # Добавляем недостающие данные, которые не были в форме
        item.school_class_id = class_id # Это значение уже получено выше
        item.day_of_week = request.POST.get('day_of_week')
        item.save()
        return JsonResponse({'status': 'success'})
    else:
        # Если форма не прошла валидацию, возвращаем ошибки
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
def get_schedule_item_details_api(request, pk):
    """API для получения деталей одного урока для редактирования."""
    item = get_object_or_404(Schedule, pk=pk)
    data = {
        'id': item.id,
        'subject': item.subject_id,
        'teacher': item.teacher_id,
        'start_time': item.start_time.strftime('%H:%M'),
        'end_time': item.end_time.strftime('%H:%M'),
        'classroom': item.classroom,
        'day_of_week': item.day_of_week, # <== ИЗМЕНЕНИЕ ЗДЕСЬ: ДОБАВЬТЕ ЭТУ СТРОКУ
    }
    return JsonResponse(data)


@require_POST
@login_required
def delete_schedule_item_api(request, pk):

    """API для удаления урока."""
    try:
        item = get_object_or_404(Schedule, pk=pk)
        item.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@require_POST
@login_required
@user_passes_test(is_staff_check)
def manage_subject_api(request):
    """API для создания или обновления предмета."""
    subject_id = request.POST.get('subject_id')
    instance = get_object_or_404(Subject, pk=subject_id) if subject_id else None
    
    form = SubjectForm(request.POST, instance=instance)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@user_passes_test(is_staff_check)
def get_subject_details_api(request, pk):
    """API для получения данных одного предмета для формы редактирования."""
    subject = get_object_or_404(Subject, pk=pk)
    data = {
        'id': subject.id,
        'name': subject.name,
    }
    return JsonResponse(data)

@require_POST
@login_required
@user_passes_test(is_staff_check)
def delete_subject_api(request, pk):
    """API для удаления предмета."""
    try:
        subject = get_object_or_404(Subject, pk=pk)
        subject.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)