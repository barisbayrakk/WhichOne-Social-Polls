from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="E-posta Adresi",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'ornek@eposta.com',
            'autocomplete': 'email',
        })
    )
    username = forms.CharField(
        required=True,
        label="Kullanıcı Adı",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'kullaniciadi',
            'autocomplete': 'username',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-input'
            if field_name == 'password1':
                field.widget.attrs['placeholder'] = 'En az 6 karakterli güçlü bir parola'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Parolanızı tekrar girin'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kullanımda.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Kullanıcı Adı veya E-posta",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Kullanıcı adı veya e-posta adresinizi girin',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Parolanızı girin',
            'autocomplete': 'current-password',
        })
    )
