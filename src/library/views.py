import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.views import View
from django.views.generic import DetailView, ListView

from users.mixins import RoleRequiredMixin
from users.models import User

from .models import LibraryItem

logger = logging.getLogger(__name__)

LIBRARY_ROLES = (
    User.Roles.VISUALLY_IMPAIRED_STUDENT,
    User.Roles.COORDINATOR,
)


class LibraryListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = LIBRARY_ROLES
    model = LibraryItem
    template_name = "library/library_list.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            LibraryItem.objects.filter(is_active=True)
            .select_related("material", "material__uploaded_by", "added_by")
        )
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        if query:
            qs = qs.filter(title__icontains=query) | qs.filter(tags__icontains=query)
        if category:
            qs = qs.filter(category__icontains=category)
        return qs.order_by("-added_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["categories"] = (
            LibraryItem.objects.filter(is_active=True)
            .exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        return context


class LibraryDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    allowed_roles = LIBRARY_ROLES
    model = LibraryItem
    template_name = "library/library_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return LibraryItem.objects.filter(is_active=True).select_related(
            "material",
            "material__uploaded_by",
            "material__request",
            "added_by",
        )


class LibraryDownloadView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = LIBRARY_ROLES

    def get(self, request, pk):
        item = LibraryItem.objects.filter(is_active=True).select_related("material").get(pk=pk) \
            if LibraryItem.objects.filter(is_active=True, pk=pk).exists() \
            else None
        if item is None:
            raise Http404("Kütüphane öğesi bulunamadı.")

        try:
            file_handle = item.material.file.open("rb")
        except (FileNotFoundError, OSError) as exc:
            logger.warning(
                "Kütüphane dosyası bulunamadı — LibraryItem pk=%s: %s",
                pk,
                exc,
            )
            raise Http404("Dosya bulunamadı veya erişilemiyor.")

        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=item.material.file.name.split("/")[-1],
        )
