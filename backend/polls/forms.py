from django import forms
from .models import Poll


class PollCreateForm(forms.ModelForm):
    question = forms.CharField(
        max_length=300,
        required=True,
        label="Anket Sorusu",
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input-lg',
            'placeholder': 'Örn: Bugün sinemaya mı gitsem, restorana mı?',
            'autocomplete': 'off',
            'maxlength': '300'
        })
    )
    duration = forms.TypedChoiceField(
        choices=Poll.DURATION_CHOICES,
        coerce=int,
        initial=24,
        required=True,
        label="Anket Süresi",
        widget=forms.Select(attrs={
            'class': 'form-input',
        })
    )

    class Meta:
        model = Poll
        fields = ('question',)
