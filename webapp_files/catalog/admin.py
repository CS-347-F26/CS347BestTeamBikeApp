from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Comment, Location, Route, User

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


admin.site.register(Route)
admin.site.register(Location)
admin.site.register(Comment)
