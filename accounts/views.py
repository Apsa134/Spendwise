
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegisterForm
from core.email_utils import send_email


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Send a welcome email to the new user
            if user.email:
                try:
                    send_email(
                        to_email=user.email,
                        subject='Welcome to SpendWise!',
                        html_content=f"""
                            <h2>Welcome to SpendWise, {user.username}!</h2>
                            <p>Your account has been created successfully.</p>
                            <p>You can now track your income and expenses,
                            manage your budgets, and monitor your spending.</p>
                            <p>Happy tracking!</p>
                            <p><strong>The SpendWise Team</strong></p>
                        """
                    )
                    messages.success(
                        request,
                        'Account created successfully! '
                        'A welcome email has been sent.'
                    )
                except Exception:
                    messages.warning(
                        request,
                        'Account created successfully, but the welcome '
                        'email could not be sent.'
                    )
            else:
                messages.success(
                    request,
                    'Account created successfully!'
                )

            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(
        request,
        'registration/register.html',
        {'form': form}
    )


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {
        'profile_user': request.user
    })


@login_required
def profile_edit(request):
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'accounts/profile_edit.html', {
        'profile_user': user
    })
