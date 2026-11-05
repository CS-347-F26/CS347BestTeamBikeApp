from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import User, Route, RouteFeedback

def index(request):
    """View function for home page of site."""

    # Generate counts of the users and routes
    num_users = User.objects.count()
    num_routes = Route.objects.count()

    context = {
        'num_users': num_users,
        'num_routes': num_routes,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


def route_selection(request):
    """Display routes so the user can choose one to review."""
    return render(
        request,
        'route_selection.html',
    )

def feedback_route_selection(request):
    """Display routes so the user can choose one to review."""
    return render(
        request,
        'feedback_route_selection.html',
    )


def feedback_form(request, route_id):
    """Display the feedback form for a selected route."""
    return render(
        request,
        'feedback_form.html',
        {'route_id': route_id},
    )


def post_ride_feedback_prompt(request, route_id):
    """Ask whether the user wants to give feedback after completing a route."""
    return render(
        request,
        'post_ride_feedback_prompt.html',
        {'route_id': route_id},
    )

def feedback_confirmation(request):
    """Display confirmation after feedback is submitted."""
    return render(
        request,
        'feedback__form_complete_confirmation.html',
    )