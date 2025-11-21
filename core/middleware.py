# Dans le fichier de votre middleware
import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class UserLanguageRedirectMiddleware(MiddlewareMixin):
    """
    Ce middleware vérifie si un utilisateur authentifié a une langue préférée
    différente de celle de l'URL actuelle. Si c'est le cas, il le redirige
    vers la même page, mais avec le préfixe de sa langue.
    """
    def process_request(self, request):
        
        # Ne rien faire si l'utilisateur n'est pas authentifié
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        try:
            # Langue préférée de l'utilisateur (ex: 'fr')
            user_lang = request.user.lang_com
        except AttributeError:
            # L'utilisateur n'a pas de champ 'lang_com'
            return None

        if not user_lang:
            return None # Le champ est défini mais vide

        # Langue actuelle de la requête, déterminée par LocaleMiddleware (ex: 'en')
        current_lang = translation.get_language()

        # Si la langue de l'URL est déjà la bonne, on ne fait rien
        if user_lang == current_lang:
            return None
            
        # Vérifier si la langue de l'utilisateur est valide
        if user_lang not in [lang[0] for lang in settings.LANGUAGES]:
            return None

        # Obtenir le chemin complet avec les paramètres GET (ex: /en/profil/?page=2)
        full_path = request.get_full_path()

        # Remplacer l'ancien préfixe de langue par le nouveau
        # Gère /en/profil/ -> /fr/profil/
        new_path = re.sub(f'^/{current_lang}/', f'/{user_lang}/', full_path)
        
        # Gère le cas où la langue actuelle était la langue par défaut
        # sans préfixe (si PREFIX_DEFAULT_LANGUAGE = False)
        # et que le chemin ne commence pas par un préfixe
        if (current_lang == settings.LANGUAGE_CODE and 
            not settings.PREFIX_DEFAULT_LANGUAGE and 
            not full_path.startswith(f'/{current_lang}/')):
            
            # On vérifie que ce n'est pas une URL non-traduite (ex: /admin/, /i18n/)
            # C'est une simplification ; idéalement, on vérifie si l'URL
            # fait partie de i18n_patterns. Pour cet exemple, on suppose
            # que si l'URL ne commence pas par un préfixe, c'est la langue par défaut.
            new_path = f'/{user_lang}{full_path}'


        # Si le remplacement a fonctionné et que le chemin a changé
        if new_path != full_path:
            return HttpResponseRedirect(new_path)
            
        return None
