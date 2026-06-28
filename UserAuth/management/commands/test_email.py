from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from UserAuth.email_utils import send_transactional_email, smtp_is_configured


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP settings in .env'

    def add_arguments(self, parser):
        parser.add_argument('recipient', nargs='?', help='Email address to send the test to')

    def handle(self, *args, **options):
        if not smtp_is_configured():
            raise CommandError(
                'SMTP is not configured. Edit .env and set EMAIL_HOST_USER and '
                'EMAIL_HOST_PASSWORD (Gmail App Password), then restart the server.'
            )

        recipient = options['recipient'] or settings.EMAIL_HOST_USER
        if not recipient:
            raise CommandError('Provide a recipient email or set EMAIL_HOST_USER in .env.')

        site_url = getattr(settings, 'SITE_URL', '') or 'http://127.0.0.1:8000'
        send_transactional_email(
            subject='SnoozeNot test email',
            text_body=(
                'If you received this, reminder emails are configured correctly.\n\n'
                f'Open SnoozeNot: {site_url}\n'
            ),
            html_body=(
                '<p>If you received this, reminder emails are configured correctly.</p>'
                f'<p><a href="{site_url}">Open SnoozeNot</a></p>'
            ),
            to=[recipient],
        )
        self.stdout.write(self.style.SUCCESS(f'Test email sent to {recipient}'))
