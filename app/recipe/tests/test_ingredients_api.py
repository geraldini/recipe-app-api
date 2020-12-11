from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from core.models import Recipe
from recipe.serializers import IngredientSerializer
from recipe.tests.test_api_base import TestPublicApi
from recipe.tests.test_api_base import TestPrivateApi


class TestPublicIngredientApi(TestPublicApi):
    """Test the publicly available ingredients API"""

    API_URL = reverse('recipe:ingredient-list')

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to retrieve ingredients"""
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateIngredientApi(TestPrivateApi):
    """Test ingredients API is accessible for authorized users"""

    API_URL = reverse('recipe:ingredient-list')

    def test_retrieve_ingredients(self):
        """Test retrieveing all the ingredients associated with the user"""
        Ingredient.objects.create(user=self.user, name='tomato')
        Ingredient.objects.create(user=self.user, name='salt')

        response = self.client.get(self.API_URL)

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

        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(user_ingredients))
        for ingredient in response.data:
            self.assertIn(ingredient['name'], user_ingredients)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Sugar'}
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_empty_ingredient(self):
        """Test creating an ingredient with empty name is not allowed"""
        payload = {'name': ''}
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering ingredients that are assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Bread')
        Ingredient.objects.create(user=self.user, name='Butter')
        recipe = Recipe.objects.create(
            user=self.user,
            name='Avocado toast',
            price=7.5,
            time_minutes=5,
        )
        recipe.ingredients.add(ingredient1)

        response = self.client.get(self.API_URL, {'assigned_only': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer1 = IngredientSerializer(ingredient1)

        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer1.data, response.data)

    def test_retrieve_ingredients_assigned_to_recipe_unique(self):
        """Test that filtering assigned ingredients are unique"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Bread')
        Ingredient.objects.create(user=self.user, name='Butter')

        recipe1 = Recipe.objects.create(
            user=self.user,
            name='Avocado toast',
            price=7.5,
            time_minutes=5,
        )
        recipe1.ingredients.add(ingredient1)

        recipe2 = Recipe.objects.create(
            user=self.user,
            name='Breakfast ciabatta',
            price=15.0,
            time_minutes=12,
        )
        recipe2.ingredients.add(ingredient1)

        response = self.client.get(self.API_URL, {'assigned_only': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer1 = IngredientSerializer(ingredient1)

        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer1.data, response.data)
