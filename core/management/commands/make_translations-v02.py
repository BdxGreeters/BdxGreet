from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

class Command(BaseCommand):
    help = "Mise à jour complète des traductions"

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--lang", type=str, help="Langue cible (ex: fr, de, en-us)"
        )

    def handle(self, *args, **options):
        try:
            # Récupère le code langue de l'argument
            lang_input = options["lang"]
            
            # --- DÉBUT DE LA NORMALISATION ---
            
            # 1. Remplace 'en-us' par 'en_us'
            lang_normalized = lang_input.replace('-', '_')

            # 2. Normalise la casse : 'en_us' -> 'en_US' ou 'FR' -> 'fr'
            if '_' in lang_normalized:
                parts = lang_normalized.split('_')
                if len(parts) == 2:
                    lang_normalized = f"{parts[0].lower()}_{parts[1].upper()}"
                else:
                    # Gère les cas plus complexes en mettant tout en minuscules
                    lang_normalized = lang_normalized.lower()
            else:
                # Pour les langues sans région (ex: 'fr', 'FR', 'de')
                lang_normalized = lang_normalized.lower()

            # --- FIN DE LA NORMALISATION ---

            print(f"Mise à jour des traductions pour : {lang_input} (Normalisé en: {lang_normalized})")
            
            self.stdout.write(self.style.WARNING("Execute makemessages"))
            call_command("makemessages", locale=[lang_normalized])
            self.stdout.write(self.style.SUCCESS(f"makemessages done for {lang_normalized}."))

            self.stdout.write(self.style.WARNING("Execute makemessages for JavaScript"))
            call_command("makemessages", domain='djangojs', locale=[lang_normalized])
            self.stdout.write(self.style.SUCCESS(f"makemessages (js) done for {lang_normalized}."))

            self.stdout.write(self.style.WARNING("Update translations..."))
            
            # --- CORRECTION DE BUG ---
            # 'update_po' attend aussi une liste pour 'locale'
            call_command("update_po", locale=[lang_normalized])
            # --- FIN DE LA CORRECTION ---
            
            self.stdout.write(self.style.WARNING("Translations updated"))

            self.stdout.write(
                self.style.WARNING("Start compiling translations")
            )
            # Compilemessages sans argument compile *toutes* les langues trouvées
            call_command("compilemessages")
            self.stdout.write(self.style.SUCCESS("Compilation is complete."))
        
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
            raise CommandError("Error during translation")