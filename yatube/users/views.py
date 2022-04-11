from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import (CreationForm, UserLoginForm,
                    PasswordResetForm, UserLogoutForm)


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LoginView(CreateView):
    form_class = UserLoginForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/login.html'


class LogoutView(CreateView):
    form_class = UserLogoutForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/logout.html'


class PasswordResetView(CreateView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/password_reset_form.html'
