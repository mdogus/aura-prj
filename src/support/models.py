from calendar import monthrange
from datetime import timedelta
from pathlib import PurePath
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def request_material_upload_to(instance, filename):
    today = timezone.localdate()
    clean_name = PurePath(str(filename).replace("\\", "/")).name
    original_path = PurePath(clean_name)
    extension = original_path.suffix.lower()
    stem = slugify(original_path.stem) or "dosya"
    short_stem = stem[:48].strip("-") or "dosya"
    unique_suffix = uuid4().hex[:8]
    return (
        f"request_materials/{today:%Y/%m/%d}/"
        f"{short_stem}-{unique_suffix}{extension}"
    )


class SupportRequest(models.Model):
    class Categories(models.TextChoices):
        ACCESSIBLE_MATERIAL = (
            "accessible_material",
            "Erişilebilir materyal hazırlama",
        )
        AUDIO_NARRATION = ("audio_narration", "Seslendirme")
        ACADEMIC = ("academic", "Akademik destek")
        JOINT_STUDY = ("joint_study", "Birlikte ders çalışma")
        VISUAL_DESCRIPTION = ("visual_description", "Görsel betimleme")
        RESOURCE_ACCESS = ("resource_access", "Kaynak erişimi")
        EXAM_PREPARATION = ("exam_preparation", "Sınav hazırlık")
        WAYFINDING = ("wayfinding", "Bağımsız hareket, yön bulma ve rehberlik")
        DAILY_LIFE = ("daily_life", "Günlük yaşam")
        SOCIAL_ACTIVITY = ("social_activity", "Sosyal etkinlik")

    class Statuses(models.TextChoices):
        OPEN = ("open", "Açık")
        MATCHED = ("matched", "Eşleşti")
        IN_PROGRESS = ("in_progress", "Sürüyor")
        COMPLETED = ("completed", "Tamamlandı")
        CANCELLED = ("cancelled", "İptal edildi")

    class Urgencies(models.TextChoices):
        LOW = ("low", "Düşük")
        MEDIUM = ("medium", "Orta")
        HIGH = ("high", "Yüksek")

    class Priorities(models.TextChoices):
        NORMAL = ("normal", "Normal")
        HIGH = ("high", "Yüksek öncelik")
        CRITICAL = ("critical", "Kritik öncelik")

    class DurationUnits(models.TextChoices):
        DAY = ("day", "Gün")
        WEEK = ("week", "Hafta")
        MONTH = ("month", "Ay")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_support_requests",
    )
    assigned_volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_requests",
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=Categories.choices)
    course_name = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    description = models.TextField()
    urgency = models.CharField(
        max_length=16,
        choices=Urgencies.choices,
        default=Urgencies.MEDIUM,
    )
    priority = models.CharField(
        max_length=16,
        choices=Priorities.choices,
        default=Priorities.NORMAL,
    )
    duration_value = models.PositiveSmallIntegerField(null=True, blank=True)
    duration_unit = models.CharField(
        max_length=16,
        choices=DurationUnits.choices,
        blank=True,
    )
    requested_completion_date = models.DateField(null=True, blank=True)
    preferred_timing = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Statuses.choices,
        default=Statuses.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="supportreq_status_idx"),
            models.Index(fields=["priority"], name="supportreq_priority_idx"),
            models.Index(fields=["category"], name="supportreq_category_idx"),
            models.Index(
                fields=["created_by", "-created_at"],
                name="supportreq_createdby_date_idx",
            ),
            models.Index(
                fields=["assigned_volunteer", "status"],
                name="supportreq_vol_status_idx",
            ),
            models.Index(
                fields=["requested_completion_date"],
                name="supportreq_deadline_idx",
            ),
        ]

    CATEGORY_DESCRIPTIONS = {
        Categories.ACCESSIBLE_MATERIAL: (
            "El yazısı notların, PDF'lerin veya ders içeriklerinin erişilebilir hale getirilmesi için destek isteyebilirsiniz."
        ),
        Categories.AUDIO_NARRATION: (
            "Testlerin, denemelerin veya kısa akademik içeriklerin seslendirilmesi için talep oluşturabilirsiniz."
        ),
        Categories.VISUAL_DESCRIPTION: (
            "Grafik, tablo, görsel, şekil veya sunu içeriklerinin açıklayıcı biçimde betimlenmesini isteyebilirsiniz."
        ),
        Categories.JOINT_STUDY: (
            "Bir gönüllüyle birlikte ders çalışma, konu tekrarı yapma veya düzenli çalışma oturumu planlama desteği alabilirsiniz."
        ),
        Categories.ACADEMIC: (
            "Matematik, yabancı dil, istatistik, Osmanlı Türkçesi, müzik ve benzeri derslerde konu anlatımı veya akademik eşlik desteği isteyebilirsiniz."
        ),
        Categories.RESOURCE_ACCESS: (
            "Kütüphane, veri tabanı veya araştırma merkezlerinde ihtiyaç duyduğunuz kaynağa ulaşmak için rehberlik talep edebilirsiniz."
        ),
        Categories.EXAM_PREPARATION: (
            "Sınav öncesi test çözümü, deneme düzenleme, konu tekrar planı ve hazırlık desteği isteyebilirsiniz."
        ),
        Categories.WAYFINDING: (
            "Kampüs içinde veya kampüs dışında bağımsız hareket, yön bulma ya da belirli bir noktaya güvenli ulaşma konusunda destek talep edebilirsiniz."
        ),
        Categories.DAILY_LIFE: (
            "Günlük yaşamda kısa süreli bireysel destek veya kampüs içi ya da kampüs dışı pratik ihtiyaçlar için talep oluşturabilirsiniz."
        ),
        Categories.SOCIAL_ACTIVITY: (
            "Kulüp, etkinlik, söyleşi veya sosyal buluşmalara kampüs içinde ya da kampüs dışında katılım için eşlik ve rehberlik desteği isteyebilirsiniz."
        ),
    }

    def __str__(self):
        return self.title

    @classmethod
    def get_category_descriptions(cls):
        return cls.CATEGORY_DESCRIPTIONS.copy()

    @property
    def category_description(self):
        return self.CATEGORY_DESCRIPTIONS.get(self.category, "")

    def _local_created_date(self):
        return timezone.localtime(self.created_at).date()

    @staticmethod
    def _add_months(source_date, month_count):
        month_index = source_date.month - 1 + month_count
        year = source_date.year + month_index // 12
        month = month_index % 12 + 1
        day = min(source_date.day, monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    @property
    def calculated_deadline_date(self):
        if not self.duration_value or not self.duration_unit:
            return None

        created_date = self._local_created_date()
        if self.duration_unit == self.DurationUnits.DAY:
            return created_date + timedelta(days=self.duration_value)
        if self.duration_unit == self.DurationUnits.WEEK:
            return created_date + timedelta(weeks=self.duration_value)
        if self.duration_unit == self.DurationUnits.MONTH:
            return self._add_months(created_date, self.duration_value)
        return None

    @property
    def calculated_deadline_display(self):
        if not self.calculated_deadline_date:
            return ""
        return self.calculated_deadline_date.strftime("%d.%m.%Y")

    @property
    def requested_duration_display(self):
        if not self.duration_value or not self.duration_unit:
            return ""
        unit_label = self.get_duration_unit_display().lower()
        duration_text = f"{self.duration_value} {unit_label} içinde"
        if self.calculated_deadline_display:
            return f"{duration_text} ({self.calculated_deadline_display} tarihine kadar)"
        return duration_text

    @property
    def requested_date_display(self):
        if not self.requested_completion_date:
            return ""
        return self.requested_completion_date.strftime("%d.%m.%Y")

    @property
    def effective_deadline_date(self):
        return self.requested_completion_date or self.calculated_deadline_date

    @property
    def effective_deadline_display(self):
        if not self.effective_deadline_date:
            return ""
        return self.effective_deadline_date.strftime("%d.%m.%Y")

    @property
    def remaining_time_display(self):
        if not self.effective_deadline_date or self.status in {
            self.Statuses.COMPLETED,
            self.Statuses.CANCELLED,
        }:
            return ""

        remaining_days = (self.effective_deadline_date - timezone.localdate()).days
        if remaining_days < 0:
            return "Süre doldu"
        if remaining_days == 0:
            return "Bugün son gün"
        if remaining_days == 1:
            return "1 gün kaldı"
        return f"{remaining_days} gün kaldı"

    @property
    def timing_summary(self):
        parts = []
        if self.requested_duration_display:
            parts.append(self.requested_duration_display)
        if self.requested_date_display:
            parts.append(f"{self.requested_date_display} tarihine kadar")
        if self.remaining_time_display:
            parts.append(self.remaining_time_display)
        return " | ".join(parts)


class RequestMessage(models.Model):
    request = models.ForeignKey(
        SupportRequest,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="request_messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} - {self.request}"


class RequestMaterial(models.Model):
    class Statuses(models.TextChoices):
        DRAFT = ("draft", "Taslak")
        REVISION_REQUESTED = ("revision_requested", "Revizyon istendi")
        APPROVED = ("approved", "Onaylandı")

    request = models.ForeignKey(
        SupportRequest,
        on_delete=models.CASCADE,
        related_name="materials",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_request_materials",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=request_material_upload_to,
        max_length=255,
    )
    status = models.CharField(
        max_length=24,
        choices=Statuses.choices,
        default=Statuses.DRAFT,
    )
    version = models.PositiveSmallIntegerField(default=1)
    parent_material = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revisions",
    )
    revision_note = models.TextField(
        blank=True,
        help_text="Koordinatörün revizyon talebi veya onay notu.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (v{self.version})"


class SupportRequestInterventionNote(models.Model):
    class Priorities(models.TextChoices):
        NORMAL = ("normal", "Normal")
        HIGH = ("high", "Yüksek önem")
        CRITICAL = ("critical", "Kritik önem")

    request = models.ForeignKey(
        SupportRequest,
        on_delete=models.CASCADE,
        related_name="intervention_notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_intervention_notes",
    )
    priority = models.CharField(
        max_length=16,
        choices=Priorities.choices,
        default=Priorities.NORMAL,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} - {self.request}"


class SupportRequestActivityLog(models.Model):
    class ActionTypes(models.TextChoices):
        REQUEST_CREATED = ("request_created", "Talep oluşturuldu")
        STATUS_UPDATED = ("status_updated", "Durum güncellendi")
        PRIORITY_UPDATED = ("priority_updated", "Öncelik güncellendi")
        VOLUNTEER_ASSIGNED = ("volunteer_assigned", "Gönüllü atandı")
        INTERVENTION_NOTE = ("intervention_note", "Müdahale notu eklendi")
        MESSAGE_POSTED = ("message_posted", "Mesaj gönderildi")
        MATERIAL_UPLOADED = ("material_uploaded", "Materyal yüklendi")
        MATERIAL_REVISION_REQUESTED = (
            "material_revision_requested",
            "Materyal revizyonu istendi",
        )
        MATERIAL_APPROVED = ("material_approved", "Materyal onaylandı")
        MATERIAL_REVISED = ("material_revised", "Materyal revize edildi")

    request = models.ForeignKey(
        SupportRequest,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_activity_logs",
    )
    action_type = models.CharField(max_length=32, choices=ActionTypes.choices)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.request} - {self.get_action_type_display()}"
