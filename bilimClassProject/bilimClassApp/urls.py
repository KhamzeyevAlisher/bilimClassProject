# bilimClassApp/urls.py

from django.urls import path, include
from . import views

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
]