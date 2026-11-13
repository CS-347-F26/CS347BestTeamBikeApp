from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AuditEvent,
    Comment,
    Location,
    Route,
    RouteWaypoint,
    User,
    Waypoint,
)

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


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "actor_username",
        "action",
        "object_type",
        "object_id",
        "object_label",
    )
    list_filter = ("action", "object_type", "timestamp")
    search_fields = ("actor_username", "object_type", "object_id", "object_label")
    date_hierarchy = "timestamp"
    readonly_fields = (
        "timestamp",
        "actor_user_id",
        "actor_username",
        "action",
        "object_type",
        "object_id",
        "object_label",
        "changes",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
