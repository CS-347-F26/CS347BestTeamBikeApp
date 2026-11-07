from django.test import TestCase
from django.urls import reverse

from .models import Location, Route, User


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
            ("index", ()): "/bike-routes/",
            ("route-list", ()): "/bike-routes/routes/",
            ("route-detail", (r,)): f"/bike-routes/routes/{r}/",
            ("feedback-route-selection", ()): "/bike-routes/feedback/",
            ("feedback-form", (r,)): f"/bike-routes/routes/{r}/feedback/",
            (
                "feedback-confirmation",
                (r,),
            ): f"/bike-routes/routes/{r}/feedback/thanks/",
            ("post-ride-feedback-prompt", (r,)): f"/bike-routes/routes/{r}/complete/",
            ("location-list", ()): "/bike-routes/locations/",
            ("location-detail", (loc,)): f"/bike-routes/locations/{loc}/",
            ("map", ()): "/bike-routes/map/",
            ("trip-new", ()): "/bike-routes/trips/new/",
            ("profile", ()): "/bike-routes/profile/",
            ("login", ()): "/accounts/login/",
        }
        for (name, args), path in expected.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), path)

    def test_route_get_absolute_url(self):
        self.assertEqual(
            self.route.get_absolute_url(), f"/bike-routes/routes/{self.route.pk}/"
        )

    def test_root_redirects_to_home(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/bike-routes/", fetch_redirect_response=False)

    def test_public_pages_load(self):
        r, loc = self.route.pk, self.start.pk
        pages = [
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

    def test_old_catalog_prefix_is_gone(self):
        response = self.client.get("/catalog/routes/")
        self.assertEqual(response.status_code, 404)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response,
            "/accounts/login/?next=/bike-routes/profile/",
            fetch_redirect_response=False,
        )

    def test_profile_loads_when_logged_in(self):
        User.objects.create_user(username="rider", password="test-pass-123")
        self.client.login(username="rider", password="test-pass-123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
