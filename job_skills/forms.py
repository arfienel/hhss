from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'и тут короче пиши свои классы как обычно через запятую каждый класс внутри этой строки kekw'}), label='username', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': ''}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': ''}), label='password confirmation')
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'class': ''}))

    def clean(self):
        cd = self.cleaned_data

        if cd.get('password') != cd.get('password2'):
            raise ValidationError('Passwords didn`t  match')
        else:
            return cd

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)