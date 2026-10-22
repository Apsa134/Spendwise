from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
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
