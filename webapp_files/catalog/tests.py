import json
from unittest.mock import patch

from django.db import IntegrityError
from django.db.utils import DatabaseError
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import AuditEvent, Location, Route, RouteWaypoint, User, Waypoint
from .log_formatters import JSONFormatter


class NotFoundPageTests(TestCase):
    """Rubric B60: invalid URLs show a custom 404 page.

    The test runner always runs with DEBUG off, which is when Django uses
    templates/404.html, so this checks what real visitors would see.
    """

    def test_unknown_url_returns_custom_404(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(
            response, "Sorry! This page was not found.", status_code=404
        )


class UrlRoutingTests(TestCase):
    """Rubric B80: clean, RESTful URLs.

    Checks that every URL name maps to the readable path we expect, that each
    page loads, and that pages for a missing route or location return 404.
    """

    @classmethod
    def setUpTestData(cls):
        cls.start = Location.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )
        cls.end = Location.objects.create(
            name="JMU Quad", latitude=38.438, longitude=-78.871
        )
        cls.route = Route.objects.create(
            name="Red Line",
            color="red",
            start_location=cls.start,
            end_location=cls.end,
        )
        cls.missing_pk = 9999

    def test_url_names_reverse_to_expected_paths(self):
        r, loc = self.route.pk, self.start.pk
        expected = {
            ("landing", ()): "/",
            ("index", ()): "/home/",
            ("route-list", ()): "/routes/",
            ("route-detail", (r,)): f"/routes/{r}/",
            ("feedback-route-selection", ()): "/feedback/",
            ("feedback-form", (r,)): f"/routes/{r}/feedback/",
            (
                "feedback-confirmation",
                (r,),
            ): f"/routes/{r}/feedback/thanks/",
            ("post-ride-feedback-prompt", (r,)): f"/routes/{r}/complete/",
            ("location-list", ()): "/locations/",
            ("location-detail", (loc,)): f"/locations/{loc}/",
            ("map", ()): "/map/",
            ("trip-new", ()): "/trips/new/",
            ("profile", ()): "/profile/",
            ("login", ()): "/accounts/login/",
        }
        for (name, args), path in expected.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), path)

    def test_route_get_absolute_url(self):
        self.assertEqual(self.route.get_absolute_url(), f"/routes/{self.route.pk}/")

    def test_root_shows_landing_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")
        self.assertContains(response, f'href="{reverse("landing")}">Home</a>')

    def test_public_pages_load(self):
        r, loc = self.route.pk, self.start.pk
        pages = [
            ("landing", ()),
            ("index", ()),
            ("route-list", ()),
            ("route-detail", (r,)),
            ("feedback-route-selection", ()),
            ("feedback-form", (r,)),
            ("feedback-confirmation", (r,)),
            ("post-ride-feedback-prompt", (r,)),
            ("location-list", ()),
            ("location-detail", (loc,)),
            ("map", ()),
            ("trip-new", ()),
            ("login", ()),
        ]
        for name, args in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)

    def test_missing_ids_return_404(self):
        names = [
            "route-detail",
            "feedback-form",
            "feedback-confirmation",
            "post-ride-feedback-prompt",
            "location-detail",
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=[self.missing_pk]))
                self.assertEqual(response.status_code, 404)

    def test_old_url_prefixes_are_gone(self):
        for path in ("/catalog/routes/", "/bike-routes/", "/bike-routes/map/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response,
            "/accounts/login/?next=/profile/",
            fetch_redirect_response=False,
        )

    def test_profile_loads_when_logged_in(self):
        User.objects.create_user(username="rider", password="test-pass-123")
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)


