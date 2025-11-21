import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import LangueDeepL
from core.tasks import translation_content


class Command(BaseCommand):
    help = "Importe les langues DeepL depuis un fichier CSV"

    def handle(self, *args, **kwargs):
        with open('data/langues_deepl.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                langdeepl, created=LangueDeepL.objects.update_or_create(
                code_iso=row['Code ISO'])
                langdeepl.lang_deepl= row['Nom en français']
                langdeepl.save()
            for langdeepl in LangueDeepL.objects.all():
                translation_content.delay("core","LangueDeepL", langdeepl.id, "lang_deepl")
            
        self.stdout.write(self.style.SUCCESS('Importation terminée avec succès.'))
