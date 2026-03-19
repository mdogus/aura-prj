from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousFileOperation
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from notifications.services import notify_staff, notify_users
from users.mixins import RoleRequiredMixin
from users.models import User

from .forms import (
    CoordinatorAssignmentForm,
    CoordinatorRequestPriorityForm,
    InterventionNoteForm,
    RequestMaterialForm,
    RequestMessageForm,
    StudentSupportRequestForm,
    StudentRequestMaterialForm,
    VolunteerRequestMaterialForm,
)
from .models import (
    RequestMaterial,
    SupportRequest,
    SupportRequestActivityLog,
    SupportRequestInterventionNote,
)


DEFAULT_DETAIL_SECTION = "overview"
STUDENT_DETAIL_SECTIONS = {"overview", "messages", "materials", "all"}
VOLUNTEER_DETAIL_SECTIONS = {"overview", "messages", "materials", "all"}
COORDINATOR_DETAIL_SECTIONS = {
    "overview",
    "management",
    "notes",
    "history",
    "messages",
    "materials",
    "all",
}


def filter_requests_by_deadline(request_items, deadline_filter):
    if not deadline_filter:
        return request_items

    today = timezone.localdate()
    if deadline_filter == "overdue":
        return [
            item
            for item in request_items
            if item.effective_deadline_date and item.effective_deadline_date < today
        ]
    if deadline_filter == "due_soon":
        return [
            item
            for item in request_items
            if item.effective_deadline_date
            and today <= item.effective_deadline_date <= today + timedelta(days=3)
        ]
    if deadline_filter == "dated":
        return [item for item in request_items if item.effective_deadline_date]
    return request_items


def get_active_section(request, allowed_sections, default=DEFAULT_DETAIL_SECTION):
    section = request.GET.get("section", default)
    return section if section in allowed_sections else default


def build_section_url(route_name, pk, section):
    base_url = reverse(route_name, args=[pk])
    if not section or section == DEFAULT_DETAIL_SECTION:
        return base_url
    return f"{base_url}?section={section}"


def log_request_activity(request_item, action_type, description, actor=None):
    SupportRequestActivityLog.objects.create(
        request=request_item,
        actor=actor,
        action_type=action_type,
        description=description,
    )


def user_can_access_request(user, request_item):
    if not user.is_authenticated:
        return False
    if user.role in {User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR}:
        return True
    if request_item.created_by_id == user.id:
        return True
    if request_item.assigned_volunteer_id == user.id:
        return True
    return False


def intervention_priority_order():
    return Case(
        When(
            priority=SupportRequestInterventionNote.Priorities.CRITICAL,
            then=Value(0),
        ),
        When(
            priority=SupportRequestInterventionNote.Priorities.HIGH,
            then=Value(1),
        ),
        default=Value(2),
        output_field=IntegerField(),
    )


class RequestMaterialDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        material = get_object_or_404(
            RequestMaterial.objects.select_related(
                "request",
                "request__created_by",
                "request__assigned_volunteer",
            ),
            pk=pk,
        )
        if not user_can_access_request(request.user, material.request):
            raise PermissionDenied

        file_handle = material.file.open("rb")
        return FileResponse(
            file_handle,
            as_attachment=False,
            filename=material.file.name.split("/")[-1],
        )


class RequestCommunicationContextMixin:
    def build_request_context(self, request_item, include_forms=False):
        messages_list = request_item.messages.select_related("author")
        materials_list = request_item.materials.select_related("uploaded_by")
        context = {
            "messages_list": messages_list,
            "materials_list": materials_list,
            "messages_count": messages_list.count(),
            "materials_count": materials_list.count(),
        }
        if include_forms:
            context["message_form"] = RequestMessageForm()
            context["material_form"] = RequestMaterialForm()
        return context

    def post_message(self, request, request_item):
        form = RequestMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.request = request_item
            message.author = request.user
            message.save()
            messages.success(request, "Mesajınız başarıyla gönderildi.")
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.MESSAGE_POSTED,
                f"{request.user} mesaj gönderdi.",
                actor=request.user,
            )
            return message
        messages.error(request, "Mesaj gönderilemedi.")
        return None

    def post_material(self, request, request_item):
        form = RequestMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.request = request_item
            material.uploaded_by = request.user
            material.save()
            messages.success(request, "Materyal başarıyla eklendi.")
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.MATERIAL_UPLOADED,
                f"{request.user} materyal yükledi: {material.title}.",
                actor=request.user,
            )
            return material
        messages.error(request, "Materyal yüklenemedi.")
        return None


class StudentRequestListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)
    model = SupportRequest
    context_object_name = "requests"
    template_name = "support/student_request_list.html"

    def get_queryset(self):
        return SupportRequest.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_list = list(context["requests"])
        closed_statuses = {
            SupportRequest.Statuses.COMPLETED,
            SupportRequest.Statuses.CANCELLED,
        }
        context["active_requests"] = [
            request_item
            for request_item in request_list
            if request_item.status not in closed_statuses
        ]
        context["closed_requests"] = [
            request_item
            for request_item in request_list
            if request_item.status in closed_statuses
        ]
        return context


class StudentRequestCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)
    form_class = StudentSupportRequestForm
    model = SupportRequest
    template_name = "support/request_form.html"
    success_url = reverse_lazy("support:student_request_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_request_activity(
            self.object,
            SupportRequestActivityLog.ActionTypes.REQUEST_CREATED,
            "Talep öğrenci tarafından oluşturuldu.",
            actor=self.request.user,
        )
        notify_staff(
            title="Yeni destek talebi oluşturuldu",
            body=f"{self.object.title} başlıklı yeni bir talep açıldı.",
            actor=self.request.user,
            support_request=self.object,
            exclude_ids={self.request.user.id},
        )
        messages.success(self.request, "Talebiniz başarıyla oluşturuldu.")
        return response


class StudentRequestDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)
    model = SupportRequest
    context_object_name = "request_item"
    template_name = "support/student_request_detail.html"

    def get_queryset(self):
        return SupportRequest.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_section"] = get_active_section(
            self.request,
            STUDENT_DETAIL_SECTIONS,
        )
        context["status_actions"] = [
            SupportRequest.Statuses.COMPLETED,
            SupportRequest.Statuses.CANCELLED,
        ]
        context.update(
            RequestCommunicationContextMixin().build_request_context(
                self.object,
                include_forms=True,
            )
        )
        context["material_form"] = StudentRequestMaterialForm()
        return context


class StudentRequestStatusUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            created_by=request.user,
        )
        next_status = request.POST.get("status")
        allowed_statuses = {
            SupportRequest.Statuses.COMPLETED,
            SupportRequest.Statuses.CANCELLED,
        }
        if next_status in allowed_statuses:
            request_item.status = next_status
            request_item.save(update_fields=["status", "updated_at"])
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.STATUS_UPDATED,
                f"Öğrenci durumu {request_item.get_status_display()} olarak güncelledi.",
                actor=request.user,
            )
            recipients = []
            if request_item.assigned_volunteer:
                recipients.append(request_item.assigned_volunteer)
            notify_users(
                recipients,
                title="Talep durumu güncellendi",
                body=f"{request_item.title} talebi {request_item.get_status_display()} olarak güncellendi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Talep durumu güncellendi",
                body=f"{request_item.title} talebinin durumu {request_item.get_status_display()} oldu.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            messages.success(request, "Talep durumu güncellendi.")
        else:
            messages.error(request, "Geçersiz durum güncelleme isteği.")
        return HttpResponseRedirect(
            build_section_url(
                "support:student_request_detail",
                request_item.pk,
                "overview",
            )
        )


class CoordinatorRequestListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)
    model = SupportRequest
    context_object_name = "requests"
    template_name = "support/coordinator_request_list.html"

    def get_queryset(self):
        queryset = SupportRequest.objects.annotate(
            priority_order=Case(
                When(priority=SupportRequest.Priorities.CRITICAL, then=Value(0)),
                When(priority=SupportRequest.Priorities.HIGH, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            intervention_note_count=Count("intervention_notes"),
        ).select_related(
            "created_by",
            "assigned_volunteer",
        ).order_by("priority_order", "-created_at")
        status = self.request.GET.get("status")
        urgency = self.request.GET.get("urgency")
        priority = self.request.GET.get("priority")
        category = self.request.GET.get("category")
        assigned = self.request.GET.get("assigned")
        deadline = self.request.GET.get("deadline")
        query = self.request.GET.get("q")
        if status:
            queryset = queryset.filter(status=status)
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        if priority:
            queryset = queryset.filter(priority=priority)
        if category:
            queryset = queryset.filter(category=category)
        if assigned == "assigned":
            queryset = queryset.filter(assigned_volunteer__isnull=False)
        elif assigned == "unassigned":
            queryset = queryset.filter(assigned_volunteer__isnull=True)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(course_name__icontains=query)
                | Q(topic__icontains=query)
                | Q(created_by__username__icontains=query)
                | Q(created_by__first_name__icontains=query)
                | Q(created_by__last_name__icontains=query)
            )
        request_items = list(queryset)
        return filter_requests_by_deadline(request_items, deadline)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_items = list(context["requests"])
        active_statuses = {
            SupportRequest.Statuses.OPEN,
            SupportRequest.Statuses.MATCHED,
            SupportRequest.Statuses.IN_PROGRESS,
        }
        today = timezone.localdate()
        context["result_count"] = len(request_items)
        context["active_result_count"] = sum(
            1 for item in request_items if item.status in active_statuses
        )
        context["closed_result_count"] = sum(
            1 for item in request_items if item.status not in active_statuses
        )
        context["unassigned_result_count"] = sum(
            1 for item in request_items if not item.assigned_volunteer
        )
        context["critical_result_count"] = sum(
            1
            for item in request_items
            if item.priority == SupportRequest.Priorities.CRITICAL
        )
        context["due_soon_result_count"] = sum(
            1
            for item in request_items
            if item.effective_deadline_date
            and today <= item.effective_deadline_date <= today + timedelta(days=3)
        )
        context["overdue_result_count"] = sum(
            1
            for item in request_items
            if item.effective_deadline_date and item.effective_deadline_date < today
        )
        context["status_choices"] = SupportRequest.Statuses.choices
        context["urgency_choices"] = SupportRequest.Urgencies.choices
        context["priority_choices"] = SupportRequest.Priorities.choices
        context["category_choices"] = SupportRequest.Categories.choices
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_urgency"] = self.request.GET.get("urgency", "")
        context["selected_priority"] = self.request.GET.get("priority", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_assigned"] = self.request.GET.get("assigned", "")
        context["selected_deadline"] = self.request.GET.get("deadline", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CoordinatorRequestDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)
    model = SupportRequest
    context_object_name = "request_item"
    template_name = "support/coordinator_request_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        priority_rank = intervention_priority_order()
        context["active_section"] = get_active_section(
            self.request,
            COORDINATOR_DETAIL_SECTIONS,
        )
        context["assignment_form"] = CoordinatorAssignmentForm()
        context["priority_form"] = CoordinatorRequestPriorityForm(
            initial={"priority": self.object.priority}
        )
        context["intervention_form"] = InterventionNoteForm()
        context["status_choices"] = SupportRequest.Statuses.choices
        context["activity_logs"] = self.object.activity_logs.select_related("actor")[:12]
        context["intervention_notes"] = (
            self.object.intervention_notes.select_related("author")
            .annotate(priority_rank=priority_rank)
            .order_by("priority_rank", "-created_at")[:8]
        )
        context["activity_logs_count"] = self.object.activity_logs.count()
        context["intervention_notes_count"] = self.object.intervention_notes.count()
        context.update(
            RequestCommunicationContextMixin().build_request_context(self.object)
        )
        return context


class VolunteerOpenRequestListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)
    model = SupportRequest
    context_object_name = "requests"
    template_name = "support/volunteer_open_request_list.html"

    def get_queryset(self):
        return SupportRequest.objects.filter(
            status=SupportRequest.Statuses.OPEN,
            assigned_volunteer__isnull=True,
        )


class VolunteerActiveSupportListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)
    model = SupportRequest
    context_object_name = "requests"
    template_name = "support/volunteer_active_support_list.html"

    def get_queryset(self):
        return SupportRequest.objects.filter(
            assigned_volunteer=self.request.user,
        ).exclude(status=SupportRequest.Statuses.CANCELLED)


class VolunteerRequestDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)
    model = SupportRequest
    context_object_name = "request_item"
    template_name = "support/volunteer_request_detail.html"

    def get_queryset(self):
        return SupportRequest.objects.filter(
            Q(status=SupportRequest.Statuses.OPEN, assigned_volunteer__isnull=True)
            | Q(assigned_volunteer=self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_section"] = get_active_section(
            self.request,
            VOLUNTEER_DETAIL_SECTIONS,
        )
        include_forms = self.object.assigned_volunteer == self.request.user
        context.update(
            RequestCommunicationContextMixin().build_request_context(
                self.object,
                include_forms=include_forms,
            )
        )
        if include_forms:
            context["material_form"] = VolunteerRequestMaterialForm()
        return context


class VolunteerClaimRequestView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            status=SupportRequest.Statuses.OPEN,
            assigned_volunteer__isnull=True,
        )
        request_item.assigned_volunteer = request.user
        request_item.status = SupportRequest.Statuses.MATCHED
        request_item.save(update_fields=["assigned_volunteer", "status", "updated_at"])
        log_request_activity(
            request_item,
            SupportRequestActivityLog.ActionTypes.VOLUNTEER_ASSIGNED,
            f"Gönüllü atandı: {request.user}.",
            actor=request.user,
        )
        notify_users(
            [request_item.created_by],
            title="Bir gönüllü talebi üstlendi",
            body=f"{request_item.title} talebiniz bir gönüllü tarafından üstlenildi.",
            actor=request.user,
            support_request=request_item,
            exclude_ids={request.user.id},
        )
        notify_staff(
            title="Talep eşleşti",
            body=f"{request_item.title} talebi gönüllü ile eşleşti.",
            actor=request.user,
            support_request=request_item,
            exclude_ids={request.user.id},
        )
        messages.success(request, "Talep sizinle eşleştirildi.")
        return HttpResponseRedirect(
            reverse("support:volunteer_request_detail", args=[request_item.pk])
        )


class VolunteerRequestStatusUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            assigned_volunteer=request.user,
        )
        next_status = request.POST.get("status")
        allowed_statuses = {
            SupportRequest.Statuses.IN_PROGRESS,
            SupportRequest.Statuses.COMPLETED,
        }
        if next_status in allowed_statuses:
            request_item.status = next_status
            request_item.save(update_fields=["status", "updated_at"])
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.STATUS_UPDATED,
                f"Gönüllü durumu {request_item.get_status_display()} olarak güncelledi.",
                actor=request.user,
            )
            notify_users(
                [request_item.created_by],
                title="Gönüllü destek durumunu güncelledi",
                body=f"{request_item.title} talebi {request_item.get_status_display()} durumuna geçti.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Destek durumu güncellendi",
                body=f"{request_item.title} talebi gönüllü tarafından {request_item.get_status_display()} durumuna geçti.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            messages.success(request, "Destek durumu güncellendi.")
        else:
            messages.error(request, "Geçersiz durum güncelleme isteği.")
        return HttpResponseRedirect(
            reverse("support:volunteer_request_detail", args=[request_item.pk])
        )


class CoordinatorAssignVolunteerView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)

    def post(self, request, pk):
        request_item = get_object_or_404(SupportRequest, pk=pk)
        form = CoordinatorAssignmentForm(request.POST)
        if form.is_valid():
            request_item.assigned_volunteer = form.cleaned_data["volunteer"]
            if request_item.status == SupportRequest.Statuses.OPEN:
                request_item.status = SupportRequest.Statuses.MATCHED
            request_item.save(
                update_fields=["assigned_volunteer", "status", "updated_at"]
            )
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.VOLUNTEER_ASSIGNED,
                f"Koordinasyon tarafından gönüllü atandı: {request_item.assigned_volunteer}.",
                actor=request.user,
            )
            notify_users(
                [request_item.created_by, request_item.assigned_volunteer],
                title="Gönüllü ataması yapıldı",
                body=f"{request_item.title} talebi için gönüllü ataması yapıldı.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Gönüllü ataması güncellendi",
                body=f"{request_item.title} talebi için gönüllü ataması kaydedildi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            messages.success(request, "Gönüllü ataması kaydedildi.")
        else:
            messages.error(request, "Geçerli bir gönüllü seçilemedi.")
        return HttpResponseRedirect(
            build_section_url(
                "support:coordinator_request_detail",
                request_item.pk,
                "management",
            )
        )


class CoordinatorRequestStatusUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)

    def post(self, request, pk):
        request_item = get_object_or_404(SupportRequest, pk=pk)
        next_status = request.POST.get("status")
        valid_statuses = {choice[0] for choice in SupportRequest.Statuses.choices}
        if next_status in valid_statuses:
            request_item.status = next_status
            request_item.save(update_fields=["status", "updated_at"])
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.STATUS_UPDATED,
                f"Koordinasyon durumu {request_item.get_status_display()} olarak güncelledi.",
                actor=request.user,
            )
            recipients = [request_item.created_by]
            if request_item.assigned_volunteer:
                recipients.append(request_item.assigned_volunteer)
            notify_users(
                recipients,
                title="Koordinatör talep durumunu güncelledi",
                body=f"{request_item.title} talebi {request_item.get_status_display()} olarak güncellendi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            messages.success(request, "Talep durumu güncellendi.")
        else:
            messages.error(request, "Geçersiz durum seçimi.")
        return HttpResponseRedirect(
            build_section_url(
                "support:coordinator_request_detail",
                request_item.pk,
                "management",
            )
        )


class CoordinatorRequestPriorityUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)

    def post(self, request, pk):
        request_item = get_object_or_404(SupportRequest, pk=pk)
        form = CoordinatorRequestPriorityForm(request.POST)
        if form.is_valid():
            request_item.priority = form.cleaned_data["priority"]
            request_item.save(update_fields=["priority", "updated_at"])
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.PRIORITY_UPDATED,
                f"Koordinasyon önceliği {request_item.get_priority_display()} olarak güncelledi.",
                actor=request.user,
            )
            messages.success(request, "Talep önceliği güncellendi.")
        else:
            messages.error(request, "Talep önceliği güncellenemedi.")
        return HttpResponseRedirect(
            build_section_url(
                "support:coordinator_request_detail",
                request_item.pk,
                "management",
            )
        )


class CoordinatorInterventionNoteCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR)

    def post(self, request, pk):
        request_item = get_object_or_404(SupportRequest, pk=pk)
        form = InterventionNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.request = request_item
            note.author = request.user
            note.save()
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.INTERVENTION_NOTE,
                "Koordinasyon müdahale notu eklendi.",
                actor=request.user,
            )
            messages.success(request, "Müdahale notu kaydedildi.")
        else:
            messages.error(request, "Müdahale notu eklenemedi.")
        return HttpResponseRedirect(
            build_section_url(
                "support:coordinator_request_detail",
                request_item.pk,
                "notes",
            )
        )


class StudentRequestMessageCreateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    RequestCommunicationContextMixin,
    View,
):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            created_by=request.user,
        )
        message = self.post_message(request, request_item)
        if message:
            recipients = []
            if request_item.assigned_volunteer:
                recipients.append(request_item.assigned_volunteer)
            notify_users(
                recipients,
                title="Yeni talep mesajı",
                body=f"{request_item.title} talebi için yeni bir mesaj var.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Talep mesajı eklendi",
                body=f"{request_item.title} talebi için yeni bir mesaj gönderildi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
        return HttpResponseRedirect(
            build_section_url(
                "support:student_request_detail",
                request_item.pk,
                "messages",
            )
        )


class StudentRequestMaterialCreateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    RequestCommunicationContextMixin,
    View,
):
    allowed_roles = (User.Roles.VISUALLY_IMPAIRED_STUDENT,)

    def render_invalid_form(self, request, request_item, form):
        context = self.build_request_context(
            request_item,
            include_forms=True,
        )
        context.update(
            {
                "request_item": request_item,
                "object": request_item,
                "status_actions": [
                    SupportRequest.Statuses.COMPLETED,
                    SupportRequest.Statuses.CANCELLED,
                ],
                "active_section": "materials",
                "material_form": form,
            }
        )
        return render(
            request,
            "support/student_request_detail.html",
            context,
            status=200,
        )

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            created_by=request.user,
        )
        form = StudentRequestMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                material = form.save(commit=False)
                material.request = request_item
                material.uploaded_by = request.user
                material.save()
            except SuspiciousFileOperation:
                form.add_error(
                    "file",
                    "Dosya adı çok uzun olduğu için yüklenemedi. Daha kısa bir adla tekrar deneyin.",
                )
                messages.error(
                    request,
                    "Dosya eklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
                )
                return self.render_invalid_form(request, request_item, form)
            messages.success(request, "Dosya başarıyla eklendi.")
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.MATERIAL_UPLOADED,
                f"{request.user} kaynak dosya ekledi: {material.title}.",
                actor=request.user,
            )
        else:
            messages.error(
                request,
                "Dosya eklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
            )
            return self.render_invalid_form(request, request_item, form)
        if material:
            recipients = []
            if request_item.assigned_volunteer:
                recipients.append(request_item.assigned_volunteer)
            notify_users(
                recipients,
                title="Yeni kaynak dosya eklendi",
                body=f"{request_item.title} talebine öğrenciden yeni bir kaynak dosya eklendi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Talebe kaynak dosya eklendi",
                body=f"{request_item.title} talebi için öğrenci yeni bir kaynak dosya yükledi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
        return HttpResponseRedirect(
            build_section_url(
                "support:student_request_detail",
                request_item.pk,
                "materials",
            )
        )


class VolunteerRequestMessageCreateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    RequestCommunicationContextMixin,
    View,
):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            assigned_volunteer=request.user,
        )
        message = self.post_message(request, request_item)
        if message:
            notify_users(
                [request_item.created_by],
                title="Yeni talep mesajı",
                body=f"{request_item.title} talebi için gönüllüden yeni mesaj geldi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Gönüllü mesaj gönderdi",
                body=f"{request_item.title} talebi için gönüllü yeni bir mesaj gönderdi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
        return HttpResponseRedirect(
            build_section_url(
                "support:volunteer_request_detail",
                request_item.pk,
                "messages",
            )
        )


class VolunteerRequestMaterialCreateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    RequestCommunicationContextMixin,
    View,
):
    allowed_roles = (User.Roles.VOLUNTEER_STUDENT,)

    def render_invalid_form(self, request, request_item, form):
        context = self.build_request_context(
            request_item,
            include_forms=True,
        )
        context.update(
            {
                "request_item": request_item,
                "object": request_item,
                "active_section": "materials",
                "material_form": form,
            }
        )
        return render(
            request,
            "support/volunteer_request_detail.html",
            context,
            status=200,
        )

    def post(self, request, pk):
        request_item = get_object_or_404(
            SupportRequest,
            pk=pk,
            assigned_volunteer=request.user,
        )
        form = VolunteerRequestMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                material = form.save(commit=False)
                material.request = request_item
                material.uploaded_by = request.user
                material.save()
            except SuspiciousFileOperation:
                form.add_error(
                    "file",
                    "Dosya adı çok uzun olduğu için yüklenemedi. Daha kısa bir adla tekrar deneyin.",
                )
                messages.error(
                    request,
                    "Materyal yüklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
                )
                return self.render_invalid_form(request, request_item, form)
            messages.success(request, "Materyal başarıyla eklendi.")
            log_request_activity(
                request_item,
                SupportRequestActivityLog.ActionTypes.MATERIAL_UPLOADED,
                f"{request.user} materyal yükledi: {material.title}.",
                actor=request.user,
            )
        else:
            messages.error(
                request,
                "Materyal yüklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
            )
            return self.render_invalid_form(request, request_item, form)
        if material:
            notify_users(
                [request_item.created_by],
                title="Yeni materyal yüklendi",
                body=f"{request_item.title} talebine gönüllü tarafından yeni materyal eklendi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
            notify_staff(
                title="Gönüllü materyal ekledi",
                body=f"{request_item.title} talebi için gönüllü yeni materyal yükledi.",
                actor=request.user,
                support_request=request_item,
                exclude_ids={request.user.id},
            )
        return HttpResponseRedirect(
            build_section_url(
                "support:volunteer_request_detail",
                request_item.pk,
                "materials",
            )
        )
