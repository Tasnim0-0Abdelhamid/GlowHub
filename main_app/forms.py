from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth import authenticate


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)

    def confirm_login_allowed(self, user):
        pass

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError(
                    "Invalid email or password.", code='invalid_login'
                )
            self.user_cache = user
        return self.cleaned_data
    


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone')

        error_messages = {
        'invalid_login': "Invalid email or password.",
        'inactive': "This account is inactive.",
    }

