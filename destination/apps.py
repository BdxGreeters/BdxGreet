from django.apps import AppConfig


class DestinationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'destination'

    def ready(self):
        import core.signals  # Importez les signaux pour qu'ils soient enregistrés
