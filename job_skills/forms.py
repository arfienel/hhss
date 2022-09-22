from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.Form):
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput(), label='password confirmation')
    email = forms.EmailField(max_length=254, widget=forms.EmailInput())

    def clean(self):
        cd = self.cleaned_data

        if cd.get('password') != cd.get('password2'):
            raise ValidationError('Passwords didn`t  match')
        else:
            return cd

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)