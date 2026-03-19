from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from notifications.models import Notification
from support.models import (
    SupportRequest,
    SupportRequestActivityLog,
    SupportRequestInterventionNote,
)
from users.mixins import ActiveUserRequiredMixin, RoleRequiredMixin
from users.models import User, UserManagementAction


VOLUNTEER_CATEGORY_SCORE = {
    SupportRequest.Categories.ACCESSIBLE_MATERIAL: 6,
    SupportRequest.Categories.EXAM_PREPARATION: 6,
    SupportRequest.Categories.RESOURCE_ACCESS: 5,
    SupportRequest.Categories.ACADEMIC: 5,
    SupportRequest.Categories.JOINT_STUDY: 5,
    SupportRequest.Categories.AUDIO_NARRATION: 4,
    SupportRequest.Categories.VISUAL_DESCRIPTION: 4,
    SupportRequest.Categories.WAYFINDING: 4,
    SupportRequest.Categories.DAILY_LIFE: 3,
    SupportRequest.Categories.SOCIAL_ACTIVITY: 3,
}

VOLUNTEER_STREAK_BONUS = 4
VOLUNTEER_RECENT_ACTIVITY_BONUS = 2

VOLUNTEER_LEVELS = [
    {
        "label": "İstekli",
        "threshold": 0,
        "icon": "icon-gentle",
        "description": "İlk desteğini üstlenmeye hazır gönüllü seviyesi.",
    },
    {
        "label": "Aktif Ortak",
        "threshold": 20,
        "icon": "icon-user",
        "description": "Düzenli katkı veren ve aktif destek üstlenen gönüllü seviyesi.",
    },
    {
        "label": "Yol Arkadaşı",
        "threshold": 60,
        "icon": "icon-compass",
        "description": "Birden fazla alanda güven veren ve süreklilik sağlayan gönüllü seviyesi.",
    },
    {
        "label": "AURA Elçisi",
        "threshold": 120,
        "icon": "icon-flag",
        "description": "Yüksek katkı sunan ve topluluğa örnek olan gönüllü seviyesi.",
    },
]


def get_volunteer_level(score):
    current_level = VOLUNTEER_LEVELS[0]
    for level in VOLUNTEER_LEVELS:
        if score >= level["threshold"]:
            current_level = level
        else:
            break
    return current_level


def get_next_volunteer_level(score):
    for level in VOLUNTEER_LEVELS:
        if score < level["threshold"]:
            return {
                "label": level["label"],
                "threshold": level["threshold"],
                "icon": level["icon"],
                "description": level["description"],
                "remaining": level["threshold"] - score,
            }
    return None


def get_volunteer_level_roadmap(score):
    current_level = get_volunteer_level(score)
    next_level = get_next_volunteer_level(score)
    roadmap = []
    for level in VOLUNTEER_LEVELS:
        roadmap.append(
            {
                **level,
                "is_current": level["label"] == current_level["label"],
                "is_reached": score >= level["threshold"],
                "is_next": bool(next_level and level["label"] == next_level["label"]),
            }
        )
    return roadmap


def get_weekly_completion_streak(completed_supports):
    completed_weeks = {
        timezone.localtime(item.updated_at).date().isocalendar()[:2]
        for item in completed_supports
    }
    current_week = timezone.localdate().isocalendar()[:2]
    if current_week not in completed_weeks:
        return 0

    streak = 0
    year, week = current_week
    while (year, week) in completed_weeks:
        streak += 1
        week -= 1
        if week == 0:
            year -= 1
            week = date(year, 12, 28).isocalendar().week
    return streak


