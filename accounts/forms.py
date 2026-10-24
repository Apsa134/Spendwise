from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.utils.html import escape
from core.email_utils import send_email


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
        })
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
        })
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
        })
    )

    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class BrevoPasswordResetForm(PasswordResetForm):

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        username = escape(context['user'].get_username())

        reset_url = (
            f"{context['protocol']}://{context['domain']}"
            f"/accounts/reset/{context['uid']}/{context['token']}/"
        )

        html_content = f"""
            <div style="font-family: Arial, sans-serif;
                        max-width: 600px; margin: auto; padding: 24px;">
                <h2 style="color: #087f5b;">
                    Reset Your SpendWise Password
                </h2>

                <p>Hello {username},</p>

                <p>
                    We received a request to reset your SpendWise
                    account password.
                </p>

                <p>
                    Click the button below to create a new password.
                </p>

                <p style="margin: 28px 0;">
                    <a href="{reset_url}"
                       style="background-color: #087f5b;
                              color: white; padding: 12px 22px;
                              text-decoration: none; border-radius: 6px;">
                        Reset Password
                    </a>
                </p>

                <p>
                    If you didn't request this, you can safely ignore
                    this email.
                </p>

                <p>The SpendWise Team</p>
            </div>
        """

        send_email(
            to_email=to_email,
            subject="Reset Your SpendWise Password",
            html_content=html_content,
        )
