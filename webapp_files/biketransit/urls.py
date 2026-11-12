"""
URL configuration for the biketransit project (the Bike Transit app).

This is the project's root URLconf (ROOT_URLCONF in settings.py). It only
wires up the top-level sections of the site; the app's own pages are listed
in catalog/urls.py.

    /admin/         Django admin site
    /accounts/      Login, logout and password pages (Django's built-in auth)
    /bike-routes/   The Bike Transit app itself (catalog/urls.py)
    /               Landing page (catalog.views.landing)

For more information on URL patterns see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path

# Use include() to pull in other URLconfs (the catalog app, Django's auth)
from django.urls import include

# Use static() to add URL mapping to serve static files during development (only)
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

from catalog.forms import StyledAuthenticationForm
from catalog import views as catalog_views

urlpatterns = [
    path("admin/", admin.site.urls),
]

# Login, logout and password change/reset pages from Django's auth app.
# These use the URL names "login", "logout", etc., and their templates live
# in templates/registration/.
urlpatterns += [
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(authentication_form=StyledAuthenticationForm),
        name="login",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]

# All Bike Transit pages (routes, feedback, locations, map, trips, profile).
# The Python app is still called "catalog"; only the URL prefix is "bike-routes".
urlpatterns += [
    path("bike-routes/", include("catalog.urls")),
]

# Landing page for visitors who open the bare domain. It lives here rather
# than in catalog/urls.py because "/" is outside the /bike-routes/ prefix.
urlpatterns += [
    path("", catalog_views.landing, name="landing"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