def get_volunteer_goal(active_support_count, completed_support_count, open_request_count):
    if active_support_count > 0:
        return {
            "title": "Bu hafta hedefin",
            "body": "Aktif desteğini tamamlayarak ek puan kazanabilir ve seviyeni daha hızlı yükseltebilirsin.",
        }
    if open_request_count > 0:
        return {
            "title": "Bu hafta hedefin",
            "body": "Açık talepler arasından yeni bir destek üstlenerek puan yolculuğunu hızlandırabilirsin.",
        }
    if completed_support_count > 0:
        return {
            "title": "Harika ilerliyorsun",
            "body": "Yeni talepler açıldığında hızlıca destek vererek serini sürdürebilirsin.",
        }
    return {
        "title": "Başlamak için iyi bir zaman",
        "body": "İlk desteğini üstlendiğinde puanın, seviyen ve katkı yolun görünür hale gelecek.",
    }


def get_volunteer_motivation_message(score, weekly_streak):
    if weekly_streak >= 3:
        return "Sürekliliğin çok güçlü. Bu ritmi koruyarak AURA Elçisi seviyesine yaklaşabilirsin."
    if score >= 60:
        return "İstikrarlı katkın görünür hale geldi. Birkaç güçlü destek daha seni üst seviyeye taşıyabilir."
    if score >= 20:
        return "Düzenli katkı vermeye başladın. Haftalık serini koruman büyük fark yaratır."
    return "İlk katkıların görünür olmaya başladı. Küçük ama düzenli destekler hızla seviye kazandırır."


def split_requests_by_timing(requests, limit=5, window_days=3):
    today = timezone.localdate()
    overdue_requests = []
    due_soon_requests = []

    for request_item in requests:
        deadline = request_item.effective_deadline_date
        if not deadline:
            continue
        if deadline < today:
            overdue_requests.append(request_item)
        elif deadline <= today + timedelta(days=window_days):
            due_soon_requests.append(request_item)

    overdue_requests.sort(key=lambda item: item.effective_deadline_date)
    due_soon_requests.sort(key=lambda item: item.effective_deadline_date)
    return overdue_requests[:limit], due_soon_requests[:limit]


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


class DashboardHomeRedirectView(LoginRequiredMixin, ActiveUserRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard_redirect.html'

    def get(self, request, *args, **kwargs):
        if not request.user.profile_completed:
            return redirect('users:profile_onboarding')
        if request.user.role == request.user.Roles.VISUALLY_IMPAIRED_STUDENT:
            return redirect('dashboard:student')
        if request.user.role == request.user.Roles.VOLUNTEER_STUDENT:
            return redirect('dashboard:volunteer')
        if request.user.role == request.user.Roles.ACADEMIC_ADVISOR:
            return redirect('dashboard:advisor')
        return redirect('dashboard:coordinator')


class StudentDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ('visually_impaired_student',)
    template_name = 'dashboard/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requests = SupportRequest.objects.filter(created_by=self.request.user)
        context['request_count'] = requests.count()
        context['open_request_count'] = requests.exclude(
            status__in=[
                SupportRequest.Statuses.COMPLETED,
                SupportRequest.Statuses.CANCELLED,
            ]
        ).count()
        context['recent_requests'] = requests.order_by('-created_at')[:3]
        context['recent_notifications'] = Notification.objects.filter(
            recipient=self.request.user
        )[:5]
        return context


class VolunteerDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ('volunteer_student',)
    template_name = 'dashboard/volunteer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        open_requests = SupportRequest.objects.filter(
            status=SupportRequest.Statuses.OPEN,
            assigned_volunteer__isnull=True,
        )
        volunteer_supports = SupportRequest.objects.filter(
            assigned_volunteer=self.request.user,
        ).exclude(status=SupportRequest.Statuses.CANCELLED)
        active_supports = volunteer_supports.exclude(
            status=SupportRequest.Statuses.COMPLETED,
        )
        completed_supports = volunteer_supports.filter(
            status=SupportRequest.Statuses.COMPLETED,
        )
        latest_completed_support = completed_supports.order_by('-updated_at').first()
        thirty_days_ago = timezone.localdate() - timedelta(days=29)
        recent_30_day_support_count = volunteer_supports.filter(
            updated_at__date__gte=thirty_days_ago
        ).count()
        weekly_streak = get_weekly_completion_streak(completed_supports)
        support_items = list(volunteer_supports.order_by('-updated_at'))
        category_labels = dict(SupportRequest.Categories.choices)
        category_counts = {}
        volunteer_score = 0
        for support_item in support_items:
            category_counts[support_item.category] = (
                category_counts.get(support_item.category, 0) + 1
            )
            volunteer_score += 10
            volunteer_score += VOLUNTEER_CATEGORY_SCORE.get(support_item.category, 3)
            if support_item.status == SupportRequest.Statuses.COMPLETED:
                volunteer_score += 15

        streak_score_bonus = weekly_streak * VOLUNTEER_STREAK_BONUS
        recent_activity_score_bonus = (
            recent_30_day_support_count * VOLUNTEER_RECENT_ACTIVITY_BONUS
        )
        volunteer_score += streak_score_bonus + recent_activity_score_bonus

        top_supported_categories = sorted(
            [
                {
                    "value": category_value,
                    "label": category_labels.get(category_value, category_value),
                    "count": count,
                }
                for category_value, count in category_counts.items()
            ],
            key=lambda item: (-item["count"], item["label"]),
        )[:3]
        context['open_request_count'] = open_requests.count()
        context['active_support_count'] = active_supports.count()
        context['completed_support_count'] = completed_supports.count()
        context['total_supported_count'] = volunteer_supports.count()
        context['supported_category_count'] = len(category_counts)
        context['volunteer_score'] = volunteer_score
        context['volunteer_level'] = get_volunteer_level(volunteer_score)
        context['next_volunteer_level'] = get_next_volunteer_level(volunteer_score)
        context['volunteer_level_roadmap'] = get_volunteer_level_roadmap(
            volunteer_score
        )
        context['top_supported_categories'] = top_supported_categories
        context['latest_completed_support'] = latest_completed_support
        context['recent_30_day_support_count'] = recent_30_day_support_count
        context['weekly_streak'] = weekly_streak
        context['streak_score_bonus'] = streak_score_bonus
        context['recent_activity_score_bonus'] = recent_activity_score_bonus
        context['volunteer_score_rules'] = [
            "Her üstlenilen destek için +10 puan",
            "Tamamlanan her destek için ek +15 puan",
            "Destek türüne göre ek katkı puanı",
            f"Her haftalık seri adımı için +{VOLUNTEER_STREAK_BONUS} puan",
            f"Son 30 gündeki her katkı için +{VOLUNTEER_RECENT_ACTIVITY_BONUS} puan",
        ]
        context['volunteer_goal'] = get_volunteer_goal(
            active_supports.count(),
            completed_supports.count(),
            open_requests.count(),
        )
        context['volunteer_motivation_message'] = get_volunteer_motivation_message(
            volunteer_score,
            weekly_streak,
        )
        context['recent_open_requests'] = open_requests[:3]
        context['recent_notifications'] = Notification.objects.filter(
            recipient=self.request.user
        )[:5]
        return context


class AdvisorDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.ACADEMIC_ADVISOR,)
    template_name = 'dashboard/advisor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requests = SupportRequest.objects.all()
        context['total_request_count'] = requests.count()
        context['academic_request_count'] = requests.filter(
            category__in=[
                SupportRequest.Categories.ACADEMIC,
                SupportRequest.Categories.ACCESSIBLE_MATERIAL,
                SupportRequest.Categories.JOINT_STUDY,
            ]
        ).count()
        context['recent_requests'] = requests.order_by('-created_at')[:5]
        context['recent_notifications'] = Notification.objects.filter(
            recipient=self.request.user
        )[:5]
        return context


class CoordinatorDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.COORDINATOR,)
    template_name = 'dashboard/coordinator_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        note_priority_rank = intervention_priority_order()
        requests = SupportRequest.objects.all()
        active_requests = requests.exclude(
            status__in=[
                SupportRequest.Statuses.COMPLETED,
                SupportRequest.Statuses.CANCELLED,
            ]
        )
        active_requests = active_requests.select_related(
            'created_by',
            'assigned_volunteer',
        )
        priority_order = Case(
            When(priority=SupportRequest.Priorities.CRITICAL, then=Value(0)),
            When(priority=SupportRequest.Priorities.HIGH, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
        critical_requests = (
            active_requests.filter(priority=SupportRequest.Priorities.CRITICAL)
            .select_related('created_by', 'assigned_volunteer')
            .annotate(priority_rank=priority_order)
            .order_by('priority_rank', '-updated_at')[:5]
        )
        attention_requests = (
            active_requests.filter(
                Q(priority=SupportRequest.Priorities.CRITICAL)
                | Q(assigned_volunteer__isnull=True)
            )
            .annotate(priority_rank=priority_order)
            .order_by('priority_rank', '-updated_at')
            .distinct()[:5]
        )
        active_request_items = list(
            active_requests.annotate(priority_rank=priority_order).order_by(
                'priority_rank',
                '-updated_at',
            )
        )
        overdue_requests, due_soon_requests = split_requests_by_timing(
            active_request_items
        )
        notifications = Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')
        context['total_request_count'] = requests.count()
        context['unmatched_request_count'] = active_requests.filter(
            assigned_volunteer__isnull=True
        ).count()
        context['critical_request_count'] = active_requests.filter(
            priority=SupportRequest.Priorities.CRITICAL
        ).count()
        context['unassigned_critical_count'] = active_requests.filter(
            priority=SupportRequest.Priorities.CRITICAL,
            assigned_volunteer__isnull=True,
        ).count()
        context['overdue_request_count'] = len(overdue_requests)
        context['due_soon_request_count'] = len(due_soon_requests)
        context['inactive_user_count'] = User.objects.filter(is_active=False).count()
        context['incomplete_profile_count'] = User.objects.filter(
            profile_completed=False
        ).count()
        context['intervention_note_count'] = SupportRequestInterventionNote.objects.count()
        context['critical_requests'] = critical_requests
        context['attention_requests'] = attention_requests
        context['overdue_requests'] = overdue_requests
        context['due_soon_requests'] = due_soon_requests
        context['recent_request_activities'] = (
            SupportRequestActivityLog.objects.select_related('actor', 'request')
            .order_by('-created_at')[:5]
        )
        context['recent_intervention_notes'] = (
            SupportRequestInterventionNote.objects.select_related('author', 'request')
            .annotate(priority_rank=note_priority_rank)
            .order_by('priority_rank', '-created_at')[:5]
        )
        context['recent_user_management_actions'] = (
            UserManagementAction.objects.select_related('actor', 'target_user')
            .order_by('-created_at')[:5]
        )
        context['recent_notifications'] = notifications[:5]
        context['unread_notification_count'] = notifications.filter(is_read=False).count()
        context['active_user_count'] = User.objects.filter(is_active=True).count()
        context['request_filter_links'] = [
            {
                "label": "Atanmamış aktifler",
                "url": f"{reverse('support:coordinator_request_list')}?assigned=unassigned",
            },
            {
                "label": "Kritik öncelikliler",
                "url": f"{reverse('support:coordinator_request_list')}?priority=critical",
            },
            {
                "label": "Süresi yaklaşanlar",
                "url": f"{reverse('support:coordinator_request_list')}?deadline=due_soon",
            },
            {
                "label": "Süresi geçenler",
                "url": f"{reverse('support:coordinator_request_list')}?deadline=overdue",
            },
        ]
        context['user_filter_links'] = [
            {
                "label": "Pasif kullanıcılar",
                "url": f"{reverse('users:coordinator_user_list')}?active=inactive",
            },
            {
                "label": "Profili eksik olanlar",
                "url": f"{reverse('users:coordinator_user_list')}?profile=incomplete",
            },
        ]
        return context
