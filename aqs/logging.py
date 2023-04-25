from django.db import models, connections
from django.utils import timezone
import logging

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            level = record.levelname
            message = self.format(record)
            timestamp = timezone.now()
            with connections['default'].cursor() as cursor:
                cursor.execute("INSERT INTO myapp_log (level, message, timestamp) VALUES (%s, %s, %s)",
                               [level, message, timestamp])
        except:
            self.handleError(record)
