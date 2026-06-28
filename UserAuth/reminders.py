import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings

from .email_utils import send_transactional_email
from .models import Task

logger = logging.getLogger(__name__)


def get_user_timezone(tz_name=None):
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            logger.warning('Unknown timezone %r, using default.', tz_name)
    return timezone.get_current_timezone()


def parse_due_date_time(date_value, time_value, tz_name=None):
    """Combine date/time fields using the user's local timezone."""
    if not date_value or not time_value:
        return None
    combined = f"{date_value.strip()} {time_value.strip()}"
    dt = None
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            dt = datetime.strptime(combined, fmt)
            break
        except ValueError:
            continue
    if dt is None:
        logger.warning('Could not parse due date/time: %r', combined)
        return None
    tz = get_user_timezone(tz_name)
    return timezone.make_aware(dt, tz)


def local_due_parts(due_time, tz_name=None):
    """Split a stored due_time into local date/time strings for form fields."""
    if not due_time:
        return '', ''
    tz = get_user_timezone(tz_name)
    local = due_time.astimezone(tz)
    return local.strftime('%Y-%m-%d'), local.strftime('%H:%M')


def parse_due_datetime(value):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def get_due_tasks():
    now = timezone.now()
    return Task.objects.filter(
        completed=False,
        reminder_sent=False,
        due_time__isnull=False,
        due_time__lte=now,
    ).select_related('user')


def send_task_reminder(task):
    user = task.user
    if not user.email:
        logger.warning(
            'Skipping reminder for task %s — user %s has no email address.',
            task.pk,
            user.username,
        )
        return False

    due_display = timezone.localtime(task.due_time).strftime('%B %d, %Y at %I:%M %p %Z')

    context = {
        'user': user,
        'task': task,
        'due_display': due_display,
        'site_url': getattr(settings, 'SITE_URL', ''),
    }
    subject = render_to_string('emails/task_reminder_subject.txt', context).strip()
    text_body = render_to_string('emails/task_reminder.txt', context)
    html_body = render_to_string('emails/task_reminder.html', context)

    send_transactional_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        to=[user.email],
    )

    task.reminder_sent = True
    task.save(update_fields=['reminder_sent'])
    logger.info('Reminder sent for task %s to %s', task.pk, user.email)
    return True


def process_due_reminders():
    sent = 0
    for task in get_due_tasks():
        try:
            if send_task_reminder(task):
                sent += 1
        except Exception:
            logger.exception('Failed to send reminder for task %s', task.pk)
    return sent
