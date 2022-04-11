from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class UserLogoutForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')


class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')


class PasswordResetForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')
