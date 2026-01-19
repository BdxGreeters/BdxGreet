from django.utils.safestring import mark_safe
from django.utils.text import capfirst

class HelpTextTooltipMixin:
    """
    Mixin qui transforme les help_text en tooltips Bootstrap.
    Doit être appelé explicitement via self.apply_tooltips() à la fin du __init__ du formulaire.
    """
    def apply_tooltips(self):
        for field_name, field in self.fields.items():
            help_text = field.help_text
            
            # On traite le champ seulement s'il a un help_text
            if help_text:
                # Si le label est vide (cas de vos checkboxes), on met une chaîne vide pour éviter 'None'
                current_label = field.label or ""
                
                # Si le label n'est pas défini mais que ce n'est pas voulu vide (ex: champs automatiques)
                if not current_label and field.label is None:
                     current_label = capfirst(field_name.replace("_", " "))

                # On vide le help_text standard pour éviter le doublon
                field.help_text = None
                
                # Création de l'icône. 
                # Astuce : Pour une checkbox sans label, on ajoute un petit padding
                icon_style = "margin-left: 5px;" if current_label else ""
                
                tooltip_html = f'''
                    <span data-bs-toggle="tooltip" title="{help_text}" style="cursor: help;">
                        <i class="bi bi-info-circle text-info" style="{icon_style}"></i>
                    </span>
                '''
                
                # On met à jour le label
                field.label = mark_safe(f"{current_label}{tooltip_html}")
###################################################################################################

# Ajout à une liste dans un champ Texte

class CommaSeparatedFieldMixin:
    comma_fields_config = {}  # Exemple : {'list_experience_cluster': {'min': 1, 'max': 5}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.comma_fields_config:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'comma-input-field',
                    'data-field-name': field_name,
                    'data-min-items': self.comma_fields_config[field_name].get('min', 0),
                    'data-max-items': self.comma_fields_config[field_name].get('max', 10),
                })



    def clean(self):
        cleaned_data = super().clean()
        for field_name, config in self.comma_fields_config.items():
            value = cleaned_data.get(field_name, "")
            items = [item.strip() for item in value.split(",") if item.strip()]
            min_items = config.get('min', 0)
            max_items = config.get('max', 10)
            if len(items) < min_items:
                self.add_error(field_name, f"Minimum {min_items} éléments requis.")
            elif len(items) > max_items:
                self.add_error(field_name, f"Maximum {max_items} éléments autorisés.")
            else:
                cleaned_data[field_name] = ",".join(items)
        return cleaned_data


###################################################################################################
# Mixin Gestion des permissions des champs définis éditables dans un formulaire

from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
# Assurez-vous d'importer votre modèle FieldPermission
from core.models import FieldPermission 

class FormFieldPermissionMixin:
    permission_groups = []  
    target_group_name = None  
    app_name = None

    def user_has_any_permission_group(self, user):
    # Un superutilisateur a toujours les droits
        if user.is_superuser:
            return True # Indentation corrigée
        
        if not self.permission_groups: # Indentation corrigée
            return False # Indentation corrigée

        return user.groups.filter(name__in=self.permission_groups).exists() # Indentation corrigée

    def get_field_permissions(self, obj):
        if not self.target_group_name:
            raise ValueError("Le nom du groupe cible n'est pas défini.")

        target_group = get_object_or_404(Group, name=self.target_group_name)
        content_type = ContentType.objects.get_for_model(obj)
        permissions = FieldPermission.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            app_name=self.app_name,
            target_group=target_group
        )
        return {p.field_name: p.is_editable for p in permissions}

    # RENOMMÉ POUR CORRESPONDRE À LA VUE
    def update_field_permissions(self, obj, form):
        if not self.target_group_name or not self.app_name:
            raise ValueError("target_group_name et app_name doivent être définis.")

        target_group = get_object_or_404(Group, name=self.target_group_name)
        content_type = ContentType.objects.get_for_model(obj)
        
        # Récupère la liste des champs gérables définie dans le formulaire
        current_editable_fields = getattr(form, 'editable_fields', [])

        # 1. NETTOYAGE
        FieldPermission.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            target_group=target_group,
            app_name=self.app_name
        ).exclude(field_name__in=current_editable_fields).delete()

        # 2. MISE À JOUR / CRÉATION
        for field_name in current_editable_fields:
            permission_key = f'can_edit_{field_name}'
            # Important : on vérifie si la clé existe dans cleaned_data
            if permission_key in form.cleaned_data:
                is_editable = form.cleaned_data.get(permission_key)
                
                FieldPermission.objects.update_or_create(
                    field_name=field_name,
                    content_type=content_type,
                    object_id=obj.id,
                    app_name=self.app_name,
                    target_group=target_group,
                    defaults={'is_editable': is_editable}
                )
            
            

###################################################################################################

# Mixin pour gérer la création/mise à jour des modèles liés à un autre modèle par des champs CharFied

from django.db import transaction
from core.tasks import translation_content

class RelatedModelsMixin:
    """
    Mixin pour gérer les relations ManyToMany via des champs texte (tags).
    Déclenche la traduction asynchrone via Celery après le commit de la transaction.
    """
    related_fields = {} 

    def save_related_data(self, form):
        """
        Méthode à appeler dans le form_valid de la vue.
        """
        instance = self.object
        
        for form_field, (model, m2m_field, model_attr) in self.related_fields.items():
            # 1. Récupération des données du formulaire
            data_string = form.cleaned_data.get(form_field, "")
            
            # 2. Identification des anciens objets pour le nettoyage des orphelins
            old_objects_ids = list(getattr(instance, m2m_field).values_list('id', flat=True))
            
            # 3. Traitement des nouveaux noms saisis
            names = [name.strip() for name in data_string.split(',') if name.strip()]
            new_objects = []
            
            for name in names:
                # Création ou récupération de l'objet lié
                obj, created = model.objects.get_or_create(**{model_attr: name})
                
                # 4. Si l'objet est nouveau, on planifie la traduction
                if created:
                    # On prépare les données pour Celery
                    app_label = obj._meta.app_label
                    model_name = obj._meta.model_name
                    obj_id = obj.pk
                    field_name = model_attr

                    # Utilisation de transaction.on_commit pour garantir que l'objet
                    # existe en base de données avant que Celery ne tente de le lire.
                    # On utilise des arguments par défaut (a=..., m=...) pour figer 
                    # les valeurs dans la boucle.
                    transaction.on_commit(
                        lambda a=app_label, m=model_name, i=obj_id, f=field_name: 
                        translation_content.delay(a, m, i, f)
                    )
                
                new_objects.append(obj)
            
            # 5. Mise à jour de la relation ManyToMany de l'instance
            getattr(instance, m2m_field).set(new_objects)

            # 6. Suppression des orphelins (objets qui ne sont plus liés à rien)
            new_objects_ids = [o.id for o in new_objects]
            removed_ids = set(old_objects_ids) - set(new_objects_ids)

            if removed_ids:
                # Récupération dynamique de la relation inverse pour compter les liens
                m2m_field_obj = instance._meta.get_field(m2m_field)
                related_query_name = m2m_field_obj.related_query_name()

                for orphan_id in removed_ids:
                    try:
                        orphan = model.objects.get(id=orphan_id)
                        # On ne supprime que si cet objet n'est lié à aucun autre parent
                        if getattr(orphan, related_query_name).count() == 0:
                            orphan.delete()
                    except model.DoesNotExist:
                        continue