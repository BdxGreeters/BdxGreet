from crispy_forms.bootstrap import (InlineCheckboxes, InlineRadios, Tab,
                                    TabHolder)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Column, Div, Field, Fieldset, Hidden,
                                 Layout, Row, Submit)
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from cluster.models import Cluster
from core.mixins import CommaSeparatedFieldMixin, HelpTextTooltipMixin, FormFieldPermissionMixin
from core.models import FieldPermission, Language_communication, Pays

User = get_user_model()

class ClusterForm(CommaSeparatedFieldMixin, HelpTextTooltipMixin, forms.ModelForm):
    interest_center = forms.CharField(required=True, label=_("Centres d'intérêt"), help_text=_("Saisissez les centres d'intérêts en les validant par Entrée"))
    experience_greeter = forms.CharField(required=True, label=_("Expériences du Greeter"), help_text=_("Saisissez les expériences du Greeter sen les validant par Entrée"))
    no_reply_greeter= forms.CharField(required=True, label=_("Raisons de non réponse du Greeter"), help_text=_("Saisissez les raisons de non réponse du Greeter en les validant par Entrée"))
    no_reply_visitor= forms.CharField(required=True, label=_("Raisons de non réponse du visiteur"), help_text=_("Saisissez les raisons de non réponse du visiteur en les validant par Entrée"))
    notoriety= forms.CharField(required=True, label=_("Notoriété"), help_text=_("Saisissez les motifs de notoriété en les validant par Entrée"))
    pending_adm_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pending_adm_alt_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    

    editable_fields = [
        'code_cluster', 'name_cluster', 'statut_cluster', 'adress_cluster', 'desc_cluster',
        'paypal_cluster', 'admin_cluster', 'country_admin_cluster', 'admin_alt_cluster',
        'country_admin_alt_cluster', 'param_nbr_part_cluster', 'langs_com',
        'backup_mails_cluster', 'url_biblio_cluster', 'url_biblio_Greeter_cluster',
        'experience_greeter', 'interest_center', 'no_reply_greeter',
        'no_reply_visitor', 'notoriety'
    ]

    class Meta:
        model = Cluster
        fields = [
            'code_cluster', 'name_cluster', 'statut_cluster', 'adress_cluster', 'desc_cluster',
            'paypal_cluster', 'admin_cluster', 'country_admin_cluster', 'admin_alt_cluster',
            'country_admin_alt_cluster', 'param_nbr_part_cluster', 'langs_com',
            'backup_mails_cluster', 'url_biblio_cluster', 'url_biblio_Greeter_cluster'
        ]
        widgets = {
            'admin_cluster': forms.Select(attrs={'class': 'form-select'}),
            'country_admin_cluster' : forms.Select(attrs={'class': 'form-select'}),
            'country_admin_alt_cluster' : forms.Select(attrs={'class': 'form-select'}),
            'admin_alt_cluster': forms.Select(attrs={'class': 'form-select'}),
            'statut_cluster': forms.RadioSelect(),
            'langs_com': forms.CheckboxSelectMultiple(),
            'desc_cluster': forms.Textarea(attrs={'rows': 2}),
        }

    comma_fields_config = {
        'experience_greeter': {'min': 2, 'max': 10},
        'interest_center': {'min': 2, 'max': 10},
        'notoriety': {'min': 2, 'max': 10},
        'no_reply_visitor': {'min': 2, 'max': 10},
        'no_reply_greeter': {'min': 1, 'max': 10}
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ajouter un champ BooleanField pour chaque champ éditable
        for field_name in self.editable_fields:
            self.fields[f'can_edit_{field_name}'] = forms.BooleanField(
                label="",
                required=False,
                initial=False,
                help_text=_("Cocher la case pour autoriser l'édition du champ par l'administrateur")
                
            )

        # Masquer les cases à cocher si l'utilisateur n'est pas dans un groupe autorisé
        if self.user and not self.user.groups.filter(name__in=['SuperAdmin']).exists():
            for field_name in self.editable_fields:
                self.fields[f'can_edit_{field_name}'].widget = forms.HiddenInput()

        # Si l'utilisateur est autorisé et qu'on modifie un objet existant
        if self.user and self.user.groups.filter(name__in=['SuperAdmin']).exists() and self.instance and self.instance.pk:
            target_group = get_object_or_404(Group, name='Admin')
            content_type = ContentType.objects.get_for_model(self.instance)
            permissions = FieldPermission.objects.filter(
                content_type=content_type,
                object_id=self.instance.pk,
                target_group=target_group,
                app_name='cluster'
            )
            for field_name in self.editable_fields:
                permission = permissions.filter(field_name=field_name).first()
                if permission and permission.is_editable:
                    self.fields[f'can_edit_{field_name}'].initial = True

        # Filtrer les utilisateurs éligibles pour admin_cluster et admin_alt_cluster
        excluded_users = User.objects.filter(
            Q(admin_cluster__isnull=False) | Q(admin_alt_cluster__isnull=False)
        ).exclude(
            Q(admin_cluster=self.instance) | Q(admin_alt_cluster=self.instance)
        ).distinct() if self.instance and self.instance.pk else User.objects.filter(
            Q(admin_cluster__isnull=False) | Q(admin_alt_cluster__isnull=False)
        ).distinct()

        eligible_users = User.objects.filter(
            is_superuser=False,
        ).exclude(
            groups__name='Greeter'
        ).exclude(
            id__in=excluded_users
        )

        if self.instance and self.instance.pk:
            if self.instance.admin_cluster:
                eligible_users = eligible_users | User.objects.filter(pk=self.instance.admin_cluster.pk)
            if self.instance.admin_alt_cluster:
                eligible_users = eligible_users | User.objects.filter(pk=self.instance.admin_alt_cluster.pk)

        self.fields['admin_cluster'].queryset = eligible_users
        self.fields['admin_alt_cluster'].queryset = eligible_users

        # Initialiser les valeurs des champs admin_cluster et admin_alt_cluster
        if self.instance and self.instance.pk:
            self.fields['admin_cluster'].initial = self.instance.admin_cluster
            self.fields['admin_alt_cluster'].initial = self.instance.admin_alt_cluster

        self.fields['country_admin_cluster'].queryset = Pays.objects.all().order_by('nom_pays')
        self.fields['country_admin_alt_cluster'].queryset = Pays.objects.all().order_by('nom_pays')

        self.apply_tooltips() #Appel du mixin HelpextTooltip

        # Configuration du layout avec crispy_forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'pending_adm_id',
            'pending_adm_alt_id',
            TabHolder(
                Tab(
                    _("Identification"),
                    Row(
                        Column('code_cluster', css_class='col-md-2'),
                        Column('name_cluster', css_class='col-md-6'),
                        Column('can_edit_name_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                    Row(
                        Column('adress_cluster', css_class='col-md-11'),
                        Column('can_edit_adress_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column(Field('desc_cluster'), css_class='col-md-11'),
                        Column('can_edit_desc_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                ),
                Tab(
                    _("Administration"),
                    Fieldset(
                        _("Administrateur principal"),
                        Row(
                            Column('admin_cluster', css_class='col-md-6'),
                            Column('can_edit_admin_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                            Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_adm" data-pending-field="id_pending_adm_id">{_("Nouvel utilisateur")}</button>'),
                                   css_class="d-flex align-items-center")
                        ),
                        Row(
                            Column('country_admin_cluster', css_class='col-md-4'),
                            Column('can_edit_country_admin_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        ),
                        css_class="fieldset-personnalise"
                    ),
                    Fieldset(
                        _("Administrateur alternatif"),
                        Row(
                            Column('admin_alt_cluster', css_class='col-md-6'),
                            Column('can_edit_admin_alt_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                            Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_adm_alt" data-pending-field="id_pending_adm_alt_id">{_("Nouvel utilisateur")}</button>'),
                                   css_class="d-flex align-items-center")
                        ),
                        Row(
                            Column('country_admin_alt_cluster', css_class='col-md-4'),
                            Column('can_edit_country_admin_alt_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        ),
                        css_class="fieldset-personnalise"
                    ),
                ),
                Tab(
                    _("Paramètres"),
                    Row(
                        Column(InlineRadios('statut_cluster', css_class='col-md-6')),
                        Column('can_edit_statut_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                    Row(
                        Column(InlineCheckboxes('langs_com', css_class='col-md-9')),
                        Column('can_edit_langs_com', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                    Row(
                        Column('param_nbr_part_cluster', css_class='col-md-3'),
                        Column('can_edit_param_nbr_part_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('paypal_cluster', css_class='col-md-6'),
                        Column('can_edit_paypal_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('backup_mails_cluster', css_class='col-md-6'),
                        Column('can_edit_backup_mails_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('url_biblio_cluster', css_class='col-md-6'),
                        Column('can_edit_url_biblio_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('url_biblio_Greeter_cluster', css_class='col-md-6'),
                        Column('can_edit_url_biblio_Greeter_cluster', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                ),
                Tab(
                    _("Listes"),
                    Row(
                        Column(Field('experience_greeter'), css_class='col-md-11'),
                        Column('can_edit_experience_greeter', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('interest_center', css_class='col-md-11'),
                        Column('can_edit_interest_center', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                    Row(
                        Column('no_reply_greeter', css_class='col-md-11'),
                        Column('can_edit_no_reply_greeter', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('no_reply_visitor', css_class='col-md-11'),
                        Column('can_edit_no_reply_visitor', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                        Column('notoriety', css_class='col-md-11'),
                        Column('can_edit_notoriety', css_class='col-md-1 d-flex align-items-center justify-content-center'),
                    ),
                ),
            ),
            Submit('submit', _("Enregistrer"), css_class='btn-primary')
        )

    