class MapViewTests(TestCase):
    def test_map_uses_ordered_database_waypoints(self):
        start = Location.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )
        end = Location.objects.create(
            name="JMU Quad", latitude=38.438, longitude=-78.871
        )
        route = Route.objects.create(
            name="Red Line",
            color="red",
            is_official=False,
            start_location=start,
            end_location=end,
        )
        first = Waypoint.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )
        middle = Waypoint.objects.create(latitude=38.443, longitude=-78.870)
        last = Waypoint.objects.create(
            name="JMU Quad", latitude=38.438, longitude=-78.871
        )
        RouteWaypoint.objects.create(route=route, waypoint=last, order=2)
        RouteWaypoint.objects.create(route=route, waypoint=first, order=0)
        RouteWaypoint.objects.create(route=route, waypoint=middle, order=1)

        response = self.client.get(reverse("map"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="bike-map"')
        self.assertContains(response, "Route glossary")
        self.assertContains(response, "min-height: 360px")
        self.assertContains(response, "tiles.openfreemap.org/styles/liberty")
        self.assertContains(response, "maplibre-gl@6.17.0")
        self.assertContains(response, "OpenStreetMap contributors")
        map_data = response.context["map_data"]
        self.assertEqual(
            map_data["locations"],
            [
                {
                    "id": start.pk,
                    "name": "Court Square",
                    "latitude": 38.449,
                    "longitude": -78.869,
                },
                {
                    "id": end.pk,
                    "name": "JMU Quad",
                    "latitude": 38.438,
                    "longitude": -78.871,
                },
            ],
        )
        self.assertEqual(
            next(route for route in map_data["routes"] if route["name"] == "Red Line"),
            {
                "name": "Red Line",
                "color": "red",
                "route_type": "main",
                "is_official": False,
                "parent_route": None,
                "coordinates": [
                    [-78.869, 38.449],
                    [-78.870, 38.443],
                    [-78.871, 38.438],
                ],
            },
        )
        west_side = next(
            route for route in map_data["routes"] if route["name"] == "West Side"
        )
        self.assertEqual(west_side["route_type"], "main")
        self.assertEqual(west_side["color"], "green")
        self.assertEqual(west_side["coordinates"][0], [-78.8824499, 38.482479])
        self.assertEqual(west_side["coordinates"][-1], [-78.9007344, 38.4342646])
        self.assertContains(response, 'style="color: green"')
        self.assertContains(response, 'style="color: #806000"')
        glossary = (
            response.content.decode()
            .split('<section class="route-glossary"', 1)[1]
            .split("</section>", 1)[0]
        )
        for route_name in (
            "West Side",
            "Friendly City Trail",
            "Brewery Loop",
            "Pleasant Hill",
            "Memorial",
        ):
            self.assertIn(route_name, glossary)
        self.assertNotIn("Subroute", glossary)
        self.assertNotIn("West Side Emu", glossary)
        self.assertIn(
            {
                "name": "Willow Run Rd",
                "longitude": -78.8824499,
                "latitude": 38.482479,
            },
            map_data["named_waypoints"],
        )
        self.assertIn(
            {
                "name": "Court Square",
                "longitude": -78.869,
                "latitude": 38.449,
            },
            map_data["named_waypoints"],
        )
        self.assertTrue(
            all(waypoint["name"] for waypoint in map_data["named_waypoints"])
        )
        self.assertTrue(
            all(
                len(point) == 2
                for route in map_data["routes"]
                for point in route["coordinates"]
            )
        )

    def test_official_routes_and_subroute_parents_are_seeded(self):
        routes = Route.objects.filter(is_official=True)

        self.assertEqual(routes.count(), 10)
        west_side = routes.get(name="West Side")
        emu_subroute = routes.get(name="West Side Emu Subroute")
        self.assertEqual(west_side.route_type, Route.Type.MAIN)
        self.assertEqual(emu_subroute.route_type, Route.Type.SUBROUTE)
        self.assertEqual(emu_subroute.parent_route, west_side)
        self.assertGreater(west_side.route_waypoints.count(), 1)
        self.assertEqual(
            west_side.route_waypoints.first().waypoint.name, "Willow Run Rd"
        )


class SignUpTests(TestCase):
    def setUp(self):
        self.url = reverse("signup")

    def test_signup_page_loads(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            self.url,
            {
                "username": "biker_24",
                "password1": "I_lov3-bIkIng43",
                "password2": "I_lov3-bIkIng43",
            },
        )
        self.assertRedirects(
            response, reverse("profile"), fetch_redirect_response=False
        )
        user = User.objects.get(username="biker_24")
        self.assertIn("_auth_user_id", self.client.session)
        event = AuditEvent.objects.get(
            object_type="catalog.User",
            object_id=str(user.pk),
            action=AuditEvent.Action.CREATE,
        )
        self.assertEqual(event.actor_username, "Anonymous")

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post(
            self.url,
            {
                "username": "biker_24",
                "password1": "I_lov3-bIkIng43",
                "password2": "different-pass-99",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="biker_24").exists())


class ReadTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )

    def test_location_list_shows_records(self):
        response = self.client.get(reverse("location-list"))
        self.assertContains(response, "Court Square")

    def test_location_detail_shows_record(self):
        response = self.client.get(reverse("location-detail", args=[self.location.pk]))
        self.assertContains(response, "Court Square")
        self.assertContains(response, "38.449")

    def test_profile_shows_user_data(self):
        user = User.objects.create_user(
            username="biker_24", password="test-pass-123", comfortability=2
        )
        user.marked_locations.add(self.location)
        self.client.login(username="biker_24", password="test-pass-123")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "biker_24")
        self.assertContains(response, "Court Square")


class ProfileEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rider", password="test-pass-123")
        self.url = reverse("profile-edit")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/profile/edit/",
            fetch_redirect_response=False,
        )

    def test_update_changes_profile(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.post(
            self.url, {"username": "biker_24", "comfortability": 3}
        )
        self.assertRedirects(
            response, reverse("profile"), fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "biker_24")
        self.assertEqual(self.user.comfortability, 3)
        event = AuditEvent.objects.get(
            object_type="catalog.User",
            object_id=str(self.user.pk),
            action=AuditEvent.Action.UPDATE,
        )
        self.assertEqual(event.actor_username, "rider")
        self.assertEqual(event.actor_user_id, str(self.user.pk))
        self.assertEqual(event.changes["username"], {"old": "rider", "new": "biker_24"})
        self.assertEqual(event.changes["comfortability"], {"old": 0, "new": 3})


class AuditEventTests(TestCase):
    def test_create_update_and_delete_are_recorded_without_passwords(self):
        user = User.objects.create_user(username="rider", password="test-pass-123")
        user_created = AuditEvent.objects.get(
            object_type="catalog.User",
            object_id=str(user.pk),
            action=AuditEvent.Action.CREATE,
        )
        self.assertNotIn("password", user_created.changes)

        location = Location.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )
        created = AuditEvent.objects.get(
            object_type="catalog.Location",
            object_id=str(location.pk),
            action=AuditEvent.Action.CREATE,
        )
        self.assertEqual(created.changes["name"], {"old": None, "new": "Court Square"})
        self.assertNotIn("password", created.changes)

        location.name = "Updated Square"
        location.save()
        updated = AuditEvent.objects.get(
            object_type="catalog.Location",
            object_id=str(location.pk),
            action=AuditEvent.Action.UPDATE,
        )
        self.assertEqual(
            updated.changes["name"],
            {"old": "Court Square", "new": "Updated Square"},
        )

        location_id = location.pk
        location.delete()
        deleted = AuditEvent.objects.get(
            object_type="catalog.Location",
            object_id=str(location_id),
            action=AuditEvent.Action.DELETE,
        )
        self.assertEqual(
            deleted.changes["name"], {"old": "Updated Square", "new": None}
        )
        self.assertEqual(deleted.actor_user_id, "")

    def test_many_to_many_changes_are_recorded(self):
        route = Route.objects.create(name="Red Line", color="red")
        location = Location.objects.create(
            name="Court Square", latitude=38.449, longitude=-78.869
        )

        route.marked_locations.add(location)

        event = AuditEvent.objects.get(
            object_type="catalog.Route",
            object_id=str(route.pk),
            action=AuditEvent.Action.UPDATE,
        )
        self.assertEqual(
            event.changes["marked_locations"], {"old": [], "new": [location.pk]}
        )

    def test_audit_events_are_read_only_in_admin(self):
        admin_user = User.objects.create_superuser(
            username="admin", password="test-pass-123"
        )
        self.client.force_login(admin_user)

        response = self.client.get("/admin/catalog/auditevent/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audit events")
        self.assertNotContains(response, "Add audit event")


