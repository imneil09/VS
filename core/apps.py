from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # Change this to your actual app name if different

    def ready(self):
        import core.signals  # Import your signal module here
