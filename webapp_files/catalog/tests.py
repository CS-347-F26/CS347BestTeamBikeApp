import json
from pathlib import Path
from unittest.mock import patch

from django.db import IntegrityError
from django.db.utils import DatabaseError
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    AuditEvent,
    Location,
    Route,
    RouteFeedback,
    RouteWaypoint,
    User,
    Waypoint,
)
from .log_formatters import JSONFormatter
from .route_import import RouteImportError, parse_route_file
from django.core.files.uploadedfile import SimpleUploadedFile


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
            ("help", ()): "/help/",
            ("route-list", ()): "/routes/",
            ("route-import", ()): "/routes/import/",
            ("route-detail", (r,)): f"/routes/{r}/",
            ("route-export", (r,)): f"/routes/{r}/export/",
            ("route-edit", (r,)): f"/routes/{r}/edit/",
            ("route-delete", (r,)): f"/routes/{r}/delete/",
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
            ("profile-feedback-list", ()): "/profile/feedback/",
            ("profile-feedback-edit", (7,)): "/profile/feedback/7/edit/",
            ("profile-feedback-delete", (7,)): "/profile/feedback/7/delete/",
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
        self.assertContains(response, f'href="{reverse("map")}"')

    def test_public_pages_load(self):
        r, loc = self.route.pk, self.start.pk
        pages = [
            ("landing", ()),
            ("index", ()),
            ("help", ()),
            ("route-list", ()),
            ("route-detail", (r,)),
            ("feedback-route-selection", ()),
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
        # feedback-form needs a login before it looks the route up.
        User.objects.create_user(username="checker", password="test-pass-123")
        self.client.login(username="checker", password="test-pass-123")
        names = [
            "route-detail",
            "route-export",
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
        # User-made routes only show on the map for the rider who made them.
        maker = User.objects.create_user(username="maker", password="test-pass-123")
        self.client.login(username="maker", password="test-pass-123")
        route = Route.objects.create(
            name="Red Line",
            color="red",
            is_official=False,
            created_by=maker,
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
        data_path = Path(__file__).resolve().parents[1] / "waypoints.json"
        with data_path.open(encoding="utf-8") as data_file:
            groups = json.load(data_file)
        expected_names = {
            feature.get("name") or feature.get("type")
            for group in groups
            for feature in group.get("features", [])
        }
        self.assertSetEqual(
            set(routes.values_list("name", flat=True)),
            expected_names,
        )
        west_side = routes.get(name="West Side")
        emu_subroute = routes.get(name="West Side Emu Subroute")
        self.assertEqual(west_side.route_type, Route.Type.MAIN)
        self.assertEqual(emu_subroute.route_type, Route.Type.SUBROUTE)
        self.assertEqual(emu_subroute.parent_route, west_side)
        self.assertGreater(west_side.route_waypoints.count(), 1)
        self.assertEqual(
            west_side.route_waypoints.first().waypoint.name, "Willow Run Rd"
        )
        central_route = routes.get(name="Central")
        ralph_subroute = routes.get(name="Central Ralph Samson Park Subroute")
        self.assertEqual(ralph_subroute.parent_route, central_route)


class SignUpTests(TestCase):
    def setUp(self):
        self.url = reverse("signup")

    def test_signup_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")
        # Both password fields get a Show/Hide button.
        self.assertContains(response, 'class="password-toggle"', count=2)

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
        self.assertContains(response, 'class="auth-field-error"')


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

    def test_edit_page_uses_card_layout(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.get(self.url)
        self.assertContains(response, 'class="auth-card"')
        self.assertContains(response, "Save changes")
        self.assertContains(response, f'href="{reverse("profile")}">Cancel</a>')


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

    def test_failed_login_marks_fields_invalid(self):
        """Both fields are flagged and point at the error message."""
        response = self.client.post(
            reverse("login"), {"username": "rider", "password": "wrong-pass"}
        )
        html = response.content.decode()
        self.assertIn('id="login-error"', html)
        self.assertEqual(html.count('aria-invalid="true"'), 2)
        self.assertEqual(html.count('aria-describedby="login-error"'), 2)

    def test_login_page_starts_without_invalid_fields(self):
        html = self.client.get(reverse("login")).content.decode()
        self.assertNotIn('aria-invalid="true"', html)

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
        for name in ("index", "help", "route-list", "location-list", "map", "login"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, "<nav")
                self.assertContains(response, "<main")

    def test_help_page_has_guidance_and_navigation_link(self):
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Explore the map")
        self.assertContains(response, "Find and compare routes")
        self.assertContains(response, "Share route feedback")
        self.assertContains(response, f'href="{reverse("help")}">Help</a>')

    def test_nav_marks_current_section(self):
        """The hamburger link for the page's section is the active pill. Pages
        that also have a bottom-bar shortcut mark that one too, so
        aria-current appears once per nav."""
        # Home goes to the landing page for now (the index page still exists).
        cases = {
            "landing": ("Home", 2),
            "map": ("Map", 2),
            "route-list": ("Routes", 2),
            "trip-new": ("Plan a trip", 1),
            "help": ("Help", 1),
        }
        for name, (label, count) in cases.items():
            with self.subTest(name=name):
                url = reverse(name)
                html = self.client.get(url).content.decode()
                self.assertIn(
                    f'<a class="nav-link active" aria-current="page" href="{url}">{label}</a>',
                    html,
                )
                self.assertEqual(html.count('aria-current="page"'), count)

    def test_tab_bar_shows_log_in_or_profile(self):
        """The bottom bar's 4th button is Log in (back to this page after)
        when logged out, and Profile when logged in."""
        url = reverse("map")
        html = self.client.get(url).content.decode()
        self.assertIn(f'href="{reverse("login")}?next={url}">', html)
        self.assertIn("<span>Log in</span>", html)
        self.assertNotIn("<span>Profile</span>", html)

        User.objects.create_user(username="tabber", password="test-pass-123")
        self.client.login(username="tabber", password="test-pass-123")
        html = self.client.get(url).content.decode()
        self.assertIn("<span>Profile</span>", html)
        self.assertNotIn("<span>Log in</span>", html)


def _delete_all_routes():
    """A migration seeds the real Harrisonburg routes. Tests that need an
    empty route table remove them: subroutes first, because a main route
    can't be deleted while subroutes still point at it (PROTECT)."""
    Route.objects.filter(parent_route__isnull=False).delete()
    Route.objects.all().delete()


class RouteListPageTests(TestCase):
    """The routes page shows one row per route (name, comfort rating,
    comments link), or example rows while there are no routes."""

    def setUp(self):
        _delete_all_routes()

    def test_example_rows_when_no_routes(self):
        html = self.client.get(reverse("route-list")).content.decode()
        for color in ("Red", "Yellow", "Black", "Purple", "Blue", "Green"):
            self.assertIn(f'<span class="route-name">{color}</span>', html)
        self.assertEqual(html.count("Comfort rating"), 6)

    def test_real_route_replaces_example_rows(self):
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.45, longitude=-78.87)
        route = Route.objects.create(
            name="Red Line",
            color="Red",
            start_location=start,
            end_location=end,
            comfortability=4,
        )
        html = self.client.get(reverse("route-list")).content.decode()
        self.assertIn('class="route-row route-color--red"', html)
        self.assertIn('<span class="route-name">Red Line</span>', html)
        self.assertIn(f'href="{route.get_absolute_url()}">Comments</a>', html)
        self.assertEqual(html.count("Comfort rating"), 1)


class RouteSearchTests(TestCase):
    """Claim I20: the routes page's search box (?q=) matches route names or
    colors, and the comfort filter (?comfort=n) keeps routes rated n or more."""

    def setUp(self):
        _delete_all_routes()
        for name, color, comfort in (
            ("Red", "Red", 3),
            ("Blue", "Blue", 5),
            ("Purple", "Purple", 1),
            ("Memorial", "Maroon", 0),  # not rated yet
        ):
            Route.objects.create(name=name, color=color, comfortability=comfort)

    def names(self, **params):
        response = self.client.get(reverse("route-list"), params)
        self.assertEqual(response.status_code, 200)
        return [route.name for route in response.context["route_list"]]

    def test_no_search_shows_every_route(self):
        self.assertEqual(self.names(), ["Blue", "Memorial", "Purple", "Red"])

    def test_search_matches_name_in_any_case(self):
        self.assertEqual(self.names(q="red"), ["Red"])
        self.assertEqual(self.names(q="RED"), ["Red"])
        self.assertEqual(self.names(q="mem"), ["Memorial"])

    def test_search_matches_color(self):
        self.assertEqual(self.names(q="maroon"), ["Memorial"])

    def test_no_match_shows_message_not_example_rows(self):
        html = self.client.get(reverse("route-list"), {"q": "zzz"}).content.decode()
        self.assertIn("No routes match your search.", html)
        self.assertNotIn('<span class="route-name">', html)

    def test_comfort_filter_is_a_minimum(self):
        self.assertEqual(self.names(comfort=3), ["Blue", "Red"])
        self.assertEqual(self.names(comfort=1), ["Blue", "Purple", "Red"])

    def test_search_and_filter_combine(self):
        self.assertEqual(self.names(q="blue", comfort=3), ["Blue"])
        self.assertEqual(self.names(q="purple", comfort=3), [])

    def test_bad_comfort_value_is_ignored(self):
        everything = ["Blue", "Memorial", "Purple", "Red"]
        self.assertEqual(self.names(comfort=9), everything)
        self.assertEqual(self.names(comfort="abc"), everything)

    def test_page_has_search_box_and_five_comfort_circles(self):
        html = self.client.get(reverse("route-list")).content.decode()
        self.assertIn('role="search"', html)
        self.assertIn('type="search" name="q"', html)
        self.assertEqual(html.count('name="comfort"'), 5)
        # The comfort card is always on the page; there's no Filter button
        # or drop-down panel any more.
        self.assertIn('class="comfort-filter"', html)
        self.assertNotIn('data-bs-toggle="collapse"', html)
        self.assertIn("comfort-unpick.js", html)

    def test_choices_are_kept_after_submit(self):
        html = self.client.get(
            reverse("route-list"), {"q": "blue", "comfort": 4}
        ).content.decode()
        self.assertIn('value="blue"', html)
        self.assertRegex(html, r'value="4"[^>]*checked')
        self.assertIn("comfort 4+", html)  # in the "Showing n routes" line


class RouteSearchCheckboxTests(TestCase):
    """The Name / Color / Official pills under the search bar.
    ?search_in=name|color picks which fields the search text is matched
    against (none = both); ?official=on keeps only official routes."""

    def setUp(self):
        _delete_all_routes()
        Route.objects.create(name="Yellow", color="Yellow")
        Route.objects.create(name="Friendly City Trail", color="yellow")
        # A user-made route is only listed for the rider who made it.
        maker = User.objects.create_user(username="maker", password="test-pass-123")
        Route.objects.create(
            name="Community Yellow Loop",
            color="Red",
            is_official=False,
            created_by=maker,
        )
        self.client.login(username="maker", password="test-pass-123")

    def names(self, **params):
        response = self.client.get(reverse("route-list"), params)
        self.assertEqual(response.status_code, 200)
        return [route.name for route in response.context["route_list"]]

    def test_no_box_searches_name_and_color(self):
        self.assertEqual(
            self.names(q="yellow"),
            ["Community Yellow Loop", "Friendly City Trail", "Yellow"],
        )

    def test_name_box_only_matches_names(self):
        self.assertEqual(
            self.names(q="yellow", search_in="name"),
            ["Community Yellow Loop", "Yellow"],
        )

    def test_color_box_only_matches_colors(self):
        self.assertEqual(
            self.names(q="yellow", search_in="color"),
            ["Friendly City Trail", "Yellow"],
        )
        self.assertEqual(self.names(q="trail", search_in="color"), [])

    def test_both_boxes_match_either(self):
        self.assertEqual(
            self.names(q="yellow", search_in=["name", "color"]),
            self.names(q="yellow"),
        )

    def test_official_works_without_search_text(self):
        self.assertEqual(self.names(official="on"), ["Friendly City Trail", "Yellow"])

    def test_official_combines_with_search_and_comfort(self):
        Route.objects.filter(name="Yellow").update(comfortability=4)
        self.assertEqual(
            self.names(q="yellow", search_in="name", official="on"), ["Yellow"]
        )
        self.assertEqual(self.names(official="on", comfort=4), ["Yellow"])

    def test_bad_search_in_value_is_ignored(self):
        self.assertEqual(len(self.names(q="yellow", search_in="zzz")), 3)

    def test_boxes_stay_checked_after_submit(self):
        html = self.client.get(
            reverse("route-list"),
            {"q": "yellow", "search_in": "name", "official": "on"},
        ).content.decode()
        self.assertRegex(html, r'name="search_in" value="name"[^>]*checked')
        self.assertNotRegex(html, r'name="search_in" value="color"[^>]*checked')
        self.assertRegex(html, r'name="official"[^>]*checked')
        self.assertIn("“yellow” in name, official only", html)

    def test_pills_render_unchecked_by_default(self):
        html = self.client.get(reverse("route-list")).content.decode()
        self.assertEqual(html.count('name="search_in"'), 2)
        self.assertIn('name="official"', html)
        self.assertNotIn("checked", html)


class FeedbackRouteSelectionPageTests(TestCase):
    """The feedback page lists routes as rows that each link to that
    route's feedback form, or example rows while there are no routes."""

    def setUp(self):
        _delete_all_routes()

    def test_example_rows_when_no_routes(self):
        html = self.client.get(reverse("feedback-route-selection")).content.decode()
        for color in ("Red", "Yellow", "Black", "Purple", "Blue", "Green"):
            self.assertIn(f'<span class="feedback-name">{color}</span>', html)
        self.assertEqual(html.count('class="feedback-link"'), 6)

    def test_real_route_links_to_its_feedback_form(self):
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.45, longitude=-78.87)
        route = Route.objects.create(
            name="Blue Line", color="Blue", start_location=start, end_location=end
        )
        html = self.client.get(reverse("feedback-route-selection")).content.decode()
        self.assertIn('class="route-row route-color--blue feedback-row"', html)
        self.assertIn(f'href="{reverse("feedback-form", args=[route.pk])}"', html)
        self.assertEqual(html.count('class="feedback-link"'), 1)


class FeedbackFormPageTests(TestCase):
    """One route's feedback form: login required, saves a RouteFeedback,
    then shows the thank-you popup."""

    @classmethod
    def setUpTestData(cls):
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.45, longitude=-78.87)
        cls.route = Route.objects.create(
            name="Red", color="Red", start_location=start, end_location=end
        )
        cls.user = User.objects.create_user(username="rider", password="test-pass-123")

    def setUp(self):
        self.url = reverse("feedback-form", args=[self.route.pk])

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_form_shows_route_and_five_ratings(self):
        self.client.login(username="rider", password="test-pass-123")
        html = self.client.get(self.url).content.decode()
        self.assertIn('<h1 class="ff-route-name">Red</h1>', html)
        self.assertEqual(html.count('name="comfort_rating"'), 5)
        self.assertIn('class="route-color--red feedback-form-page"', html)
        self.assertNotIn(".show()", html)  # no popup before submitting

    def test_valid_submit_saves_and_shows_thanks_once(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.post(
            self.url, {"comfort_rating": "4", "text": "Wide bike lane on Main St."}
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        feedback = RouteFeedback.objects.get()
        self.assertEqual(
            (feedback.user, feedback.route, feedback.comfort_rating, feedback.text),
            (self.user, self.route, 4, "Wide bike lane on Main St."),
        )
        html = self.client.get(self.url).content.decode()
        self.assertIn("Feedback received!", html)
        self.assertIn(".show()", html)
        # Reloading again doesn't reopen the popup.
        self.assertNotIn(".show()", self.client.get(self.url).content.decode())

    def test_missing_rating_shows_error(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.post(self.url, {"text": "No rating"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pick a comfort rating from 1 to 5.")
        self.assertFalse(RouteFeedback.objects.exists())

    def test_rating_out_of_range_is_rejected(self):
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.post(self.url, {"comfort_rating": "6"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RouteFeedback.objects.exists())


class ProfilePageTests(TestCase):
    """The profile shows who you are, three stats, and your routes and
    feedback, with helpful empty states."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="rider", password="test-pass-123")
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.45, longitude=-78.87)
        cls.route = Route.objects.create(
            name="Red", color="Red", start_location=start, end_location=end
        )

    def setUp(self):
        self.client.login(username="rider", password="test-pass-123")

    def test_header_and_stats(self):
        html = self.client.get(reverse("profile")).content.decode()
        self.assertIn('<h1 id="pf-name" class="pf-name">rider</h1>', html)
        self.assertIn("Member since", html)
        for label in ("Comfort level", "Feedback given", "Saved routes"):
            self.assertIn(f"<dt>{label}</dt>", html)
        self.assertIn("<dd>Not set</dd>", html)  # comfortability defaults to 0

    def test_empty_states(self):
        html = self.client.get(reverse("profile")).content.decode()
        self.assertIn("No saved routes yet.", html)
        self.assertIn("You haven't given feedback yet.", html)
        self.assertIn("No rides yet.", html)
        self.assertIn("No marked locations yet.", html)

    def test_saved_route_and_feedback_show(self):
        self.user.saved_routes.add(self.route)
        RouteFeedback.objects.create(
            user=self.user, route=self.route, comfort_rating=4, text="Smooth ride"
        )
        html = self.client.get(reverse("profile")).content.decode()
        self.assertIn('class="pf-row route-color--red"', html)
        self.assertIn("<dt>Feedback given</dt>\n          <dd>1</dd>", html)
        self.assertIn("Comfort 4/5", html)
        self.assertIn("Smooth ride", html)
        self.assertNotIn("No saved routes yet.", html)
        self.assertIn(f'href="{reverse("profile-feedback-list")}"', html)
        self.assertIn("See all feedback (1)", html)


class ProfileFeedbackTests(TestCase):
    """A rider can list, edit and delete their own route feedback from the
    profile, but never someone else's."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="rider", password="test-pass-123")
        cls.other = User.objects.create_user(username="other", password="test-pass-123")
        start = Location.objects.create(name="A", latitude=38.449, longitude=-78.869)
        end = Location.objects.create(name="B", latitude=38.45, longitude=-78.87)
        cls.route = Route.objects.create(
            name="Red", color="Red", start_location=start, end_location=end
        )

    def setUp(self):
        self.mine = RouteFeedback.objects.create(
            user=self.user, route=self.route, comfort_rating=2, text="Busy road"
        )
        self.theirs = RouteFeedback.objects.create(
            user=self.other, route=self.route, comfort_rating=5, text="Not yours"
        )
        self.client.login(username="rider", password="test-pass-123")

    def test_pages_require_login(self):
        self.client.logout()
        for url in (
            reverse("profile-feedback-list"),
            reverse("profile-feedback-edit", args=[self.mine.pk]),
            reverse("profile-feedback-delete", args=[self.mine.pk]),
        ):
            with self.subTest(url=url):
                self.assertRedirects(
                    self.client.get(url),
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_list_shows_only_my_feedback(self):
        response = self.client.get(reverse("profile-feedback-list"))
        self.assertContains(response, "Busy road")
        self.assertContains(response, "Comfort 2/5")
        self.assertContains(
            response, reverse("profile-feedback-edit", args=[self.mine.pk])
        )
        self.assertNotContains(response, "Not yours")

    def test_list_empty_state(self):
        self.mine.delete()
        response = self.client.get(reverse("profile-feedback-list"))
        self.assertContains(response, "You haven't given feedback yet.")

    def test_edit_form_is_prefilled(self):
        url = reverse("profile-feedback-edit", args=[self.mine.pk])
        html = self.client.get(url).content.decode()
        self.assertIn("Edit feedback", html)
        self.assertIn("Save changes", html)
        self.assertRegex(html, r'value="2"[^>]*checked')
        self.assertIn("Busy road</textarea>", html)
        self.assertNotIn("thanks-modal", html)

    def test_edit_saves_changes(self):
        url = reverse("profile-feedback-edit", args=[self.mine.pk])
        response = self.client.post(url, {"comfort_rating": "4", "text": "Better now"})
        self.assertRedirects(response, reverse("profile-feedback-list"))
        self.mine.refresh_from_db()
        self.assertEqual((self.mine.comfort_rating, self.mine.text), (4, "Better now"))
        self.assertEqual((self.mine.user, self.mine.route), (self.user, self.route))

    def test_edit_rejects_bad_rating(self):
        url = reverse("profile-feedback-edit", args=[self.mine.pk])
        response = self.client.post(url, {"comfort_rating": "9", "text": "x"})
        self.assertEqual(response.status_code, 200)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.comfort_rating, 2)

    def test_delete_confirms_then_deletes(self):
        url = reverse("profile-feedback-delete", args=[self.mine.pk])
        self.assertContains(self.client.get(url), "Delete this feedback?")
        self.assertTrue(RouteFeedback.objects.filter(pk=self.mine.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse("profile-feedback-list"))
        self.assertFalse(RouteFeedback.objects.filter(pk=self.mine.pk).exists())
        self.assertTrue(RouteFeedback.objects.filter(pk=self.theirs.pk).exists())

    def test_other_users_and_missing_feedback_404(self):
        for name in ("profile-feedback-edit", "profile-feedback-delete"):
            for pk in (self.theirs.pk, 9999):
                with self.subTest(name=name, pk=pk):
                    url = reverse(name, args=[pk])
                    self.assertEqual(self.client.get(url).status_code, 404)
                    self.assertEqual(self.client.post(url).status_code, 404)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.comfort_rating, 5)


class PasswordChangePageTests(TestCase):
    """Change password uses our card-style templates, not Django's admin look."""

    def setUp(self):
        User.objects.create_user(username="rider", password="test-pass-123")
        self.client.login(username="rider", password="test-pass-123")

    def test_form_page_uses_our_template(self):
        response = self.client.get(reverse("password_change"))
        self.assertTemplateUsed(response, "registration/password_change_form.html")
        self.assertContains(response, 'class="auth-card"')
        self.assertContains(response, 'class="password-toggle"', count=3)

    def test_change_then_done_page(self):
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "test-pass-123",
                "new_password1": "Gr33nway-Loop-77",
                "new_password2": "Gr33nway-Loop-77",
            },
            follow=True,
        )
        self.assertTemplateUsed(response, "registration/password_change_done.html")
        self.assertContains(response, "Password changed")

    def test_wrong_old_password_shows_field_error(self):
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "wrong",
                "new_password1": "Gr33nway-Loop-77",
                "new_password2": "Gr33nway-Loop-77",
            },
        )
        self.assertContains(response, 'class="auth-field-error"')


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


class RouteImportTests(TestCase):
    """Riders upload a GeoJSON file (geojson.io or the team's waypoints.json
    format) at /routes/import/ to add user-made routes."""

    # A line like geojson.io saves it (Save -> GeoJSON), plus a point to skip.
    GEOJSON_IO = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Campus Loop", "color": "Blue"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-78.8690, 38.4490],
                        [-78.8700, 38.4500],
                        [-78.8710, 38.4510],
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", "coordinates": [-78.87, 38.45]},
            },
        ],
    }

    # The team's format, as in waypoints.json.
    TEAM_FORMAT = [
        {
            "type": "PredefinedRoute",
            "features": [
                {
                    "name": "Test Main",
                    "properties": {},
                    "color": "Green",
                    "geometry": {
                        "type": "MainRoute",
                        "coordinates": [
                            [-78.80, 38.40, "Start Point"],
                            [-78.81, 38.41, ""],
                        ],
                    },
                }
            ],
        },
        {
            "type": "PredefinedRoute",
            "features": [
                {
                    "type": "Test Main Spur Subroute",
                    "properties": {},
                    "color": "Green",
                    "geometry": {
                        "type": "SubRoute",
                        "coordinates": [[-78.81, 38.41, ""], [-78.82, 38.42, "End"]],
                    },
                }
            ],
        },
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="importer", password="test-pass-123"
        )

    def setUp(self):
        self.client.login(username="importer", password="test-pass-123")
        # Only look at routes these tests make (migrations load official ones).
        self.before = set(Route.objects.values_list("pk", flat=True))

    def upload(self, data, follow=False, **fields):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        upload = SimpleUploadedFile("route.geojson", raw, "application/geo+json")
        return self.client.post(
            reverse("route-import"), {"file": upload, **fields}, follow=follow
        )

    def new_routes(self):
        return Route.objects.exclude(pk__in=self.before)

    # --- parser ----------------------------------------------------------

    def test_parse_multilinestring_is_joined(self):
        result = parse_route_file(
            {
                "type": "Feature",
                "properties": {"name": "Two Parts"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[-78.1, 38.1], [-78.2, 38.2]], [[-78.3, 38.3]]],
                },
            },
            default_color="red",
        )
        self.assertEqual(len(result.routes[0].points), 3)
        self.assertEqual(result.routes[0].color, "red")

    def test_parse_elevation_is_not_a_name(self):
        result = parse_route_file(
            {
                "type": "LineString",
                "coordinates": [[-78.1, 38.1, 400], [-78.2, 38.2, 410]],
            },
            default_color="red",
        )
        self.assertEqual(result.routes[0].points[0], (-78.1, 38.1, ""))
        self.assertEqual(result.routes[0].name, "Imported route")

    def test_parse_errors(self):
        def line(coordinates, color="red"):
            return {
                "type": "Feature",
                "properties": {"color": color},
                "geometry": {"type": "LineString", "coordinates": coordinates},
            }

        bad = {
            "one point": line([[-78.1, 38.1]]),
            "off the map": line([[-78.1, 38.1], [-200, 38.2]]),
            "text coordinate": line([[-78.1, 38.1], ["x", 38.2]]),
            "unknown color": line([[-78.1, 38.1], [-78.2, 38.2]], color="teal"),
            "no color": line([[-78.1, 38.1], [-78.2, 38.2]], color=""),
            "no lines": {"type": "FeatureCollection", "features": []},
            "not geojson": {"hello": "world"},
        }
        for label, data in bad.items():
            with self.subTest(label), self.assertRaises(RouteImportError):
                parse_route_file(data)

    # --- view ------------------------------------------------------------

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("route-import"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('route-import')}",
            fetch_redirect_response=False,
        )

    def test_form_page_loads(self):
        response = self.client.get(reverse("route-import"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_import_geojson_io_file(self):
        response = self.upload(self.GEOJSON_IO, follow=True)
        route = self.new_routes().get()
        self.assertRedirects(response, route.get_absolute_url())
        self.assertContains(response, "Added by importer")
        self.assertContains(response, "Skipped 1 feature")
        self.assertEqual(route.name, "Campus Loop")
        self.assertEqual(route.color, "blue")
        self.assertFalse(route.is_official)
        self.assertEqual(route.created_by, self.user)
        self.assertEqual(route.route_type, Route.Type.MAIN)
        self.assertEqual(
            [(rw.order, rw.waypoint.longitude) for rw in route.route_waypoints.all()],
            [(0, -78.8690), (1, -78.8700), (2, -78.8710)],
        )

    def test_form_name_and_color_fill_gaps(self):
        data = {
            "type": "LineString",
            "coordinates": [[-78.869, 38.449], [-78.871, 38.439]],
        }
        self.upload(data, name="My Commute", color="purple")
        route = self.new_routes().get()
        self.assertEqual((route.name, route.color), ("My Commute", "purple"))

    def test_import_team_format_links_subroute(self):
        response = self.upload(self.TEAM_FORMAT)
        self.assertRedirects(response, reverse("route-list"))
        main = self.new_routes().get(name="Test Main")
        sub = self.new_routes().get(name="Test Main Spur Subroute")
        self.assertEqual(sub.route_type, Route.Type.SUBROUTE)
        self.assertEqual(sub.parent_route, main)
        self.assertEqual(main.route_waypoints.first().waypoint.name, "Start Point")
        # The shared point is one waypoint on both routes.
        self.assertEqual(
            main.route_waypoints.last().waypoint,
            sub.route_waypoints.first().waypoint,
        )

    def test_waypoints_json_imports(self):
        """The team's real waypoints.json is a valid upload."""
        raw = (Path(__file__).resolve().parents[1] / "waypoints.json").read_bytes()
        response = self.upload(raw)
        self.assertRedirects(response, reverse("route-list"))
        self.assertGreater(self.new_routes().count(), 5)

    def test_parse_checks_area_bounds(self):
        data = {"type": "LineString", "coordinates": [[-78.1, 38.1], [-78.2, 38.2]]}
        # No bounds: anywhere on Earth is fine.
        parse_route_file(data, default_color="red")
        with self.assertRaisesMessage(RouteImportError, "goes outside Testville"):
            parse_route_file(
                data,
                default_color="red",
                bounds=(-79.0, 38.0, -78.15, 38.5),
                area_name="Testville",
            )

    def test_route_outside_harrisonburg_is_rejected(self):
        # Ends in Richmond, VA.
        data = {
            "type": "Feature",
            "properties": {"name": "Road Trip", "color": "red"},
            "geometry": {
                "type": "LineString",
                "coordinates": [[-78.869, 38.449], [-77.436, 37.541]],
            },
        }
        response = self.upload(data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "goes outside the Harrisonburg area")
        self.assertFalse(self.new_routes().exists())

    @override_settings(
        ROUTE_AREA_NAME="Richmond", ROUTE_AREA_BOUNDS=(-77.6, 37.4, -77.3, 37.7)
    )
    def test_area_comes_from_settings(self):
        """Another city only changes settings, not code."""
        data = {
            "type": "Feature",
            "properties": {"name": "Downtown RVA", "color": "red"},
            "geometry": {
                "type": "LineString",
                "coordinates": [[-77.436, 37.541], [-77.440, 37.545]],
            },
        }
        self.upload(data)
        self.assertTrue(self.new_routes().filter(name="Downtown RVA").exists())
        self.assertContains(self.client.get(reverse("route-import")), "within Richmond")

    def test_export_downloads_geojson(self):
        self.upload(self.TEAM_FORMAT)
        main = self.new_routes().get(name="Test Main")
        response = self.client.get(reverse("route-export", args=[main.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/geo+json")
        self.assertIn('filename="test-main.geojson"', response["Content-Disposition"])
        data = json.loads(response.content)
        line, point = data["features"]
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(line["properties"]["name"], "Test Main")
        self.assertEqual(line["properties"]["color"], "green")
        self.assertEqual(
            line["geometry"],
            {"type": "LineString", "coordinates": [[-78.80, 38.40], [-78.81, 38.41]]},
        )
        # The named waypoint comes along as a point.
        self.assertEqual(point["properties"]["name"], "Start Point")
        self.assertContains(
            self.client.get(main.get_absolute_url()),
            reverse("route-export", args=[main.pk]),
        )

    # --- privacy, saved routes, edit, delete -------------------------------

    def import_campus_loop(self):
        self.upload(self.GEOJSON_IO)
        return self.new_routes().get()

    def test_imported_route_is_saved_for_uploader(self):
        route = self.import_campus_loop()
        self.assertIn(route, self.user.saved_routes.all())

    def test_imported_route_is_private_to_uploader(self):
        route = self.import_campus_loop()
        for page in ("route-list", "feedback-route-selection"):
            with self.subTest(owner=page):
                response = self.client.get(reverse(page))
                self.assertIn(route, response.context["route_list"])
        map_names = [
            r["name"]
            for r in self.client.get(reverse("map")).context["map_data"]["routes"]
        ]
        self.assertIn("Campus Loop", map_names)

        User.objects.create_user(username="other", password="test-pass-123")
        for who in ("other rider", "logged out"):
            self.client.logout()
            if who == "other rider":
                self.client.login(username="other", password="test-pass-123")
            with self.subTest(who=who):
                # Check by id: an official route is called "Central JMU Campus
                # Loop Subroute", so the name alone isn't unique.
                listed = self.client.get(reverse("route-list")).context["route_list"]
                self.assertNotIn(route, listed)
                picks = self.client.get(reverse("feedback-route-selection"))
                self.assertNotIn(route, picks.context["route_list"])
                map_data = self.client.get(reverse("map")).context["map_data"]
                self.assertNotIn("Campus Loop", [r["name"] for r in map_data["routes"]])
                for name in (
                    "route-detail",
                    "route-export",
                    "post-ride-feedback-prompt",
                    "feedback-confirmation",
                ):
                    response = self.client.get(reverse(name, args=[route.pk]))
                    self.assertEqual(response.status_code, 404, name)
            if who == "other rider":
                for name in ("feedback-form", "route-edit", "route-delete"):
                    with self.subTest(who=who, page=name):
                        response = self.client.get(reverse(name, args=[route.pk]))
                        self.assertEqual(response.status_code, 404)
                response = self.client.post(reverse("route-delete", args=[route.pk]))
                self.assertEqual(response.status_code, 404)
                self.assertTrue(Route.objects.filter(pk=route.pk).exists())

    def test_import_does_not_touch_official_waypoints(self):
        official = Route.objects.create(name="Official", color="red")
        shared = Waypoint.objects.create(longitude=-78.869, latitude=38.449)
        RouteWaypoint.objects.create(route=official, waypoint=shared, order=0)
        data = {
            "type": "LineString",
            "coordinates": [[-78.869, 38.449, "My Secret Spot"], [-78.870, 38.450]],
        }
        self.upload(data, color="red")
        shared.refresh_from_db()
        self.assertEqual(shared.name, "")
        route = self.new_routes().exclude(pk=official.pk).get()
        self.assertNotEqual(route.route_waypoints.first().waypoint, shared)

    def test_owner_sees_edit_and_delete_links(self):
        route = self.import_campus_loop()
        detail = self.client.get(route.get_absolute_url())
        self.assertContains(detail, reverse("route-edit", args=[route.pk]))
        self.assertContains(detail, reverse("route-delete", args=[route.pk]))

    def test_owner_replaces_route_with_new_file(self):
        route = self.import_campus_loop()
        RouteFeedback.objects.create(user=self.user, route=route, comfort_rating=4)
        old_ids = list(route.route_waypoints.values_list("waypoint_id", flat=True))
        new_file = {
            "type": "LineString",
            "coordinates": [[-78.860, 38.440], [-78.861, 38.441]],
        }
        response = self.client.post(
            reverse("route-edit", args=[route.pk]),
            {
                "file": SimpleUploadedFile(
                    "new.geojson", json.dumps(new_file).encode(), "application/geo+json"
                )
            },
        )
        self.assertRedirects(response, route.get_absolute_url())
        route.refresh_from_db()
        # No name/color in the file or form: the current ones are kept.
        self.assertEqual((route.name, route.color), ("Campus Loop", "blue"))
        self.assertEqual(
            [(rw.waypoint.longitude, rw.waypoint.latitude) for rw in route.route_waypoints.all()],
            [(-78.860, 38.440), (-78.861, 38.441)],
        )
        self.assertEqual(route.feedback.count(), 1)
        self.assertFalse(Waypoint.objects.filter(pk__in=old_ids).exists())

    def test_edit_rejects_bad_files_and_keeps_route(self):
        route = self.import_campus_loop()
        two_lines = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {},
                 "geometry": {"type": "LineString", "coordinates": [[-78.86, 38.44], [-78.87, 38.45]]}},
                {"type": "Feature", "properties": {},
                 "geometry": {"type": "LineString", "coordinates": [[-78.86, 38.44], [-78.88, 38.46]]}},
            ],
        }
        far_away = {"type": "LineString", "coordinates": [[-78.86, 38.44], [-77.43, 37.54]]}
        for label, data, message in (
            ("two lines", two_lines, "upload a file with one line"),
            ("outside area", far_away, "goes outside"),
        ):
            with self.subTest(label):
                response = self.client.post(
                    reverse("route-edit", args=[route.pk]),
                    {"file": SimpleUploadedFile("x.geojson", json.dumps(data).encode())},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, message)
                self.assertEqual(route.route_waypoints.count(), 3)

    def test_owner_deletes_route_and_subroutes(self):
        self.upload(self.TEAM_FORMAT)
        main = self.new_routes().get(name="Test Main")
        sub = self.new_routes().get(name="Test Main Spur Subroute")
        waypoint_ids = list(
            RouteWaypoint.objects.filter(route__in=[main, sub]).values_list(
                "waypoint_id", flat=True
            )
        )
        confirm = self.client.get(reverse("route-delete", args=[main.pk]))
        self.assertContains(confirm, "Test Main Spur Subroute")
        response = self.client.post(reverse("route-delete", args=[main.pk]))
        self.assertRedirects(response, reverse("route-list"))
        self.assertFalse(self.new_routes().exists())
        self.assertFalse(Waypoint.objects.filter(pk__in=waypoint_ids).exists())

    def test_official_routes_cannot_be_edited_or_deleted(self):
        official = Route.objects.create(name="Official", color="red")
        for name in ("route-edit", "route-delete"):
            with self.subTest(name):
                response = self.client.get(reverse(name, args=[official.pk]))
                self.assertEqual(response.status_code, 404)

    def test_deleting_account_deletes_their_routes(self):
        route = self.import_campus_loop()
        self.user.delete()
        self.assertFalse(Route.objects.filter(pk=route.pk).exists())

    def test_exported_file_imports_again(self):
        self.upload(self.GEOJSON_IO)
        route = self.new_routes().get()
        exported = self.client.get(reverse("route-export", args=[route.pk])).content
        self.before.add(route.pk)
        self.upload(exported)
        copy = self.new_routes().get()
        self.assertEqual((copy.name, copy.color), ("Campus Loop", "blue"))
        self.assertEqual(copy.route_waypoints.count(), 3)

    def test_bad_file_shows_error_and_saves_nothing(self):
        empty = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        for raw in (b"{not json", empty):
            with self.subTest(raw=raw):
                response = self.upload(raw)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "auth-field-error")
                self.assertFalse(self.new_routes().exists())
