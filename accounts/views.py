from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from .forms import (
    LoginForm,
    CustomUserCreationForm,
    CustomUserChangeForm,
    ProfileForm,
    PasswordChangeCustomForm,
    AdminPasswordResetForm,
)
from .models import CustomUser


def admin_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'admin',
        login_url='/login/',
    )(view_func)
    return decorated_view


def pharmacist_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.role in ['admin', 'pharmacist'],
        login_url='/login/',
    )(view_func)
    return decorated_view


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    else:
        form = PasswordChangeCustomForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@admin_required
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    password_form = AdminPasswordResetForm()
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        password_form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            user = form.save()
            p1 = request.POST.get('password1', '')
            p2 = request.POST.get('password2', '')
            if p1 and p2 and p1 == p2:
                if password_form.is_valid():
                    user.set_password(password_form.cleaned_data['password1'])
                    user.save()
                    messages.success(request, f'User {user.username} updated and password changed.')
                else:
                    return render(request, 'accounts/user_form.html', {
                        'form': form, 'password_form': password_form, 'title': 'Edit User', 'object': user,
                    })
            else:
                messages.success(request, f'User {user.username} updated successfully.')
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)

    return render(request, 'accounts/user_form.html', {'form': form, 'password_form': password_form, 'title': 'Edit User', 'object': user})


@login_required
@admin_required
def user_reset_password(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, f'Password for {user.username} has been reset.')
            return redirect('user_list')
    else:
        form = AdminPasswordResetForm()
    return render(request, 'accounts/user_reset_password.html', {'form': form, 'user_obj': user})


@login_required
@admin_required
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'user': user})
