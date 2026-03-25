from django.conf import settings
from django.db import models

from support.models import RequestMaterial


class LibraryItem(models.Model):
    """
    Koordinatör onayı verilen erişilebilir materyallerin kütüphane kaydı.
    Her onaylı materyal için en fazla bir LibraryItem oluşturulabilir.
    """

    material = models.OneToOneField(
        RequestMaterial,
        on_delete=models.CASCADE,
        related_name="library_item",
        verbose_name="Materyal",
    )
    title = models.CharField(max_length=255, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    category = models.CharField(max_length=64, blank=True, verbose_name="Kategori")
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Virgülle ayrılmış etiketler.",
        verbose_name="Etiketler",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="added_library_items",
        verbose_name="Ekleyen",
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Eklenme tarihi")

    class Meta:
        ordering = ["-added_at"]
        verbose_name = "Kütüphane öğesi"
        verbose_name_plural = "Kütüphane öğeleri"

    def __str__(self):
        return self.title
