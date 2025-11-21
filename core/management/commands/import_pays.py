import csv

from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404

from core.models import Pays
from core.tasks import translation_content


class Command(BaseCommand):
    help = "Importe les pays depuis un fichier CSV"

    def handle(self, *args, **kwargs):
        with open('data/pays.csv', 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile,delimiter=';')
            for row in reader:
                pays, created = Pays.objects.update_or_create(
                    code_iso=row['Code_Iso'])
                pays.nom_pays = row['Nom en français']
                pays.save()
            
            for pays in Pays.objects.all():
                translation_content.delay("core","Pays", pays.id, "nom_pays")
        self.stdout.write(self.style.SUCCESS('Importation terminée avec succès.'))