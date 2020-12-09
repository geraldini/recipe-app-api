from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_API_URL = reverse('recipe:ingredient-list')


class TestPublicIngredientApi(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that API is only accessible for logged in users"""
        response = self.client.get(INGREDIENTS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateIngredientApi(TestCase):
    """Test ingredients API is accessible for authorized users"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'test_password',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieveing all the ingredients associated with the user"""
        Ingredient.objects.create(user=self.user, name='tomato')
        Ingredient.objects.create(user=self.user, name='salt')

        response = self.client.get(INGREDIENTS_API_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_user_ingredients(self):
        user2 = get_user_model().objects.create_user(
            'test2@gmail.com',
            'test2_password',
        )
        Ingredient.objects.create(user=user2, name='flour')

        user_ingredients = ['tomato', 'salt', 'pepper']
        for ingredient in user_ingredients:
            Ingredient.objects.create(user=self.user, name=ingredient)

        response = self.client.get(INGREDIENTS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(user_ingredients))
        for ingredient in response.data:
            self.assertIn(ingredient['name'], user_ingredients)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Sugar'}
        response = self.client.post(INGREDIENTS_API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_empty_ingredient(self):
        """Test creating an ingredient with empty name is not allowed"""
        payload = {'name': ''}
        response = self.client.post(INGREDIENTS_API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
