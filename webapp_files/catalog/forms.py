from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "comfortability"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "comfortability": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 5}
            ),
        }


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def get_invalid_login_error(self):
        """On a wrong username/password, mark both fields invalid and link
        them to the error message (id="login-error" in login.html) so screen
        readers announce why."""
        for field in self.fields.values():
            field.widget.attrs["aria-invalid"] = "true"
            field.widget.attrs["aria-describedby"] = "login-error"
        return super().get_invalid_login_error()
