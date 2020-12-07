from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


class TestUserApi(TestCase):
    USER_API_URL = reverse('user:create')
    TOKEN_API_URL = reverse('user:token')

    def setUp(self):
        self.client = APIClient()


class TestPublicUsersAPI(TestUserApi):

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
