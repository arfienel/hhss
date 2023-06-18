from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UserRegistrationForm(forms.Form):

    username = forms.CharField(widget=forms.TextInput(attrs={'class': ''}), label=_('Username'), max_length=100, min_length=3)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': ''}), label=_('Password'), min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': ''}), min_length=6, label=_('Password confirmation'))

    def clean(self):
        cd = self.cleaned_data
        print(User.objects.filter(username=cd.get('username')))
        if User.objects.filter(username=cd.get('username')):
            raise ValidationError(_('This username already taken'))
        if cd.get('password') != cd.get('password2'):
            raise ValidationError(_('Passwords didn`t match, try again'))
        else:
            return cd

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2',)