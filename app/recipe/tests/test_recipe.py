from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from core.models import Recipe
from recipe.serializers import RecipeSerializer
from recipe.tests.test_api_base import TestPublicApi
from recipe.tests.test_api_base import TestPrivateApi


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'name': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.0,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class TestPublicTagsApi(TestPublicApi):
    """Test the publicly available tags API"""

    API_URL = reverse('recipe:recipe-list')

    def test_login_required(self):
        """Test that login is required to retrieve tags"""
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateTagsApi(TestPrivateApi):

    API_URL = reverse('recipe:recipe-list')

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_user_recipes(self):
        """Test retrieving recipes of a specific user"""
        user2 = get_user_model().objects.create_user(
            'npassosg@cisco.com',
            'sometestpassword',
        )
        create_recipe(self.user)
        create_recipe(self.user)
        create_recipe(user2)

        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.data, serializer.data)
