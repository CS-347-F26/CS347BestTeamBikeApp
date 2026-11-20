import logging
from math import isfinite

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.db import DatabaseError, connection
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_GET
from django.http import HttpResponse
from pathlib import Path

from .models import User, Route, RouteWaypoint, Location, RouteFeedback
from .forms import ProfileForm, RouteFeedbackForm, RouteSearchForm, SignUpForm

route_logger = logging.getLogger("catalog.routes")
health_logger = logging.getLogger("catalog.health")


def _log_route_loaded(request, route, source):
    user = getattr(request, "user", None)
    user_id = user.pk if user is not None and user.is_authenticated else "-"
    route_logger.info(
        "Route loaded",
        extra={
            "event": "route_loaded",
            "request_id": getattr(request, "request_id", "-"),
            "route_id": route.pk,
            "route_name": route.name,
            "source": source,
            "user_id": user_id,
        },
    )


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


def help_page(request):
    """Show in-app guidance for exploring Bike Transit."""
    return render(request, "help.html")


# --- Routes ---------------------------------------------------------------
# Generic class-based views: ListView/DetailView do the query for us, and
# DetailView returns a 404 automatically when no route has that pk.


class RouteListView(generic.ListView):
    """List all routes: /routes/"""

    model = Route
    template_name = "route_selection.html"

    def get_queryset(self):
        """Narrow the list with the search form's GET values:
        q         -> the text is contained (any case) in the fields below
        search_in -> which fields to search: "name", "color", or both.
                     None checked means both.
        official  -> only routes with is_official=True (works without q)
        comfort   -> route's comfort rating is at least this (1-5).
        Unrated routes (comfortability 0) drop out once a comfort is picked."""
        routes = super().get_queryset()
        self.form = RouteSearchForm(self.request.GET)
        self.query = ""
        self.search_in = []
        self.official = False
        self.min_comfort = None
        if self.form.is_valid():
            self.query = self.form.cleaned_data["q"].strip()
            self.search_in = self.form.cleaned_data["search_in"]
            self.official = self.form.cleaned_data["official"]
            self.min_comfort = self.form.cleaned_data["comfort"]
        if self.query:
            # One "contains" test per chosen field, joined with OR (|).
            match = Q()
            for field in self.search_in or ["name", "color"]:
                match |= Q(**{f"{field}__icontains": self.query})
            routes = routes.filter(match)
        if self.official:
            routes = routes.filter(is_official=True)
        if self.min_comfort is not None:
            routes = routes.filter(comfortability__gte=self.min_comfort)
        return routes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["query"] = self.query
        context["search_in"] = self.search_in
        context["official"] = self.official
        context["min_comfort"] = self.min_comfort
        context["is_filtered"] = (
            bool(self.query) or self.official or self.min_comfort is not None
        )
        # Plain-words list of the active filters for the "Showing n routes:
        # ..." line, e.g. ['matching "yellow" in name', "official only",
        # "comfort 3+"].
        summary = []
        if self.query:
            where = f" in {self.search_in[0]}" if len(self.search_in) == 1 else ""
            summary.append(f"matching “{self.query}”{where}")
        if self.official:
            summary.append("official only")
        if self.min_comfort is not None:
            summary.append(f"comfort {self.min_comfort}+")
        context["filter_summary"] = summary
        for route in context["object_list"]:
            _log_route_loaded(self.request, route, "list")
        return context


class RouteDetailView(generic.DetailView):
    """One route: /routes/<pk>/"""

    model = Route
    template_name = "route_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _log_route_loaded(self.request, self.object, "detail")
        return context


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


@login_required
def feedback_form(request, pk):
    """Feedback form for one route. GET shows the form; POST saves it.

    After a successful save we redirect back to this same page (so a refresh
    can't submit twice) and leave a one-time note in the session, which the
    next GET turns into the "thank you" popup."""
    route = get_object_or_404(Route, pk=pk)
    _log_route_loaded(request, route, "feedback_form")
    if request.method == "POST":
        form = RouteFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.route = route
            feedback.save()
            request.session["feedback_submitted"] = route.pk
            return redirect("feedback-form", pk=route.pk)
    else:
        form = RouteFeedbackForm()
    show_thanks = request.session.pop("feedback_submitted", None) == route.pk
    return render(
        request,
        "feedback_form.html",
        {"route": route, "form": form, "show_thanks": show_thanks},
    )


def post_ride_feedback_prompt(request, pk):
    """Ask whether the user wants to give feedback after completing a route."""
    route = get_object_or_404(Route, pk=pk)
    _log_route_loaded(request, route, "post_ride_prompt")
    return render(
        request,
        "post_ride_feedback_prompt.html",
        {"route": route},
    )


def feedback_confirmation(request, pk):
    """Display confirmation after feedback on a route is submitted."""
    route = get_object_or_404(Route, pk=pk)
    _log_route_loaded(request, route, "feedback_confirmation")
    return render(
        request,
        "feedback_form_complete_confirmation.html",
        {"route": route},
    )


# --- Locations ------------------------------------------------------------


class LocationListView(generic.ListView):
    """List all locations (stations / transfer points): /locations/"""

    model = Location
    template_name = "location_list.html"


class LocationDetailView(generic.DetailView):
    """One location: /locations/<pk>/"""

    model = Location
    template_name = "location_detail.html"


# --- Map, trips, profile (placeholders) -----------------------------------


