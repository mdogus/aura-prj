from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


BADGE_PREFIXES = {
    'status': 'Durum',
    'urgency': 'Aciliyet',
    'priority': 'Öncelik',
    'category': 'Kategori',
    'role': 'Rol',
    'user_state': 'Kullanıcı durumu',
    'profile_state': 'Profil durumu',
}

BADGE_METADATA = {
    'status': {
        'open': {'class': 'badge badge-status-open', 'icon': 'icon-dot'},
        'matched': {'class': 'badge badge-status-matched', 'icon': 'icon-users'},
        'in_progress': {'class': 'badge badge-status-progress', 'icon': 'icon-clock'},
        'completed': {'class': 'badge badge-status-completed', 'icon': 'icon-check'},
        'cancelled': {'class': 'badge badge-status-cancelled', 'icon': 'icon-close'},
    },
    'urgency': {
        'low': {'class': 'badge badge-urgency-low', 'icon': 'icon-gentle'},
        'medium': {'class': 'badge badge-urgency-medium', 'icon': 'icon-clock'},
        'high': {'class': 'badge badge-urgency-high', 'icon': 'icon-alert'},
    },
    'priority': {
        'normal': {'class': 'badge badge-neutral', 'icon': 'icon-dot'},
        'high': {'class': 'badge badge-urgency-medium', 'icon': 'icon-flag'},
        'critical': {'class': 'badge badge-urgency-high', 'icon': 'icon-alert'},
    },
    'category': {
        'accessible_material': {'class': 'badge badge-neutral', 'icon': 'icon-file'},
        'audio_narration': {'class': 'badge badge-neutral', 'icon': 'icon-audio'},
        'academic': {'class': 'badge badge-neutral', 'icon': 'icon-cap'},
        'joint_study': {'class': 'badge badge-neutral', 'icon': 'icon-users'},
        'visual_description': {'class': 'badge badge-neutral', 'icon': 'icon-image'},
        'resource_access': {'class': 'badge badge-neutral', 'icon': 'icon-book'},
        'exam_preparation': {'class': 'badge badge-neutral', 'icon': 'icon-target'},
        'wayfinding': {'class': 'badge badge-neutral', 'icon': 'icon-compass'},
        'daily_life': {'class': 'badge badge-neutral', 'icon': 'icon-life'},
        'social_activity': {'class': 'badge badge-neutral', 'icon': 'icon-users'},
    },
    'role': {
        'visually_impaired_student': {'class': 'badge badge-role-student', 'icon': 'icon-user'},
        'volunteer_student': {'class': 'badge badge-role-volunteer', 'icon': 'icon-users'},
        'academic_advisor': {'class': 'badge badge-role-advisor', 'icon': 'icon-cap'},
        'coordinator': {'class': 'badge badge-role-coordinator', 'icon': 'icon-shield'},
    },
    'user_state': {
        'active': {'class': 'badge badge-neutral', 'icon': 'icon-check'},
        'inactive': {'class': 'badge badge-status-cancelled', 'icon': 'icon-pause'},
    },
    'profile_state': {
        'completed': {'class': 'badge badge-status-completed', 'icon': 'icon-check'},
        'incomplete': {'class': 'badge badge-status-open', 'icon': 'icon-pencil'},
    },
}

ACTIVITY_PREFIX = "İşlem türü"

ACTIVITY_METADATA = {
    'request_created': {'class': 'badge badge-neutral', 'icon': 'icon-plus'},
    'status_updated': {'class': 'badge badge-status-progress', 'icon': 'icon-clock'},
    'priority_updated': {'class': 'badge badge-urgency-medium', 'icon': 'icon-flag'},
    'volunteer_assigned': {'class': 'badge badge-role-volunteer', 'icon': 'icon-user'},
    'intervention_note': {'class': 'badge badge-role-coordinator', 'icon': 'icon-chat'},
    'message_posted': {'class': 'badge badge-neutral', 'icon': 'icon-chat'},
    'material_uploaded': {'class': 'badge badge-neutral', 'icon': 'icon-upload'},
}


def _get_badge_meta(kind, value):
    return BADGE_METADATA.get(kind, {}).get(
        value,
        {'class': 'badge badge-neutral', 'icon': 'icon-list'},
    )


def _get_activity_meta(value):
    return ACTIVITY_METADATA.get(
        value,
        {'class': 'badge badge-neutral', 'icon': 'icon-list'},
    )


@register.filter
def status_badge_class(value):
    return _get_badge_meta('status', value)['class']


@register.filter
def urgency_badge_class(value):
    return _get_badge_meta('urgency', value)['class']


@register.filter
def priority_badge_class(value):
    return _get_badge_meta('priority', value)['class']


@register.filter
def notification_badge_class(is_read):
    if is_read:
        return 'badge badge-neutral'
    return 'badge badge-urgency-high'


@register.filter
def role_badge_class(value):
    return _get_badge_meta('role', value)['class']


@register.filter
def basename(value):
    return Path(str(value)).name


@register.simple_tag
def static_asset_exists(path):
    for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
        candidate = Path(static_dir) / path
        if candidate.exists():
            return True
    return False


@register.simple_tag
def render_field(bound_field):
    attrs = {}
    described_by = []
    current_described_by = bound_field.field.widget.attrs.get('aria-describedby', '')
    if current_described_by:
        described_by.extend(current_described_by.split())

    help_id = f'{bound_field.id_for_label}_help'
    error_id = f'{bound_field.id_for_label}_error'

    if bound_field.help_text and help_id not in described_by:
        described_by.append(help_id)
    if bound_field.errors and error_id not in described_by:
        described_by.append(error_id)
        attrs['aria-invalid'] = 'true'

    if described_by:
        attrs['aria-describedby'] = ' '.join(described_by)

    return mark_safe(bound_field.as_widget(attrs=attrs))


@register.simple_tag
def render_badge(kind, value, label=None):
    meta = _get_badge_meta(kind, value)
    visible_label = label or str(value)
    prefix = BADGE_PREFIXES.get(kind, 'Etiket')
    aria_label = f"{prefix}: {visible_label}"
    return format_html(
        '<span class="{css_class}" aria-label="{aria_label}">'
        '<span class="sr-only">{prefix}: </span>'
        '<svg class="icon badge-icon" aria-hidden="true"><use href="#{icon_id}"></use></svg>'
        '<span>{label}</span>'
        '</span>',
        css_class=meta['class'],
        aria_label=aria_label,
        prefix=prefix,
        icon_id=meta['icon'],
        label=visible_label,
    )


@register.simple_tag
def render_activity_badge(value, label=None):
    meta = _get_activity_meta(value)
    visible_label = label or str(value)
    aria_label = f"{ACTIVITY_PREFIX}: {visible_label}"
    return format_html(
        '<span class="{css_class}" aria-label="{aria_label}">'
        '<span class="sr-only">{prefix}: </span>'
        '<svg class="icon badge-icon" aria-hidden="true"><use href="#{icon_id}"></use></svg>'
        '<span>{label}</span>'
        '</span>',
        css_class=meta['class'],
        aria_label=aria_label,
        prefix=ACTIVITY_PREFIX,
        icon_id=meta['icon'],
        label=visible_label,
    )
