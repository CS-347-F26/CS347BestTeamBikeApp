import pathlib

# Sanity check: this is the Bike Transit app's URLconf, catalog/urls.py.
# It is easy to confuse with the project-level biketransit/urls.py, so make
# sure this file sits next to the app's models.py and not next to settings.py.
_this_dir = pathlib.Path(__file__).resolve().parent
assert not (
    _this_dir / "settings.py"
).exists(), "catalog/urls.py should NOT have a sibling named settings.py"
assert (
    _this_dir / "models.py"
).exists(), "catalog/urls.py should have a sibling named models.py"

from django.urls import path
from . import views

# Every path below is mounted under /bike-routes/ (see biketransit/urls.py).
# Conventions: plural nouns for collections (routes/, locations/), <int:pk>
# for one object, and pages that belong to a route nested under that route.
urlpatterns = [
    # Home page: /bike-routes/
    path("", views.index, name="index"),
]

# Routes (the color-coded bike lines): list and detail
urlpatterns += [
    path("routes/", views.RouteListView.as_view(), name="route-list"),
    path("routes/<int:pk>/", views.RouteDetailView.as_view(), name="route-detail"),
]

# Feedback on a route, nested under that route.
# The form page handles both GET (show the form) and POST (submit it).
urlpatterns += [
    path(
        "feedback/",
        views.feedback_route_selection,
        name="feedback-route-selection",
    ),
    path(
        "routes/<int:pk>/feedback/",
        views.feedback_form,
        name="feedback-form",
    ),
    path(
        "routes/<int:pk>/feedback/thanks/",
        views.feedback_confirmation,
        name="feedback-confirmation",
    ),
    path(
        "routes/<int:pk>/complete/",
        views.post_ride_feedback_prompt,
        name="post-ride-feedback-prompt",
    ),
]

# Locations (stations / transfer points): list and detail
urlpatterns += [
    path("locations/", views.LocationListView.as_view(), name="location-list"),
    path(
        "locations/<int:pk>/",
        views.LocationDetailView.as_view(),
        name="location-detail",
    ),
]

# Schematic map and trip planner
urlpatterns += [
    path("map/", views.map_view, name="map"),
    path("trips/new/", views.trip_new, name="trip-new"),
]

# The logged-in rider's profile
urlpatterns += [
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile-edit"),
]

# Account creation
urlpatterns += [
    path("signup/", views.signup, name="signup"),
]
