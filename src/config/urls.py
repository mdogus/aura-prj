from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django_ratelimit.decorators import ratelimit

from core import views as core_views
from users.forms import AuraAuthenticationForm, AuraPasswordResetForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('healthz/', core_views.healthcheck_view, name='healthcheck'),
    path('accounts/', include('users.urls')),
    path('notifications/', include('notifications.urls')),
    path(
        'accounts/login/',
        # IP başına 5 dakikada en fazla 10 oturum açma denemesi
        ratelimit(key='ip', rate='10/5m', method='POST', block=True)(
            auth_views.LoginView.as_view(
                template_name='registration/login.html',
                authentication_form=AuraAuthenticationForm,
            )
        ),
        name='login',
    ),
    path(
        'accounts/password-reset/',
        # IP başına saatte en fazla 5 şifre sıfırlama isteği
        ratelimit(key='ip', rate='5/h', method='POST', block=True)(
            auth_views.PasswordResetView.as_view(
                template_name='registration/password_reset_form.html',
                form_class=AuraPasswordResetForm,
            )
        ),
        name='password_reset',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('support/', include('support.urls')),
    path('library/', include('library.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = core_views.permission_denied_view
handler404 = core_views.page_not_found_view
handler500 = core_views.server_error_view
