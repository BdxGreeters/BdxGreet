from django import forms
from django.utils.translation import gettext_lazy as _

from users.models import CustomUser


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name','cellphone', 'lang_com')

        
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields= ('first_name', 'last_name','email','cellphone', 'lang_com')
        widgets = {'email':forms.TextInput(attrs={'readonly':'readonly'}),'first_name':forms.TextInput(attrs={'readonly':'readonly'}),'last_name':forms.TextInput(attrs={'readonly':'readonly'})}
    
   



        


