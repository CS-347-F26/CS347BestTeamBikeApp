from math import isfinite

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages

from .models import User, Route, Location, RouteFeedback
from .forms import ProfileForm, SignUpForm


def landing(request):
    """Landing page at the bare domain (/): a short intro with links into the app."""
    return render(request, "landing.html")


def index(request):
    """View function for home page of site."""

    # Generate counts of the users and routes
    num_users = User.objects.count()
    num_routes = Route.objects.count()

    context = {
        "num_users": num_users,
        "num_routes": num_routes,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, "index.html", context=context)


# --- Routes ---------------------------------------------------------------
# Generic class-based views: ListView/DetailView do the query for us, and
# DetailView returns a 404 automatically when no route has that pk.


class RouteListView(generic.ListView):
    """List all routes: /bike-routes/routes/"""

    model = Route
    template_name = "route_selection.html"


class RouteDetailView(generic.DetailView):
    """One route: /bike-routes/routes/<pk>/"""

    model = Route
    template_name = "route_detail.html"


# --- Route feedback -------------------------------------------------------
# These views take the route's pk from the URL and use get_object_or_404, so
# a missing route shows the 404 page instead of a broken form.


def feedback_route_selection(request):
    """Display routes so the user can choose one to review."""
    return render(
        request,
        "feedback_route_selection.html",
        {"route_list": Route.objects.all()},
    )


def feedback_form(request, pk):
    """Display the feedback form for a selected route (GET); the same URL
    will accept the submitted form (POST) once the form is built."""
    route = get_object_or_404(Route, pk=pk)
    return render(
        request,
        "feedback_form.html",
        {"route": route},
    )


def post_ride_feedback_prompt(request, pk):
    """Ask whether the user wants to give feedback after completing a route."""
    route = get_object_or_404(Route, pk=pk)
    return render(
        request,
        "post_ride_feedback_prompt.html",
        {"route": route},
    )


def feedback_confirmation(request, pk):
    """Display confirmation after feedback on a route is submitted."""
    route = get_object_or_404(Route, pk=pk)
    return render(
        request,
        "feedback_form_complete_confirmation.html",
        {"route": route},
    )


# --- Locations ------------------------------------------------------------


class LocationListView(generic.ListView):
    """List all locations (stations / transfer points): /bike-routes/locations/"""

    model = Location
    template_name = "location_list.html"


class LocationDetailView(generic.DetailView):
    """One location: /bike-routes/locations/<pk>/"""

    model = Location
    template_name = "location_detail.html"


# --- Map, trips, profile (placeholders) -----------------------------------


def map_view(request):
    """Display Harrisonburg locations and straight-line route connections."""
    locations = []
    valid_location_ids = set()
    for location in Location.objects.all():
        if (
            isfinite(location.latitude)
            and isfinite(location.longitude)
            and -90 <= location.latitude <= 90
            and -180 <= location.longitude <= 180
        ):
            locations.append(
                {
                    "id": location.pk,
                    "name": location.name,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
            )
            valid_location_ids.add(location.pk)

    routes = [
        {
            "name": route.name,
            "color": route.color,
            "start": [
                route.start_location.latitude,
                route.start_location.longitude,
            ],
            "end": [route.end_location.latitude, route.end_location.longitude],
        }
        for route in Route.objects.select_related("start_location", "end_location")
        if route.start_location_id in valid_location_ids
        and route.end_location_id in valid_location_ids
    ]

    return render(
        request,
        "map.html",
        {"map_data": {"locations": locations, "routes": routes}},
    )


def trip_new(request):
    """Trip planner: choose a start and end station (placeholder)."""
    return render(request, "trip_new.html")


@login_required
def profile(request):
    """The logged-in rider's profile. Anonymous visitors are sent to login."""
    return render(request, "profile.html")


@login_required
def profile_edit(request):
    """Let the logged-in rider edit their own profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "profile_edit.html", {"form": form})


@login_required
def profile_delete(request):
    """Ask for confirmation (GET), then delete the rider's own account (POST)."""
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account was deleted.")
        return redirect("index")
    return render(request, "profile_confirm_delete.html")


# --- Sign up form -------------------------------------------------------


def signup(request):
    """Create a new rider account, then log them in."""
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})
