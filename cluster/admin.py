from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from cluster.models import Cluster, Experience_Greeter, InterestCenter, Notoriety, Reason_No_Response_Greeter, Reason_No_Response_Visitor


admin.site.register(Cluster)
admin.site.register(Experience_Greeter)
admin.site.register(InterestCenter)
admin.site.register(Notoriety)
admin.site.register(Reason_No_Response_Greeter)
admin.site.register(Reason_No_Response_Visitor)

