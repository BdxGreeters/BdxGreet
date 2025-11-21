from django.contrib import admin
from cluster.models import Cluster

from modeltranslation.admin import TranslationAdmin

admin.site.register(Cluster)


