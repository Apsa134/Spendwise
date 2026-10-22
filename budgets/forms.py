
from django import forms
from .models import Budget

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month', 'year']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your budget amount',
                'min': '0.01',
                'step': '0.01',
            }),
            'month': forms.Select(attrs={
                'class': 'form-select',
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2100',
            }),
        }
    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if amount <= 0:
            raise forms.ValidationError(
                'Budget amount must be greater than zero.'
            )
        return amount
