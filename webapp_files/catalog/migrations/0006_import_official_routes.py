import json
from pathlib import Path

from django.db import migrations


def import_official_routes(apps, schema_editor):
    Route = apps.get_model("catalog", "Route")
    Waypoint = apps.get_model("catalog", "Waypoint")
    RouteWaypoint = apps.get_model("catalog", "RouteWaypoint")
    database = schema_editor.connection.alias
    data_path = Path(__file__).resolve().parents[2] / "waypoints.json"

    with data_path.open(encoding="utf-8") as data_file:
        groups = json.load(data_file)
    features = [feature for group in groups for feature in group.get("features", [])]
    main_features = [
        feature for feature in features if feature["geometry"]["type"] == "MainRoute"
    ]
    main_routes = {}
    for feature in main_features:
        route_name = feature.get("name") or feature.get("type")
        route, created = Route.objects.using(database).get_or_create(
            name=route_name,
            is_official=True,
            defaults={
                "color": feature["color"].lower(),
                "route_type": "main",
            },
        )
        if not created:
            route.color = feature["color"].lower()
            route.route_type = "main"
            route.parent_route = None
            route.save(
                using=database,
                update_fields=["color", "route_type", "parent_route"],
            )
        main_routes[route_name] = route

    waypoint_by_coordinates = {}
    for waypoint in Waypoint.objects.using(database).all():
        waypoint_by_coordinates.setdefault(
            (waypoint.longitude, waypoint.latitude), waypoint
        )

    for feature in features:
        route_type = feature["geometry"]["type"]
        if route_type == "MainRoute":
            continue
        if route_type != "SubRoute":
            raise ValueError(f"Unknown predefined route type: {route_type}")

        route_name = feature.get("name") or feature.get("type")
        parent_names = [
            name for name in main_routes if route_name.startswith(f"{name} ")
        ]
        if len(parent_names) != 1:
            raise ValueError(
                f"Could not identify one main route for subroute {route_name!r}"
            )
        parent_route = main_routes[parent_names[0]]
        route, created = Route.objects.using(database).get_or_create(
            name=route_name,
            is_official=True,
            defaults={
                "color": feature["color"].lower(),
                "route_type": "subroute",
                "parent_route": parent_route,
            },
        )
        if not created:
            route.color = feature["color"].lower()
            route.route_type = "subroute"
            route.parent_route = parent_route
            route.save(
                using=database,
                update_fields=["color", "route_type", "parent_route"],
            )

    for feature in features:
        route_name = feature.get("name") or feature.get("type")
        route = Route.objects.using(database).get(name=route_name, is_official=True)
        if RouteWaypoint.objects.using(database).filter(route=route).exists():
            continue

        for order, point in enumerate(feature["geometry"]["coordinates"]):
            longitude, latitude = point[:2]
            name = point[2] if len(point) > 2 and point[2] else ""
            coordinates = (longitude, latitude)
            waypoint = waypoint_by_coordinates.get(coordinates)
            if waypoint is None:
                waypoint = Waypoint.objects.using(database).create(
                    name=name,
                    longitude=longitude,
                    latitude=latitude,
                )
                waypoint_by_coordinates[coordinates] = waypoint
            elif name and not waypoint.name:
                waypoint.name = name
                waypoint.save(using=database, update_fields=["name"])
            RouteWaypoint.objects.using(database).create(
                route=route,
                waypoint=waypoint,
                order=order,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_auditevent"),
    ]

    operations = [
        migrations.RunPython(import_official_routes, migrations.RunPython.noop),
    ]
