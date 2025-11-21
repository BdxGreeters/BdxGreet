from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Language_communication as Language
from core.tasks import translation_content_items
from core.translation import Language_communicationTranslationOptions


# Command
class Command(BaseCommand):
    help = 'Peuple la table des langues à partir de settings.LANGUAGES'

    def handle(self, *args, **options):
        for code, name in settings.LANGUAGES:
            lang_object=Language.objects.get_or_create(code=code,name=name)
            translation_content_items.delay('core', 'Language_communication', lang_object[0].id, 'name')
        self.stdout.write(self.style.SUCCESS('Langues ajoutées avec succès!'))