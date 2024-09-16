from django.apps import AppConfig # type: ignore


class VerificationServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "verification_service"

    def ready(self):
        from .services import GenFileDataExtractionService
        GenFileDataExtractionService()
