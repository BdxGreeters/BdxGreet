from django.core.management.base import BaseCommand, CommandError
from django.contrib import messages
from django.core.management import call_command
import time

class Command(BaseCommand):
    help = "Mise à jour complète des traductions"

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--lang", type=str, help="Langue cible (ex: fr, de, es)"
        )

    def handle(self, *args, **options):
        try:
            lang = options["lang"]
            print(f"Updating translations for language: {lang}")
          

            print(f"Updating translations for language: {lang}")
            self.stdout.write(self.style.WARNING("Execute makemessages"))
            call_command("makemessages", locale=[lang])
            self.stdout.write(self.style.SUCCESS(f"makemessages done for {lang}."))
            time.sleep(5)

            self.stdout.write(self.style.WARNING("Execute makemessages for JavaScript"))
            call_command("makemessages", domain='djangojs', locale=[lang])
            self.stdout.write(self.style.SUCCESS(f"makemessages (js) done for {lang}."))

            self.stdout.write(self.style.WARNING("Update translations..."))
            call_command("update_po", locale=lang)
            self.stdout.write(self.style.WARNING("Translations updated"))

            self.stdout.write(
                self.style.WARNING("Start compiling translations")
            )
            call_command("compilemessages")
            self.stdout.write(self.style.SUCCESS("Compilation is complete."))
        except Exception as e:
            print(e)
            raise CommandError("Error during translation")