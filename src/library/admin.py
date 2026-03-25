from django.contrib import admin

from .models import LibraryItem


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "added_by", "added_at")
    list_filter = ("is_active", "category")
    search_fields = ("title", "description", "tags")
    readonly_fields = ("added_at", "added_by", "material")
