from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestPublicApi(TestCase):
    """Test the publicly available API"""

    def setUp(self):
        self.client = APIClient()

    def _test_login_required(self):
        """Test that login is required to retrieve items"""
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateApi(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'nhpgeraldes@gmail.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
