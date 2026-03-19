from django.conf import settings
from django.db import models
from django.utils import timezone

from support.models import SupportRequest


class Notification(models.Model):
    TYPE_METADATA = {
        'message': {'label': 'Mesaj', 'icon': 'icon-chat'},
        'material': {'label': 'Kaynak dosya', 'icon': 'icon-upload'},
        'match': {'label': 'Eşleşme', 'icon': 'icon-users'},
        'status': {'label': 'Durum güncellemesi', 'icon': 'icon-check'},
        'general': {'label': 'Genel bildirim', 'icon': 'icon-bell'},
    }

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
    )
    support_request = models.ForeignKey(
        SupportRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    target_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def _notification_text(self):
        return f"{self.title} {self.body}".lower()

    @property
    def notification_type(self):
        text = self._notification_text()
        if 'mesaj' in text:
            return 'message'
        if 'materyal' in text or 'kaynak dosya' in text or 'dosya' in text:
            return 'material'
        if 'eşleş' in text or 'gonullu' in text or 'gönüllü' in text or 'atama' in text:
            return 'match'
        if (
            'durum' in text
            or 'tamamlandı' in text
            or 'iptal' in text
            or 'sürüyor' in text
        ):
            return 'status'
        return 'general'

    @property
    def notification_type_label(self):
        return self.TYPE_METADATA[self.notification_type]['label']

    @property
    def notification_icon(self):
        return self.TYPE_METADATA[self.notification_type]['icon']
