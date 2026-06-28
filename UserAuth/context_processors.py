from django.conf import settings

from UserAuth.email_utils import gmail_sender_mismatch, smtp_is_configured


def email_settings(request):
    ctx = {
        'smtp_configured': smtp_is_configured(),
        'gmail_sender_mismatch': gmail_sender_mismatch(),
        'smtp_sender_email': settings.EMAIL_HOST_USER if smtp_is_configured() else '',
    }
    if request.user.is_authenticated:
        ctx['reminder_email'] = request.user.email or ''
    return ctx
