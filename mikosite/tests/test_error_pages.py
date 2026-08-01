from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.utils.functional import SimpleLazyObject

from accounts.models import User
from mainSite.views import bad_request, page_not_found, permission_denied, server_error

MISSING_URL = '/nie-ma-takiej-strony/'


class ErrorResponseTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_page_returns_an_empty_404(self):
        response = self.client.get(MISSING_URL)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b'')

    def test_handlers_return_their_status_without_a_body(self):
        request = self.factory.get(MISSING_URL)
        responses = {
            400: bad_request(request, SuspiciousOperation()),
            403: permission_denied(request, PermissionDenied()),
            404: page_not_found(request, Http404()),
            500: server_error(request),
        }

        for status, response in responses.items():
            with self.subTest(status=status):
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.content, b'')

    def test_error_response_does_not_query_the_database(self):
        """A query here would strand a pooled connection under ASGI (#36027).

        request.user is lazy, exactly as AuthenticationMiddleware leaves it, so
        it only hits the database if the error response resolves it - which is
        what rendering a template with the site header used to do.
        """
        user = User.objects.create_user(
            username='widz', password='Widzpass1!', email='widz@test.com',
        )
        request = self.factory.get(MISSING_URL)
        request.user = SimpleLazyObject(lambda: User.objects.get(pk=user.pk))

        with self.assertNumQueries(0):
            response = page_not_found(request, Http404())

        self.assertEqual(response.status_code, 404)
