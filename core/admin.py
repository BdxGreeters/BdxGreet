from django.contrib import admin
from core.models import Email_Mailjet, LangueDeepL,InterestCenter, LangueParlee, Pays, No_show, Beneficiaire, Periode, TrancheAge
from core.models import Types_handicap, Language_communication, FieldPermission

admin.site.register(Email_Mailjet)
admin.site.register(LangueDeepL)
admin.site.register(InterestCenter)
admin.site.register(LangueParlee)
admin.site.register(Pays)
admin.site.register(No_show)
admin.site.register(Beneficiaire)
admin.site.register(Periode)
admin.site.register(TrancheAge)
admin.site.register(Types_handicap)
admin.site.register(Language_communication)
admin.site.register(FieldPermission)


