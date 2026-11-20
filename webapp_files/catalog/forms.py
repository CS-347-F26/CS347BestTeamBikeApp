from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import RouteFeedback, User


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


class RouteSearchForm(forms.Form):
    """Search and filter on the routes page, e.g.
    GET /routes/?q=yellow&search_in=name&official=on&comfort=3

    Every field is optional. A bad value (e.g. ?comfort=9 or ?search_in=zzz)
    makes the form invalid, and the view then just shows every route instead
    of crashing."""

    q = forms.CharField(label="Search routes", required=False, max_length=100)
    # Which route fields the search text is matched against. None checked
    # means both (see RouteListView.get_queryset).
    search_in = forms.MultipleChoiceField(
        label="Search in",
        choices=[("name", "Name"), ("color", "Color")],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    official = forms.BooleanField(label="Official routes only", required=False)
    comfort = forms.TypedChoiceField(
        label="Minimum comfort",
        choices=[(n, str(n)) for n in range(1, 6)],
        coerce=int,
        required=False,
        empty_value=None,
        widget=forms.RadioSelect,
    )


class RouteFeedbackForm(forms.ModelForm):
    """A rider's feedback on one route: a 1-5 comfort rating (5 = most
    comfortable) and optional comments. The view fills in user and route."""

    comfort_rating = forms.TypedChoiceField(
        label="Comfort rating",
        choices=[(n, str(n)) for n in range(1, 6)],
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={"required": "Pick a comfort rating from 1 to 5."},
    )

    class Meta:
        model = RouteFeedback
        fields = ["comfort_rating", "text"]
        labels = {"text": "Comments"}
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "What felt safe or unsafe? Busy roads, bike lanes, hills…",
                }
            ),
        }
