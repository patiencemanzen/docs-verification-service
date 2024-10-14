from django.apps import AppConfig # type: ignore
import subprocess
import os
import sys

class VerificationServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "verification_service"

    def ready(self):
        from .services import DataExtractionService
        DataExtractionService.initChatSession()

        # Ensure this runs only once
        if os.environ.get('RUN_MAIN') == 'true' or 'runserver' not in sys.argv:
            return

        subprocess.Popen(['celery', '-A', 'gemini_verification_service', 'worker', '--loglevel=info'])
