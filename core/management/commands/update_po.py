import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.translator import translate


class Command(BaseCommand):
    help = "Met à jour les fichiers .po avec des traductions DeepL"

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--locale", type=str, help="Langue cible (ex: fr, de, es)"
        )

    def handle(self, *args, **options):
        try:
            if settings.DEBUG is False:
                raise Exception("Must be used in development only")

            import polib

            locale = options["locale"]
            # base_dir = os.getcwd()
            base_dir = settings.BASE_DIR
            
            for app in os.listdir(base_dir):
                
                locale_path = os.path.join(
                    base_dir, app, locale,"LC_MESSAGES"
                )
                print(locale_path)
                po_file_path = os.path.join(locale_path, "django.po")
                if not os.path.exists(po_file_path):
                    continue

                po = polib.pofile(po_file_path)
                
                for entry in po:
                    if not entry.translated():
                        if "_" in locale:
                            locale=locale.replace("_", "-")
                        translated_text = translate(entry.msgid, locale)
                        entry.msgstr = translated_text
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"[{app}] Traduit: {entry.msgid} -> {translated_text}"
                            )
                        )

                po.save()
                
                po_file_path = os.path.join(locale_path, "djangojs.po")
                if not os.path.exists(po_file_path):
                    continue

                po = polib.pofile(po_file_path)
                
                for entry in po:
                    if not entry.translated():
                        if "_" in locale:
                            locale=locale.replace("_", "-")
                        translated_text = translate(entry.msgid, locale)
                        entry.msgstr = translated_text
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"[{app}] Traduit: {entry.msgid} -> {translated_text}"
                            )
                        )

                po.save()

                self.stdout.write(
                    self.style.SUCCESS(f"Mise à jour terminée pour {po_file_path}")
                )
        except Exception as e:
            print(e)
            raise CommandError("Error during translation")