class RequestLoggingTests(TestCase):
    def test_request_log_includes_status_and_request_id_not_query_string(self):
        with self.assertLogs("catalog.request", level="INFO") as captured:
            response = self.client.get("/?token=do-not-log-this")

        self.assertEqual(response.status_code, 200)
        request_id = response["X-Request-ID"]
        self.assertTrue(request_id)
        record = captured.records[0]
        self.assertEqual(record.event, "http_request")
        self.assertEqual(record.request_id, request_id)
        self.assertEqual(record.method, "GET")
        self.assertEqual(record.path, "/")
        self.assertEqual(record.status, 200)
        payload = json.loads(JSONFormatter().format(record))
        self.assertEqual(payload["event"], "http_request")
        self.assertNotIn("do-not-log-this", json.dumps(payload))


class RouteLoggingTests(TestCase):
    def setUp(self):
        self.route = Route.objects.create(name="Red Line", color="red")

    def test_detail_view_logs_loaded_route(self):
        with self.assertLogs("catalog.routes", level="INFO") as captured:
            response = self.client.get(reverse("route-detail", args=[self.route.pk]))

        self.assertEqual(response.status_code, 200)
        record = captured.records[0]
        self.assertEqual(record.event, "route_loaded")
        self.assertEqual(record.route_id, self.route.pk)
        self.assertEqual(record.route_name, "Red Line")
        self.assertEqual(record.source, "detail")

    def test_map_logs_each_loaded_route(self):
        with self.assertLogs("catalog.routes", level="INFO") as captured:
            response = self.client.get(reverse("map"))

        self.assertEqual(response.status_code, 200)
        loaded_routes = [
            record
            for record in captured.records
            if getattr(record, "event", None) == "route_loaded"
        ]
        self.assertEqual(len(loaded_routes), Route.objects.count())
        self.assertTrue(
            any(record.route_id == self.route.pk for record in loaded_routes)
        )
        self.assertTrue(all(record.source == "map" for record in loaded_routes))


