###################################################################################################
# Vue Mixin pour les permissions de champ pour le gestionnaire de destination

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class OnlyGestionnaireMixin(AccessMixin):
    """
    Mixin pour restreindre la modification des champs.
    Il vérifie si l'utilisateur est STRICTEMENT 'Gestionnaire', 
    c'est-à-dire qu'il n'appartient à aucun des groupes à privilège supérieur.
    """
    
    # 🚨 DOIT ÊTRE DÉFINI DANS LA VUE QUI UTILISE LE MIXIN
    gestionnaire_fields = []
    
    # Les groupes qui accordent des privilèges supérieurs à 'Gestionnaire'
    higher_privilege_groups = ['SuperAdmin', 'Admin','Referent']
    
    
    def _is_only_gestionnaire(self, user):
        """ Logique interne de vérification des groupes. """
        if not user.is_authenticated:
            return False

        user_groups = user.groups.all().values_list('name', flat=True)

        is_gestionnaire = 'Gestionnaire' in user_groups
        has_higher_privilege = any(group in user_groups for group in self.higher_privilege_groups)

        # L'utilisateur est 'Gestionnaire' ET n'a AUCUN privilège supérieur.
        return is_gestionnaire and not has_higher_privilege

    
    def get_form(self, form_class=None):
        """ Modifie le formulaire en désactivant les champs non autorisés. """
        form = super().get_form(form_class)

        if form is None:
            return None
    
        user = self.request.user
    
    # Appliquer la désactivation SEULEMENT si l'utilisateur est un 'Gestionnaire' simple
        if self._is_only_gestionnaire(user):
        # On récupère tous les champs du formulaire
            all_fields = form.fields.keys()
        
        # Si gestionnaire_fields est [], 'field not in self.gestionnaire_fields' 
        # sera toujours True, donc tous les champs seront désactivés.
            fields_to_disable = [
            field for field in all_fields 
            if field not in self.gestionnaire_fields
            ]
            print("Champs à désactiver pour le gestionnaire :", fields_to_disable)

        # Désactiver les champs identifiés
            for field_name in fields_to_disable:
                form.fields[field_name].disabled = True
            
        return form

# Fin du mixin
###################################################################################################
