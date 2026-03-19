from django.contrib import admin

from .models import RequestMaterial, RequestMessage, SupportRequest


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'status',
        'urgency',
        'created_by',
        'assigned_volunteer',
        'created_at',
    )
    list_filter = ('category', 'status', 'urgency')
    search_fields = ('title', 'course_name', 'topic', 'created_by__username')


@admin.register(RequestMessage)
class RequestMessageAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'created_at')
    search_fields = ('request__title', 'author__username', 'body')


@admin.register(RequestMaterial)
class RequestMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'request', 'uploaded_by', 'created_at')
    search_fields = ('title', 'request__title', 'uploaded_by__username')
