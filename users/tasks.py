from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from core.models import Email_Mailjet
from core.tasks import send_email_mailjet
from users.models import CustomUser


###################################################################################################
# Fonction permettant d'initialiser ou réinitialiser le mot de passe
def reset_password (user_id, domain, template_mailjet_id):
    template_mailjet_id = template_mailjet_id
    user = CustomUser.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    creation_link = f"http://{domain}{path}"
    recipient_email= user.email
    recipient_name =user.first_name + ' ' + user.last_name
    vars ={'url_password': creation_link,'user_first_name' : user.first_name}
    send_email_mailjet.delay(recipient_email, recipient_name,template_mailjet_id, vars)
###################################################################################################

