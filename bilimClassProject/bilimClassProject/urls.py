# bilimClassProject/urls.py

from django.contrib import admin
from django.urls import path, include
# from bilimClassApp.forms import CustomLoginForm
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('accounts/', include('django.contrib.auth.urls')), # Добавляем URL-адреса для аутентификации
    path('', include('bilimClassApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)