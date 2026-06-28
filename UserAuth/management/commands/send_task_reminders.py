import logging

from django.core.management.base import BaseCommand

from UserAuth.reminders import get_due_tasks, process_due_reminders

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send email reminders for tasks that have reached their due time'

    def handle(self, *args, **options):
        pending = list(get_due_tasks())
        self.stdout.write(f'Found {len(pending)} due task(s).')

        for task in pending:
            user = task.user
            if not user.email:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped "{task.title}" — user "{user.username}" has no email.'
                ))
            else:
                self.stdout.write(f'  Queued "{task.title}" → {user.email}')

        count = process_due_reminders()
        backend = __import__('django.conf', fromlist=['settings']).settings.EMAIL_BACKEND
        self.stdout.write(self.style.SUCCESS(f'Sent {count} reminder email(s).'))
        self.stdout.write(f'Email backend: {backend}')
