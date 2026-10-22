from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'title',
            'amount',
            'transaction_type',
            'category',
            'date',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Monthly salary',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '0.01',
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add optional notes',
                'rows': 3,
            }),
        }
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError(
                'Amount must be greater than zero.'
            )
        return amount