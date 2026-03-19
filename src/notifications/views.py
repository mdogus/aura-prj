from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from users.mixins import ActiveUserRequiredMixin

from .models import Notification


class NotificationListView(LoginRequiredMixin, ActiveUserRequiredMixin, ListView):
    model = Notification
    context_object_name = 'notifications'
    template_name = 'notifications/list.html'

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.request.GET.get('filter') == 'unread':
            queryset = queryset.filter(is_read=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_notifications = Notification.objects.filter(recipient=self.request.user)
        context['selected_filter'] = self.request.GET.get('filter', 'all')
        context['total_notification_count'] = all_notifications.count()
        context['unread_notification_total'] = all_notifications.filter(
            is_read=False
        ).count()
        return context


class NotificationMarkAllReadView(LoginRequiredMixin, ActiveUserRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        messages.success(request, 'Tüm bildirimler okundu olarak işaretlendi.')
        return redirect('notifications:list')


class NotificationOpenView(LoginRequiredMixin, ActiveUserRequiredMixin, View):
    def get(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.mark_as_read()
        return redirect(notification.target_url or 'notifications:list')


class NotificationMarkReadView(LoginRequiredMixin, ActiveUserRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.mark_as_read()
        messages.success(request, 'Bildirim okundu olarak işaretlendi.')
        filter_value = request.GET.get('filter')
        if filter_value == 'unread':
            return redirect(f"{redirect('notifications:list').url}?filter=unread")
        return redirect('notifications:list')
