from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        VISUALLY_IMPAIRED_STUDENT = (
            "visually_impaired_student",
            "Görme engelli öğrenci",
        )
        VOLUNTEER_STUDENT = ("volunteer_student", "Gönüllü öğrenci")
        ACADEMIC_ADVISOR = ("academic_advisor", "Akademik danışman")
        COORDINATOR = ("coordinator", "Koordinatör")

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=Roles.choices)
    university = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    preferred_communication = models.CharField(max_length=255, blank=True)
    accessibility_needs = models.TextField(blank=True)
    support_topics = models.TextField(blank=True)
    availability_notes = models.TextField(blank=True)
    profile_completed = models.BooleanField(default=False)

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name or self.username


class UserManagementAction(models.Model):
    class ActionTypes(models.TextChoices):
        DEACTIVATED = ("deactivated", "Kullanıcı pasife alındı")
        REACTIVATED = ("reactivated", "Kullanıcı yeniden aktive edildi")

    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="management_actions",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_management_actions",
    )
    action_type = models.CharField(max_length=24, choices=ActionTypes.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.target_user} - {self.get_action_type_display()}"
