from django import forms
from django.core.exceptions import ValidationError
from .models import User

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Usuário', help_text=None)
    password = forms.CharField(widget=forms.PasswordInput, label="Senha", required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha", required=True)
    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este e-mail já está em uso.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise ValidationError("As senhas não coincidem.")
        
        cleaned_data.pop("password_confirm", None)
        return cleaned_data
