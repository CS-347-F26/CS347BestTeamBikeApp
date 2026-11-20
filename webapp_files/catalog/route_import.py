"""Turn an uploaded route file into Route + Waypoint rows.

Two file shapes are accepted:

1. Standard GeoJSON, as saved by geojson.io (Save -> GeoJSON): a
   FeatureCollection (or a single Feature / bare geometry) whose lines are
   LineString or MultiLineString. The route's name and color come from the
   feature's `properties.name` and `properties.color`.

2. The team's own format, used by waypoints.json: a list of
   {"type": "PredefinedRoute", "features": [...]} groups (or one group).
   Each feature has a top-level `name` (or `type`) and `color`, and
   `geometry.type` is "MainRoute" or "SubRoute". A coordinate may carry a
   third value: the waypoint's name.

Parsing (parse_route_file) is kept apart from saving (save_routes) so the
rules can be tested without the database or an upload.
"""

from dataclasses import dataclass, field
from math import isfinite

from django.db import transaction

from .models import Route, RouteWaypoint, Waypoint

# Colors that have a `.route-color--<color>` class at the end of main.css.
# Add a color here when you add its CSS class.
SUPPORTED_COLORS = [
    "red",
    "yellow",
    "black",
    "purple",
    "blue",
    "green",
    "orange",
    "pink",
    "maroon",
    "indigo",
]

LINE_TYPES = {"LineString", "MultiLineString", "MainRoute", "SubRoute"}


class RouteImportError(ValueError):
    """The file can't be imported; the message is shown to the rider."""


@dataclass
class ParsedRoute:
    name: str
    color: str
    route_type: str = Route.Type.MAIN
    # (longitude, latitude, waypoint name) from start to end
    points: list = field(default_factory=list)


@dataclass
class ParseResult:
    routes: list
    skipped: int = 0  # features that aren't lines (points, polygons, ...)


def parse_route_file(
    data, default_name="", default_color="", bounds=None, area_name="the map area"
):
    """Read already-decoded JSON `data` and return a ParseResult.

    `default_name` / `default_color` (from the upload form) fill in routes
    whose file doesn't give a name or a supported color. When `bounds`
    (west, south, east, north) is given, every point must lie inside it;
    `area_name` names that box in the error message."""
    features = _collect_features(data)
    default_color = (default_color or "").strip().lower()

    routes = []
    skipped = 0
    for index, feature in enumerate(features, start=1):
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        if geometry_type not in LINE_TYPES:
            skipped += 1
            continue

        properties = feature.get("properties") or {}
        label = _first_text(feature.get("name"), properties.get("name"))
        where = f"Route “{label}”" if label else f"Line {index}"
        points = _read_points(geometry, where)
        if bounds is not None:
            _check_in_area(points, bounds, area_name, where)

        color = _first_text(feature.get("color"), properties.get("color")).lower()
        if not color:
            # geojson.io's style editor saves a hex "stroke"; we only know
            # named colors, so a hex value falls back to the form's choice.
            stroke = _first_text(properties.get("stroke")).lower()
            color = stroke if stroke in SUPPORTED_COLORS else default_color
        if not color:
            raise RouteImportError(
                f"{where} has no color. Pick a color on the form, or add "
                f'"color": "red" (for example) to its properties.'
            )
        if color not in SUPPORTED_COLORS:
            raise RouteImportError(
                f"{where} uses the color “{color}”, which the app doesn't "
                f"support. Use one of: {', '.join(SUPPORTED_COLORS)}."
            )

        name = _first_text(feature.get("name"), properties.get("name"))
        if not name and geometry_type in {"MainRoute", "SubRoute"}:
            # In waypoints.json some features keep their name in "type".
            name = _first_text(feature.get("type"))
        routes.append(
            ParsedRoute(
                name=name,
                color=color,
                route_type=(
                    Route.Type.SUBROUTE
                    if geometry_type == "SubRoute"
                    else Route.Type.MAIN
                ),
                points=points,
            )
        )

    if not routes:
        raise RouteImportError(
            "The file has no route lines. In geojson.io, draw a line "
            "(not a point or shape) and save it as GeoJSON."
        )

    # Give unnamed routes the form's name (numbered if there are several).
    unnamed = [route for route in routes if not route.name]
    base_name = (default_name or "").strip() or "Imported route"
    for number, route in enumerate(unnamed, start=1):
        route.name = base_name if len(unnamed) == 1 else f"{base_name} {number}"
    for route in routes:
        route.name = route.name[: Route._meta.get_field("name").max_length]

    return ParseResult(routes=routes, skipped=skipped)


@transaction.atomic
def save_routes(parsed_routes, user):
    """Create user-made routes (and their ordered waypoints) for `user`.

    A subroute is attached to the main route of the same color from the same
    file (the rule migration 0006 uses). If the file has no such main route,
    the subroute is saved as a main route instead. Returns the new routes."""
    main_by_color = {}
    created = {}  # index in the file -> new Route
    # Save main routes first so subroutes can find their parent.
    indexed = sorted(
        enumerate(parsed_routes),
        key=lambda pair: pair[1].route_type != Route.Type.MAIN,
    )
    for index, parsed in indexed:
        parent = None
        route_type = Route.Type.MAIN
        if parsed.route_type == Route.Type.SUBROUTE:
            parent = main_by_color.get(parsed.color)
            if parent is not None:
                route_type = Route.Type.SUBROUTE
        route = Route.objects.create(
            name=parsed.name,
            color=parsed.color,
            is_official=False,
            created_by=user,
            route_type=route_type,
            parent_route=parent,
        )
        if route_type == Route.Type.MAIN:
            main_by_color.setdefault(parsed.color, route)
        _add_waypoints(route, parsed.points)
        created[index] = route

    # Return them in the order they had in the file.
    return [created[index] for index in range(len(parsed_routes))]


