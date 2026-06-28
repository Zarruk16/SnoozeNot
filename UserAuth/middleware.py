import logging
import time

logger = logging.getLogger(__name__)

_last_check = 0
CHECK_INTERVAL = 15  # seconds


class ReminderMiddleware:
    """Check for due task reminders periodically while the app is handling requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _last_check
        now = time.time()
        if now - _last_check >= CHECK_INTERVAL:
            _last_check = now
            try:
                from UserAuth.reminders import process_due_reminders
                sent = process_due_reminders()
                if sent:
                    logger.info('Sent %s reminder email(s).', sent)
            except Exception:
                logger.exception('Reminder check failed')

        return self.get_response(request)
