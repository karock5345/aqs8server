import os
from logging.handlers import RotatingFileHandler

class CustomRotatingFileHandler(RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        self.max_log_files = kwargs.pop('max_log_files', 10)
        super().__init__(*args, **kwargs)

    def doRollover(self):
        super().doRollover()
        self.delete_old_logs()

    def delete_old_logs(self):
        log_dir = os.path.dirname(self.baseFilename)
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.startswith(os.path.basename(self.baseFilename))],
            key=lambda f: os.path.getmtime(os.path.join(log_dir, f))
        )
        while len(log_files) > self.max_log_files:
            os.remove(os.path.join(log_dir, log_files.pop(0)))