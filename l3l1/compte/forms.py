from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=30, help_text='adresse mail valide', required=True)
    email = forms.EmailField(required=True)
    

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2'
        )