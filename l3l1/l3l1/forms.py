from django import forms
from django.contrib.auth.models import User

class InscriptionForm(forms.ModelForm):
    class Meta:
            model = User
            fields = ('username', 'email', 'password')