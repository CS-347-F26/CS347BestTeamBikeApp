from django import forms
from django.contrib.auth.forms import UserCreationForm

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