# --- helpers ----------------------------------------------------------------


def _collect_features(data):
    """Flatten any accepted file shape into a list of feature dicts."""
    if isinstance(data, list):
        # The team's format: a list of PredefinedRoute groups.
        features = []
        for group in data:
            if not isinstance(group, dict):
                raise RouteImportError("The file's list should contain objects.")
            features.extend(_collect_features(group))
        return features
    if not isinstance(data, dict):
        raise RouteImportError("The file isn't a GeoJSON object.")

    kind = data.get("type")
    if "features" in data:  # FeatureCollection or PredefinedRoute group
        features = data["features"]
        if not isinstance(features, list):
            raise RouteImportError("“features” should be a list.")
        return [feature for feature in features if isinstance(feature, dict)]
    if kind == "Feature" or "geometry" in data:
        return [data]
    if kind in LINE_TYPES:  # a bare geometry
        return [{"geometry": data}]
    raise RouteImportError(
        "The file isn't GeoJSON. Export it from geojson.io with Save → GeoJSON."
    )


def _read_points(geometry, where):
    """Return [(lon, lat, name)] for a line geometry, checking every point."""
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list):
        raise RouteImportError(f"{where} has no coordinates.")
    if geometry.get("type") == "MultiLineString":
        # Join the parts end to end, in the order they appear.
        coordinates = [
            point for part in coordinates if isinstance(part, list) for point in part
        ]

    points = []
    for number, point in enumerate(coordinates, start=1):
        if not isinstance(point, list) or len(point) < 2:
            raise RouteImportError(
                f"{where}, point {number} isn't [longitude, latitude]."
            )
        longitude, latitude = point[0], point[1]
        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in (longitude, latitude)
        ):
            raise RouteImportError(f"{where}, point {number} has a non-number value.")
        if not (
            isfinite(longitude)
            and isfinite(latitude)
            and -180 <= longitude <= 180
            and -90 <= latitude <= 90
        ):
            raise RouteImportError(
                f"{where}, point {number} is off the map ({longitude}, {latitude}). "
                "GeoJSON lists longitude first, then latitude."
            )
        # Team format: an optional third value is the waypoint's name.
        # (In standard GeoJSON a third number is elevation, so only text counts.)
        name = point[2].strip() if len(point) > 2 and isinstance(point[2], str) else ""
        points.append((float(longitude), float(latitude), name))

    if len(points) < 2:
        raise RouteImportError(f"{where} needs at least 2 points.")
    return points


def _check_in_area(points, bounds, area_name, where):
    """Reject the route if any point is outside the (west, south, east,
    north) box, naming the first point that is out."""
    west, south, east, north = bounds
    outside = [
        (number, longitude, latitude)
        for number, (longitude, latitude, _) in enumerate(points, start=1)
        if not (west <= longitude <= east and south <= latitude <= north)
    ]
    if outside:
        number, longitude, latitude = outside[0]
        count = len(outside)
        raise RouteImportError(
            f"{where} goes outside {area_name}: {count} of its {len(points)} "
            f"points {'are' if count != 1 else 'is'} out, starting with point "
            f"{number} ({longitude}, {latitude}). Only routes in {area_name} "
            "can be imported."
        )


def _add_waypoints(route, points):
    """Create the route's RouteWaypoints, reusing a waypoint that already
    sits at exactly the same spot (as migration 0006 does)."""
    for order, (longitude, latitude, name) in enumerate(points):
        waypoint = Waypoint.objects.filter(
            longitude=longitude, latitude=latitude
        ).first()
        if waypoint is None:
            waypoint = Waypoint.objects.create(
                name=name, longitude=longitude, latitude=latitude
            )
        elif name and not waypoint.name:
            waypoint.name = name
            waypoint.save(update_fields=["name"])
        RouteWaypoint.objects.create(route=route, waypoint=waypoint, order=order)


def _first_text(*values):
    """The first value that is a non-blank string, stripped; else ""."""
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


# --- export -----------------------------------------------------------------


def route_to_geojson(route):
    """One route as a standard GeoJSON FeatureCollection (opens in
    geojson.io, and parse_route_file can import it again).

    The first feature is the route's line, with its name and color in
    `properties`. Each named waypoint is added as a Point feature so its
    name shows up in geojson.io; importing skips points, so they don't
    change the route."""
    route_waypoints = route.route_waypoints.select_related("waypoint")
    waypoints = [route_waypoint.waypoint for route_waypoint in route_waypoints]
    features = [
        {
            "type": "Feature",
            "properties": {
                "name": route.name,
                "color": route.color.lower(),
                "route_type": route.route_type,
                "parent_route": route.parent_route.name if route.parent_route_id else None,
                "is_official": route.is_official,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[w.longitude, w.latitude] for w in waypoints],
            },
        }
    ]
    features += [
        {
            "type": "Feature",
            "properties": {"name": w.name},
            "geometry": {"type": "Point", "coordinates": [w.longitude, w.latitude]},
        }
        for w in waypoints
        if w.name.strip()
    ]
    return {"type": "FeatureCollection", "features": features}