class HealthCheckTests(TestCase):
    def test_health_check_reports_database_availability(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("catalog.views.connection.cursor", side_effect=DatabaseError("offline"))
    def test_health_check_logs_database_failure(self, _mock_cursor):
        with self.assertLogs("catalog.health", level="ERROR") as captured:
            response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertEqual(captured.records[0].event, "health_check_failed")
        payload = json.loads(JSONFormatter().format(captured.records[0]))
        self.assertIn("exception", payload)


class ProfileDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rider", password="test-pass-123")
        self.url = reverse("profile-delete")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/profile/delete/",
            fetch_redirect_response=False,
        )

    def test_get_shows_confirmation_and_does_not_delete(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.get(self.url)
        self.assertContains(response, "Are you sure")
        self.assertTrue(User.objects.filter(username="rider").exists())

    def test_post_deletes_account_and_logs_out(self):
        self.client.login(username="rider", password="test-pass-123")
        user_id = self.user.pk
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(username="rider").exists())
        self.assertNotIn("_auth_user_id", self.client.session)
        event = AuditEvent.objects.get(
            object_type="catalog.User",
            object_id=str(user_id),
            action=AuditEvent.Action.DELETE,
        )
        self.assertEqual(event.actor_user_id, str(user_id))
        self.assertEqual(event.actor_username, "rider")


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rider", password="test-pass-123")

    def test_login_page_has_form(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'name="username"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"), {"username": "rider", "password": "test-pass-123"}
        )
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(
            reverse("login"), {"username": "rider", "password": "wrong-pass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your username and password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_session_is_maintained_across_pages(self):
        self.client.login(username="rider", password="test-pass-123")
        for name in ("index", "profile"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Log out")

    def test_logout_via_post_ends_session(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(self.client.get(reverse("index")), "Log in")

    def test_logout_rejects_get(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)


class AuthEnforcedTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="rider", password="test-pass-123")
        self.protected = ["profile", "profile-edit", "profile-delete"]

    def test_anonymous_is_redirected_to_login(self):
        for name in self.protected:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_logged_in_user_can_access(self):
        self.client.login(username="rider", password="test-pass-123")
        for name in self.protected:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_login_returns_user_to_requested_page(self):
        url = reverse("profile")
        response = self.client.post(
            reverse("login"),
            {"username": "rider", "password": "test-pass-123", "next": url},
        )
        self.assertRedirects(response, url, fetch_redirect_response=False)


class LandmarkTests(TestCase):
    def test_pages_have_nav_and_main(self):
        for name in ("index", "route-list", "location-list", "map", "login"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, "<nav")
                self.assertContains(response, "<main")


class WaypointModelTests(TestCase):
    """Waypoints keep an order on each route, including repeated loop points."""

    @classmethod
    def setUpTestData(cls):
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.438, longitude=-78.871)
        cls.red = Route.objects.create(
            name="Red Line", color="red", start_location=start, end_location=end
        )
        cls.green = Route.objects.create(
            name="Green Line", color="green", start_location=start, end_location=end
        )
        cls.first = Waypoint.objects.create(latitude=38.44, longitude=-78.87)
        cls.second = Waypoint.objects.create(latitude=38.45, longitude=-78.86)
        # Added out of order to check the ordering comes from `order`.
        RouteWaypoint.objects.create(route=cls.red, waypoint=cls.second, order=1)
        RouteWaypoint.objects.create(route=cls.red, waypoint=cls.first, order=0)

    def test_defaults(self):
        self.assertEqual(self.first.likes, 0)
        self.assertEqual(self.first.dislikes, 0)
        self.assertEqual(self.first.notes, "")

    def test_route_waypoints_in_order(self):
        waypoints = [rw.waypoint for rw in self.red.route_waypoints.all()]
        self.assertEqual(waypoints, [self.first, self.second])

    def test_shared_waypoint_has_order_per_route(self):
        RouteWaypoint.objects.create(route=self.green, waypoint=self.second, order=0)
        self.assertCountEqual(self.second.routes.all(), [self.red, self.green])

    def test_loop_route_can_repeat_a_waypoint(self):
        RouteWaypoint.objects.create(route=self.red, waypoint=self.first, order=2)
        waypoints = [rw.waypoint for rw in self.red.route_waypoints.all()]
        self.assertEqual(waypoints, [self.first, self.second, self.first])

    def test_duplicate_order_on_route_rejected(self):
        extra = Waypoint.objects.create(latitude=38.46, longitude=-78.85)
        with self.assertRaises(IntegrityError):
            RouteWaypoint.objects.create(route=self.red, waypoint=extra, order=0)


class RouteMetadataTests(TestCase):
    def test_subroute_parent_must_be_a_main_route(self):
        main_route = Route.objects.create(name="Main", color="green")
        subroute = Route.objects.create(
            name="Subroute",
            color="green",
            route_type=Route.Type.SUBROUTE,
            parent_route=main_route,
        )
        nested_subroute = Route(
            name="Nested subroute",
            color="green",
            route_type=Route.Type.SUBROUTE,
            parent_route=subroute,
        )

        with self.assertRaises(ValidationError):
            nested_subroute.full_clean()
