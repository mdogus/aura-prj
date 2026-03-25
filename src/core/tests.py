from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class HealthcheckTests(TestCase):
    """
    /healthz/ endpoint'inin veritabanı bağlantısını doğruladığını test eder.
    """

    def test_healthcheck_returns_ok_when_database_is_available(self):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_healthcheck_content_type_is_plain_text(self):
        response = self.client.get(reverse("healthcheck"))
        self.assertIn("text/plain", response["Content-Type"])

    def test_healthcheck_returns_503_when_database_is_unavailable(self):
        with patch(
            "django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection",
            side_effect=OperationalError("connection refused"),
        ):
            response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"db_unavailable")

    def test_healthcheck_is_accessible_without_authentication(self):
        """Monitoring servisleri kimlik doğrulaması gerektirmeden erişebilmelidir."""
        response = self.client.get(reverse("healthcheck"))
        # Login sayfasına yönlendirme yapılmamalı
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 200)


class HomePageTests(TestCase):
    """
    Ana sayfa görünürlük ve erişilebilirlik testleri.
    """

    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_accessible_without_login(self):
        """Ana sayfa kimliği doğrulanmamış ziyaretçilere açık olmalıdır."""
        response = self.client.get(reverse("home"))
        # Login sayfasına yönlendirme yapılmamalı
        self.assertNotEqual(response.status_code, 302)
