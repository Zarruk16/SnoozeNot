"""Email delivery helpers."""

import re
import uuid

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def uses_smtp_backend():
    return 'smtp' in settings.EMAIL_BACKEND.lower()


def smtp_is_configured():
    return uses_smtp_backend() and bool(settings.EMAIL_HOST_USER) and bool(settings.EMAIL_HOST_PASSWORD)


def extract_email_address(value):
    """Return the bare email from 'Name <user@example.com>' or 'user@example.com'."""
    if not value:
        return ''
    match = re.search(r'<([^>]+)>', value)
    if match:
        return match.group(1).strip().lower()
    return value.strip().lower()


def uses_gmail_smtp():
    return smtp_is_configured() and settings.EMAIL_HOST.rstrip('/').endswith('gmail.com')


def gmail_sender_mismatch():
    """True when Gmail SMTP auth account differs from the configured From address."""
    if not uses_gmail_smtp():
        return False
    from_addr = extract_email_address(settings.REMINDER_FROM_EMAIL)
    auth_addr = settings.EMAIL_HOST_USER.strip().lower()
    return bool(from_addr and auth_addr and from_addr != auth_addr)


def reminder_delivery_message(sent_count):
    if not sent_count:
        return None
    if smtp_is_configured():
        return (
            'Reminder email sent to your inbox. '
            'Check spam/promotions if you don\'t see it — add the SnoozeNot sender to your contacts.'
        )
    return (
        'Reminder was logged on the server only. Add Gmail SMTP credentials to .env '
        'and restart to receive emails in your inbox.'
    )


def scheduled_reminder_message(due_time):
    display = due_time.strftime('%B %d, %Y at %I:%M %p %Z')
    if smtp_is_configured():
        return (
            f'Reminder scheduled for {display}. '
            'You\'ll receive an email when the task is due.'
        )
    return (
        f'Reminder scheduled for {display}, but SMTP is not configured — '
        'emails will not be delivered to your inbox.'
    )


def send_transactional_email(*, subject, text_body, html_body, to):
    """Send a multipart HTML + plain-text email with headers that help inbox placement."""
    recipients = to if isinstance(to, (list, tuple)) else [to]
    from_addr = extract_email_address(settings.REMINDER_FROM_EMAIL)
    domain = from_addr.split('@')[-1] if '@' in from_addr else 'snoozenot.local'

    headers = {
        'Message-ID': f'<{uuid.uuid4()}@{domain}>',
        'X-Auto-Response-Suppress': 'OOF, AutoReply',
        'X-Mailer': 'SnoozeNot',
    }

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.REMINDER_FROM_EMAIL,
        to=recipients,
        reply_to=[settings.REMINDER_REPLY_TO],
        headers=headers,
    )
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)
