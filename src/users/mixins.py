from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class ActiveUserRequiredMixin:
    inactive_message = (
        'Hesabınız şu anda aktif değil. Devam etmek için koordinasyon ekibiyle iletişime geçin.'
    )

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
            messages.error(request, self.inactive_message)
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(ActiveUserRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('Bu alana erişim yetkiniz yok.')
        return super().dispatch(request, *args, **kwargs)
