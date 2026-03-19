from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class AuraUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            'AURA profile',
            {
                'fields': (
                    'role',
                    'university',
                    'department',
                    'preferred_communication',
                    'accessibility_needs',
                    'support_topics',
                    'availability_notes',
                    'profile_completed',
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'AURA profile',
            {
                'fields': (
                    'email',
                    'role',
                    'first_name',
                    'last_name',
                )
            },
        ),
    )
    list_display = (
        'username',
        'email',
        'role',
        'profile_completed',
        'is_staff',
    )
    list_filter = ('role', 'profile_completed', 'is_staff', 'is_superuser')
