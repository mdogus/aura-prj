from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from notifications.models import Notification
from notifications.services import create_notification
from support.models import SupportRequest

from .forms import ProfileOnboardingForm, SignUpForm, UserStatusActionForm
from .mixins import ActiveUserRequiredMixin, RoleRequiredMixin
from .models import User, UserManagementAction


class SignUpView(CreateView):
    form_class = SignUpForm
    model = User
    template_name = "users/signup.html"
    success_url = reverse_lazy("dashboard:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileOnboardingView(LoginRequiredMixin, ActiveUserRequiredMixin, UpdateView):
    form_class = ProfileOnboardingForm
    model = User
    template_name = "users/profile_onboarding.html"
    success_url = reverse_lazy("dashboard:home")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.instance.profile_completed = True
        return super().form_valid(form)


class CoordinatorUserListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.COORDINATOR,)
    model = User
    context_object_name = "users"
    template_name = "users/coordinator_user_list.html"

    def get_queryset(self):
        queryset = User.objects.all().order_by("role", "username")
        role = self.request.GET.get("role")
        active = self.request.GET.get("active")
        profile = self.request.GET.get("profile")
        query = self.request.GET.get("q")
        if role:
            queryset = queryset.filter(role=role)
        if active == "active":
            queryset = queryset.filter(is_active=True)
        elif active == "inactive":
            queryset = queryset.filter(is_active=False)
        if profile == "completed":
            queryset = queryset.filter(profile_completed=True)
        elif profile == "incomplete":
            queryset = queryset.filter(profile_completed=False)
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_items = list(context["users"])
        context["role_choices"] = User.Roles.choices
        context["selected_role"] = self.request.GET.get("role", "")
        context["selected_active"] = self.request.GET.get("active", "")
        context["selected_profile"] = self.request.GET.get("profile", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["result_count"] = len(user_items)
        context["active_result_count"] = sum(
            1 for item in user_items if item.is_active
        )
        context["inactive_result_count"] = sum(
            1 for item in user_items if not item.is_active
        )
        context["incomplete_profile_count"] = sum(
            1 for item in user_items if not item.profile_completed
        )
        context["volunteer_result_count"] = sum(
            1 for item in user_items if item.role == User.Roles.VOLUNTEER_STUDENT
        )
        return context


class CoordinatorUserDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    allowed_roles = (User.Roles.COORDINATOR,)
    model = User
    context_object_name = "managed_user"
    template_name = "users/coordinator_user_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_form"] = UserStatusActionForm()
        context["management_actions"] = self.object.management_actions.select_related(
            "actor"
        )[:10]
        managed_user = self.object
        created_requests = managed_user.created_support_requests.all()
        assigned_requests = managed_user.assigned_support_requests.all()
        context["user_request_summary"] = {
            "created_count": created_requests.count(),
            "assigned_count": assigned_requests.count(),
            "completed_assigned_count": assigned_requests.filter(
                status=SupportRequest.Statuses.COMPLETED
            ).count(),
            "active_assigned_count": assigned_requests.exclude(
                status__in=[
                    SupportRequest.Statuses.COMPLETED,
                    SupportRequest.Statuses.CANCELLED,
                ]
            ).count(),
            "unread_notification_count": Notification.objects.filter(
                recipient=managed_user,
                is_read=False,
            ).count(),
        }
        return context


class CoordinatorUserToggleActiveView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (User.Roles.COORDINATOR,)

    def post(self, request, pk):
        managed_user = User.objects.get(pk=pk)
        require_note = managed_user.is_active
        form = UserStatusActionForm(request.POST, require_note=require_note)
        if managed_user == request.user or managed_user.is_superuser:
            messages.error(request, "Bu kullanıcı için aktiflik durumu değiştirilemez.")
        elif not form.is_valid():
            messages.error(request, form.errors.get("note", ["İşlem notu geçersiz."])[0])
        else:
            note = form.cleaned_data["note"]
            was_active = managed_user.is_active
            managed_user.is_active = not managed_user.is_active
            managed_user.save(update_fields=["is_active"])
            action_type = (
                UserManagementAction.ActionTypes.DEACTIVATED
                if was_active
                else UserManagementAction.ActionTypes.REACTIVATED
            )
            UserManagementAction.objects.create(
                target_user=managed_user,
                actor=request.user,
                action_type=action_type,
                note=note,
            )
            create_notification(
                managed_user,
                title="Hesap durumu güncellendi",
                body=(
                    "Hesabınız pasife alındı."
                    if was_active
                    else "Hesabınız yeniden aktive edildi."
                ),
                actor=request.user,
            )
            messages.success(request, "Kullanıcı aktiflik durumu güncellendi.")
        return redirect("users:coordinator_user_detail", pk=managed_user.pk)
