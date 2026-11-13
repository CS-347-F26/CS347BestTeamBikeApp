from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Comment, Location, Route, RouteWaypoint, User, Waypoint

# Register your models here.


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Show our extra User fields on the admin edit page.
    fieldsets = UserAdmin.fieldsets + (
        (
            "Bike app",
            {
                "fields": (
                    "comfortability",
                    "prev_routes",
                    "saved_routes",
                    "marked_locations",
                )
            },
        ),
    )
    filter_horizontal = UserAdmin.filter_horizontal + (
        "prev_routes",
        "saved_routes",
        "marked_locations",
    )


class RouteWaypointInline(admin.TabularInline):
    """Lets admins add waypoints (with their order) right on a route's page."""

    model = RouteWaypoint
    extra = 1


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    inlines = [RouteWaypointInline]
    list_display = ("name", "color", "is_official", "route_type", "parent_route")
    list_filter = ("is_official", "route_type")
    search_fields = ("name",)


@admin.register(Waypoint)
class WaypointAdmin(admin.ModelAdmin):
    inlines = [RouteWaypointInline]
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name",)


admin.site.register(Location)
admin.site.register(Comment)
