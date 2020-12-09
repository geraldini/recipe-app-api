from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


class TestUserApi(TestCase):
    USER_API_URL = reverse('user:create')
    TOKEN_API_URL = reverse('user:token')
    ME_URL = reverse('user:me')


class TestPublicUsersAPI(TestUserApi):

    def setUp(self):
        self.client = APIClient()

    def test_create_new_user(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "name": "Nuno Geraldes",
            "email": "nhpgeraldes@gmail.com",
            "password": "123Test!"
        }
        response = self.client.post(self.USER_API_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_create_existing_user(self):
        """Test creating user that already exists fails"""
        payload = {
            "name": "Nuno Geraldes",
            "email": "nhpgeraldes@gmail.com",
            "password": "existing123Test!"
        }
        get_user_model().objects.create_user(**payload)

        response = self.client.post(self.USER_API_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_too_short(self):
        """Test user creation fails if password is shorter than 6 characters"""
        payload = {
            "name": "Nuno Geraldes",
            "email": "nhpgeraldes@gmail.com",
            "password": "12"
        }

        response = self.client.post(self.USER_API_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {'email': 'user@gmail.com', 'password': 'testpassword'}
        get_user_model().objects.create_user(**payload)
        response = self.client.post(self.TOKEN_API_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        username = 'user@gmail.com'
        good_payload = {'email': username, 'password': 'goodpassword'}
        get_user_model().objects.create_user(**good_payload)

        wrong_payload = {'email': username, 'password': 'wrongpassword'}
        response = self.client.post(self.TOKEN_API_URL, wrong_payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        payload = {'email': 'user@gmail.com', 'password': 'wrongpassword'}

        response = self.client.post(self.TOKEN_API_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_password(self):
        """Test that email and password are required"""
        payload = {'email': 'user@gmail.com', 'password': ''}

        response = self.client.post(self.TOKEN_API_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        response = self.client.get(self.ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateUserApi(TestUserApi):
    """Test API requests that require authentication"""

    def setUp(self):
        payload = {
            "name": "Nuno Geraldes",
            "email": "nhpgeraldes@gmail.com",
            "password": "existing123Test!"
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving the profile of a logged in user"""
        response = self.client.get(self.ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = {
            "name": self.user.name,
            "email": self.user.email,
        }
        self.assertEqual(response.data, payload)

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed in the me URL"""
        response = self.client.post(self.ME_URL, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_update_profile_success(self):
        """Test updating the user profile for an authenticated user"""
        payload = {
            'name': 'Nuno Passos Geraldes',
            'password': 'ThisIsTheNewPassword',
        }
        response = self.client.patch(self.ME_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
