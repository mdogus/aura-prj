from django.urls import reverse

from users.models import User

from .models import Notification


def build_request_target_url(recipient, support_request):
    if recipient == support_request.created_by:
        return reverse('support:student_request_detail', args=[support_request.pk])
    if recipient == support_request.assigned_volunteer:
        return reverse('support:volunteer_request_detail', args=[support_request.pk])
    if recipient.role in (User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR):
        return reverse('support:coordinator_request_detail', args=[support_request.pk])
    return reverse('dashboard:home')


def create_notification(recipient, title, body='', actor=None, support_request=None):
    target_url = ''
    if support_request:
        target_url = build_request_target_url(recipient, support_request)
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        support_request=support_request,
        title=title,
        body=body,
        target_url=target_url,
    )


def notify_users(
    recipients,
    title,
    body='',
    actor=None,
    support_request=None,
    exclude_ids=None,
):
    seen = set(exclude_ids or set())
    for recipient in recipients:
        if not recipient or not recipient.is_active or recipient.id in seen:
            continue
        create_notification(
            recipient=recipient,
            title=title,
            body=body,
            actor=actor,
            support_request=support_request,
        )
        seen.add(recipient.id)


def notify_staff(title, body='', actor=None, support_request=None, exclude_ids=None):
    staff_users = User.objects.filter(
        role__in=[User.Roles.COORDINATOR, User.Roles.ACADEMIC_ADVISOR],
        is_active=True,
    )
    notify_users(
        staff_users,
        title=title,
        body=body,
        actor=actor,
        support_request=support_request,
        exclude_ids=exclude_ids,
    )
