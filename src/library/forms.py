from django import forms

from support.forms import apply_common_field_attrs

from .models import LibraryItem


class LibraryItemForm(forms.ModelForm):
    """Koordinatörün kütüphaneye materyal eklerken doldurduğu form."""

    class Meta:
        model = LibraryItem
        fields = ("title", "description", "category", "tags")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "title": "Kütüphane başlığı",
            "description": "Materyalin kısa açıklaması",
            "category": "Örn: Matematik, Türkçe, Fizik…",
            "tags": "Örn: üniversite, görme engelli, braille",
        }
        for name, field in self.fields.items():
            apply_common_field_attrs(field, name, placeholder=placeholders.get(name))
