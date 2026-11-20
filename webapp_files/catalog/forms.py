import json

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import RouteFeedback, User
from .route_import import SUPPORTED_COLORS, RouteImportError, parse_route_file


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
        fields = ["username", "comfortability", "location_sharing_enabled"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "comfortability": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 5}
            ),
        }
        labels = {
            "location_sharing_enabled": "Show my location on the map",
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


class RouteImportForm(forms.Form):
    """Upload a route drawn in geojson.io (or in the team's waypoints.json
    format). clean() parses the file; the view saves what it finds in
    cleaned_data["parsed"] (a route_import.ParseResult)."""

    MAX_BYTES = 1_000_000  # 1 MB is far more than a hand-drawn route needs

    file = forms.FileField(
        label="Route file",
        help_text="A .geojson or .json file, e.g. from geojson.io (Save → GeoJSON).",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".geojson,.json,application/geo+json,application/json",
                "class": "form-control",
            }
        ),
    )
    name = forms.CharField(
        label="Route name",
        required=False,
        max_length=100,
        help_text="Used when the file doesn't name the route.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    color = forms.ChoiceField(
        label="Color",
        required=False,
        choices=[("", "Use the file's color")]
        + [(color, color.title()) for color in SUPPORTED_COLORS],
        help_text="Used when the file doesn't give a color the app knows.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_file(self):
        """Check the size and turn the upload into JSON data."""
        upload = self.cleaned_data["file"]
        if upload.size > self.MAX_BYTES:
            raise forms.ValidationError("That file is too big (the limit is 1 MB).")
        try:
            # utf-8-sig also accepts files saved with a byte-order mark.
            return json.loads(upload.read().decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError):
            raise forms.ValidationError(
                "That file isn't valid JSON. Export it from geojson.io with "
                "Save → GeoJSON."
            )

    def __init__(self, *args, route=None, **kwargs):
        """Pass `route` to update that route instead of adding new ones:
        the file must then hold exactly one line, and the route's current
        name and color are kept when neither the file nor the form gives
        one."""
        super().__init__(*args, **kwargs)
        self.route = route
        if route is not None:
            self.fields["name"].help_text = "Leave blank to keep the file's or current name."
            self.fields["color"].choices = [("", "Use the file's or current color")] + [
                (color, color.title()) for color in SUPPORTED_COLORS
            ]

    def clean(self):
        """Parse the routes once all fields are in, since the name and color
        fields fill in what the file leaves out."""
        cleaned = super().clean()
        if "file" in cleaned:  # only when clean_file succeeded
            default_name = cleaned.get("name", "")
            default_color = cleaned.get("color", "")
            if self.route is not None:
                default_name = default_name or self.route.name
                default_color = default_color or self.route.color.lower()
            try:
                result = parse_route_file(
                    cleaned["file"],
                    default_name=default_name,
                    default_color=default_color,
                    # Only routes inside this city's area (see settings.py).
                    bounds=settings.ROUTE_AREA_BOUNDS,
                    area_name=settings.ROUTE_AREA_NAME,
                )
            except RouteImportError as error:
                self.add_error("file", str(error))
                return cleaned
            if self.route is not None and len(result.routes) != 1:
                self.add_error(
                    "file",
                    f"To update a route, upload a file with one line "
                    f"(this one has {len(result.routes)}).",
                )
                return cleaned
            cleaned["parsed"] = result
        return cleaned
