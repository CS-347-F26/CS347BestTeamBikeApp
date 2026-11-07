from django.test import TestCase


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
