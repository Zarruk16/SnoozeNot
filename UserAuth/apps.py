import logging
import os
import sys
import threading
import time

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class UserauthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'UserAuth'

    def ready(self):
        if 'runserver' not in sys.argv:
            return
        if os.environ.get('RUN_MAIN') != 'true':
            return
        self._start_reminder_scheduler()

    def _start_reminder_scheduler(self):
        def loop():
            from UserAuth.reminders import process_due_reminders

            while True:
                try:
                    sent = process_due_reminders()
                    if sent:
                        logger.info('Background scheduler sent %s reminder(s).', sent)
                except Exception:
                    logger.exception('Background reminder scheduler error')
                time.sleep(15)

        thread = threading.Thread(target=loop, daemon=True, name='reminder-scheduler')
        thread.start()
        logger.info('Task reminder scheduler started (checks every 15s).')

        from UserAuth.email_utils import gmail_sender_mismatch, smtp_is_configured
        if smtp_is_configured():
            logger.info('Email: SMTP configured — reminders will be sent to user inboxes.')
            if gmail_sender_mismatch():
                logger.warning(
                    'Email: REMINDER_FROM_EMAIL does not match EMAIL_HOST_USER. '
                    'Gmail sends as %s and shows that Google account profile photo. '
                    'Use a dedicated SnoozeNot Gmail account in .env (see .env.example).',
                    settings.EMAIL_HOST_USER,
                )
        else:
            logger.warning(
                'Email: SMTP NOT configured — reminders only print in this terminal. '
                'Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env, then restart.'
            )
