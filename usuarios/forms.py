from django import forms
from .models import User

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha")
    email = forms.CharField(label="E-mail")

    class Meta:
        model = User
        fields = ['username', 'password']

    # Função clean para verificar se as senhas coincidem e excluir password_confirm
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem")
        
        # Exclui o campo de confirmação da senha antes de retornar os dados
        cleaned_data.pop("password_confirm", None)
        return cleaned_data