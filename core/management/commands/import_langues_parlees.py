import csv
from django.core.management.base import BaseCommand
from core.models import LangueParlee
from django.conf import settings
from core.tasks import translation_content


class Command(BaseCommand):
    help = "Importe les langues parlées depuis un fichier CSV"

    def handle(self, *args, **kwargs):
        with open('data/langues_parlees.csv', 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                langue, created = LangueParlee.objects.update_or_create(
                   code_iso=row['Code ISO'])
                langue.langue_parlee = row['Nom en français']
                langue.save()
            for langue in LangueParlee.objects.all():
                translation_content.delay("core","LangueParlee", langue.id, "langue_parlee")
                
            
        self.stdout.write(self.style.SUCCESS('Importation terminée avec succès.'))  