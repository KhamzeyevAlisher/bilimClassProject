# bilimClassApp/urls.py

from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.custom_login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('accounts/login/', views.custom_login_view, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('teacher/journal/', views.journal_view, name='teacher_journal'),
    path('api/journal-grid-data/', views.get_journal_grid_data, name='api_get_journal_grid_data'),

    path('journal/grades-content/', views.get_grades_content, name='teacher_journal_grades_content'),
    
    # ... (URL для сохранения данных из старого журнала можно оставить, он нам пригодится)
    path('api/update-journal-entry/', views.update_journal_entry, name='api_update_journal_entry'),
    path('journal/', views.teacher_journal_view, name='teacher_journal'),
    path('api/set-grade/', views.set_grade_api, name='api_set_grade'),
    path('journal/attendance-content/', views.get_attendance_content, name='journal_attendance_content'),
    # URL для API сохранения статуса посещаемости
    path('api/set-attendance/', views.set_attendance_api, name='api_set_attendance'),
    # Уникальный URL для страницы ДЗ УЧИТЕЛЯ
    path('teacher/homeworks/', views.teacher_homework_view, name='teacher_homework'),
    
    # Уникальный URL для страницы ДЗ УЧЕНИКА
    path('student/homeworks/', views.student_homework_view, name='student_homework'),
    # Новый URL для API создания ДЗ
    path('api/homework/create/', views.create_homework_api, name='api_create_homework'),

    path('api/homework/<int:pk>/details/', views.get_homework_details_api, name='api_get_homework_details'),
    path('api/homework/<int:pk>/update/', views.update_homework_api, name='api_update_homework'),
    path('api/homework/<int:pk>/submit/', views.submit_homework_api, name='api_submit_homework'),

    path('api/homework/<int:pk>/submissions/', views.get_homework_submissions_api, name='api_get_homework_submissions'),
    path('api/submission/<int:pk>/grade/', views.grade_submission_api, name='api_grade_submission'),
    path('admin_panel/', views.admin_user_list_view, name='admin_panel'),
    path('api/user/manage/', views.manage_user_view, name='api_manage_user'),
    path('api/user/<int:user_id>/details/', views.get_user_details_view, name='api_get_user_details'),
    path('api/class/<int:class_id>/details/', views.class_details_api, name='class_details_api'),
    path('api/class/manage/', views.manage_class_api, name='manage_class_api'),
    # === НАЧАЛО НОВЫХ МАРШРУТОВ ===
    path('api/user/<int:user_id>/toggle-status/', views.toggle_user_status_api, name='toggle_user_status_api'),
    path('api/user/<int:user_id>/delete/', views.delete_user_api, name='delete_user_api'),
    # === КОНЕЦ НОВЫХ МАРШРУТОВ ===
    path('api/school/manage/', views.manage_school_api, name='manage_school_api'),
    path('api/school/<int:school_id>/details/', views.school_details_api, name='school_details_api'),
    path('api/school/<int:school_id>/delete/', views.delete_school_api, name='delete_school_api'),
    path('api/assignment/manage/', views.manage_assignment_api, name='manage_assignment_api'),
    path('api/assignment/<int:assignment_id>/delete/', views.delete_assignment_api, name='delete_assignment_api'),

    #завуч
    path('headteacher/', views.headteacher_view, name='headteacher'),
    path('api/school/<int:school_id>/classes/', views.get_classes_for_school_api, name='api_get_classes_for_school'),

    # === НАЧАЛО НОВЫХ МАРШРУТОВ ДЛЯ API РАСПИСАНИЯ ===
    path('api/schedule/manage/', views.manage_schedule_item_api, name='api_manage_schedule_item'),
    path('api/schedule/<int:pk>/details/', views.get_schedule_item_details_api, name='api_get_schedule_item_details'),
    path('api/schedule/<int:pk>/delete/', views.delete_schedule_item_api, name='api_delete_schedule_item'),
    # === КОНЕЦ НОВЫХ МАРШРУТОВ ===
    # === НАЧАЛО НОВЫХ МАРШРУТОВ ДЛЯ ПРЕДМЕТОВ ===
    path('api/subject/manage/', views.manage_subject_api, name='api_manage_subject'),
    path('api/subject/<int:pk>/details/', views.get_subject_details_api, name='api_get_subject_details'),
    path('api/subject/<int:pk>/delete/', views.delete_subject_api, name='api_delete_subject'),
    # === КОНЕЦ НОВЫХ МАРШРУТОВ ===
     # === НАЧАЛО НОВЫХ МАРШРУТОВ ДЛЯ ВЫХОДНЫХ ===
    path('api/holiday/manage/', views.manage_holiday_api, name='api_manage_holiday'),
    path('api/holiday/<int:pk>/details/', views.get_holiday_details_api, name='api_get_holiday_details'),
    path('api/holiday/<int:pk>/delete/', views.delete_holiday_api, name='api_delete_holiday'),
    # === КОНЕЦ НОВЫХ МАРШРУТОВ ДЛЯ ВЫХОДНЫХ ===
    path('api/class/<int:class_id>/performance/', views.get_class_performance_details_api, name='api_get_class_performance_details'),
     # === НАЧАЛО: URL-АДРЕСА ДЛЯ API ПОУРОЧНЫХ ПЛАНОВ ===
    path('api/lesson-plans/manage/', views.manage_lesson_plan_api, name='api_manage_lesson_plan'),
    path('api/lesson-plans/<int:pk>/details/', views.get_lesson_plan_details_api, name='api_get_lesson_plan_details'),
    path('api/lesson-plans/<int:pk>/delete/', views.delete_lesson_plan_api, name='api_delete_lesson_plan'),
    # === КОНЕЦ: URL-АДРЕСА ===
    path('api/lesson-plans/<int:pk>/update-status/', views.update_lesson_plan_status_api, name='api_update_lesson_plan_status'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/change-name/', views.change_name, name='change_name'),
    path('profile/change-email/', views.change_email, name='change_email'),
    path('api/student/<int:student_id>/performance/', views.get_student_performance_details_api, name='api_get_student_performance_details'),
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), 
         name="password_reset"),

    # 2. Страница с сообщением об отправке письма
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), 
         name="password_reset_done"),

    # 3. Страница для ввода нового пароля (пользователь переходит по ссылке из письма)
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), 
         name="password_reset_confirm"),

    # 4. Страница с сообщением об успешной смене пароля
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), 
         name="password_reset_complete"),
    # === НАЧАЛО НОВОГО КОДА: API ДЛЯ СУММАТИВНЫХ РАБОТ (БЖБ/ТЖБ) ===
    # Мұғалімдерге арналған API
    path('api/summative-assessment/create/', views.create_summative_assessment_api, name='api_create_summative_assessment'),
    path('api/summative-assessment/<int:pk>/details/', views.get_summative_assessment_details_api, name='api_get_summative_assessment_details'),
    path('api/summative-assessment/<int:pk>/update/', views.update_summative_assessment_api, name='api_update_summative_assessment'),
    path('api/summative-assessment/<int:pk>/delete/', views.delete_summative_assessment_api, name='api_delete_summative_assessment'),
    path('api/summative-assessment/<int:pk>/submissions/', views.get_summative_submissions_api, name='api_get_summative_submissions'),
    
    # Тапсырылған жұмысты бағалауға арналған API (submission_id бойынша)
#     path('api/summative-submission/<int:pk>/grade/', views.grade_summative_submission_api, name='api_grade_summative_submission'),
    path('api/summative/set-grade/', views.set_summative_grade_api, name='api_set_summative_grade'),
    # Оқушыларға арналған API
    path('api/summative-assessment/<int:pk>/submit/', views.submit_summative_assessment_api, name='api_submit_summative_assessment'),
    # === КОНЕЦ НОВОГО КОДА ===
    
]