def map_view(request):
    """Display locations and route geometry stored in the database."""
    locations = []
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

    named_waypoints = []
    named_waypoint_ids = set()
    routes = []
    route_waypoints = RouteWaypoint.objects.select_related("waypoint").order_by("order")
    for route in Route.objects.select_related("parent_route").prefetch_related(
        Prefetch("route_waypoints", queryset=route_waypoints)
    ):
        _log_route_loaded(request, route, "map")
        coordinates = []
        waypoint_ids = []
        for route_waypoint in route.route_waypoints.all():
            waypoint = route_waypoint.waypoint
            waypoint_ids.append(waypoint.pk)
            longitude = waypoint.longitude
            latitude = waypoint.latitude
            if (
                not isfinite(longitude)
                or not isfinite(latitude)
                or not -180 <= longitude <= 180
                or not -90 <= latitude <= 90
            ):
                raise ValueError(
                    f"Invalid coordinate in route {route.name!r}, "
                    f"waypoint {waypoint.pk}"
                )

            coordinates.append([longitude, latitude])
            if waypoint.name.strip() and waypoint.pk not in named_waypoint_ids:
                named_waypoints.append(
                    {
                        "name": waypoint.name.strip(),
                        "longitude": longitude,
                        "latitude": latitude,
                    }
                )
                named_waypoint_ids.add(waypoint.pk)

        if len(coordinates) >= 2:
            routes.append(
                {
                    "id": route.pk,
                    "name": route.name,
                    "color": route.color,
                    "comfortability": route.comfortability,
                    "route_type": route.route_type,
                    "is_official": route.is_official,
                    "parent_route": (
                        route.parent_route.name if route.parent_route_id else None
                    ),
                    "coordinates": coordinates,
                    "waypoint_ids": waypoint_ids,
                }
            )

    return render(
        request,
        "map.html",
        {
            "map_data": {
                "locations": locations,
                "routes": routes,
                "named_waypoints": named_waypoints,
            },
            "location_sharing_enabled": (
                request.user.is_authenticated
                and getattr(request.user, "location_sharing_enabled", False)
            ),
            "is_logged_in": request.user.is_authenticated,
        },
    )


@require_GET
def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        health_logger.exception(
            "Database health check failed",
            extra={
                "event": "health_check_failed",
                "request_id": getattr(request, "request_id", "-"),
            },
        )
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def trip_new(request):
    """Trip planner: choose a start and end station (placeholder)."""
    return render(request, "trip_new.html")


@login_required
def profile(request):
    """The logged-in rider's profile. Anonymous visitors are sent to login."""
    feedback = request.user.route_feedback.select_related("route")
    return render(
        request,
        "profile.html",
        {
            "recent_feedback": feedback[
                :3
            ],  # newest first (RouteFeedback.Meta.ordering)
            "feedback_count": feedback.count(),
        },
    )


@login_required
@transaction.atomic
def profile_edit(request):
    """Let the logged-in rider edit their own profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            previously_enabled = request.user.location_sharing_enabled
            user = form.save(commit=False)

            if user.location_sharing_enabled and not previously_enabled:
                # the user intentionally turned location sharing back on
                user.location_permission_asked = False
            elif not user.location_sharing_enabled:
                # the user turned off location sharing
                user.location_permission_asked = False

            user.save()

            messages.success(request, "Your profile was updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "profile_edit.html", {"form": form})


@login_required
@transaction.atomic
def profile_delete(request):
    """Ask for confirmation (GET), then delete the rider's own account (POST)."""
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account was deleted.")
        return redirect("index")
    return render(request, "profile_confirm_delete.html")


# --- The rider's own feedback (list / edit / delete) ----------------------
# Feedback is created on the route's feedback form (feedback_form above).
# These views let a rider manage what they wrote from their profile.
# Each lookup filters on user=request.user, so opening someone else's
# feedback gives a 404 (we don't even reveal that it exists).


@login_required
def profile_feedback_list(request):
    """All feedback the logged-in rider has left, newest first."""
    feedback_list = request.user.route_feedback.select_related("route")
    return render(
        request, "profile_feedback_list.html", {"feedback_list": feedback_list}
    )


@login_required
def profile_feedback_edit(request, pk):
    """Edit one of your own feedback entries. Reuses the feedback form page."""
    feedback = get_object_or_404(
        RouteFeedback.objects.select_related("route"), pk=pk, user=request.user
    )
    if request.method == "POST":
        form = RouteFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            messages.success(request, f"Your feedback on {feedback.route} was updated.")
            return redirect("profile-feedback-list")
    else:
        form = RouteFeedbackForm(instance=feedback)
    return render(
        request,
        "feedback_form.html",
        {"route": feedback.route, "form": form, "feedback": feedback},
    )


@login_required
def profile_feedback_delete(request, pk):
    """Ask for confirmation (GET), then delete one of your own feedback
    entries (POST)."""
    feedback = get_object_or_404(
        RouteFeedback.objects.select_related("route"), pk=pk, user=request.user
    )
    if request.method == "POST":
        route = feedback.route
        feedback.delete()
        messages.success(request, f"Your feedback on {route} was deleted.")
        return redirect("profile-feedback-list")
    return render(
        request, "profile_feedback_confirm_delete.html", {"feedback": feedback}
    )


# --- Sign up form -------------------------------------------------------


@transaction.atomic
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


@require_GET
def service_worker(request):
    worker_path = (
        Path(__file__).resolve().parent
        / "static"
        / "catalog"
        / "js"
        / "service-worker.js"
    )

    return HttpResponse(
        worker_path.read_text(),
        content_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )
