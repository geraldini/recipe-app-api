from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from core.models import Ingredient
from core.models import Recipe
from core.models import Tag
from recipe.serializers import RecipeDetailSerializer
from recipe.serializers import RecipeSerializer
from recipe.tests.test_api_base import TestPublicApi
from recipe.tests.test_api_base import TestPrivateApi


def create_tag(user, name='Main couse'):
    """Create and return a tag"""
    return Tag.objects.create(user=user, name=name)


def create_ingredient(user, name='Salt'):
    """Create and return an ingredient"""
    return Ingredient.objects.create(user=user, name=name)


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

    def get_detail_url(self, recipe_id):
        """Return recipe detail URL"""
        return reverse('recipe:recipe-detail', args=[recipe_id])

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

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        recipe.tags.add(create_tag(user=self.user, name='Want To Go Again'))
        recipe.ingredients.add(create_ingredient(user=self.user))
        recipe.ingredients.add(
            create_ingredient(user=self.user, name='Parsley'),
        )

        url = self.get_detail_url(recipe.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'name': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.0,
        }
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""
        tags = [
            create_tag(self.user, 'Dinner'),
            create_tag(self.user, 'Casual'),
        ]
        payload = {
            'name': 'Tritip',
            'time_minutes': 50,
            'price': 12.0,
            'tags': [tag.id for tag in tags],
        }
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        recipe_tags = recipe.tags.all()
        self.assertEqual(recipe_tags.count(), len(tags))
        for tag in tags:
            self.assertIn(tag, recipe_tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredients = [
            create_ingredient(self.user, 'Prawns'),
            create_ingredient(self.user, 'Ginger'),
        ]
        payload = {
            'name': 'Thai red curry prawns',
            'time_minutes': 25,
            'price': 7.0,
            'ingredients': [ingredient.id for ingredient in ingredients],
        }
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        recipe_ingredients = recipe.ingredients.all()
        self.assertEqual(recipe_ingredients.count(), len(ingredients))
        for ingredient in ingredients:
            self.assertIn(ingredient, recipe_ingredients)

    def test_update_recipe_partially(self):
        """Test updating a recipe with PATCH"""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        new_tag = create_tag(user=self.user, name='Curry')
        payload = {
            'name': 'Butter Chicken',
            'tags': new_tag.id,
        }
        url = self.get_detail_url(recipe.id)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.name, payload['name'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_update_recipe_fully(self):
        """Test updating a recipe with PUT"""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        payload = {
            'name': 'Cheeseburger',
            'time_minutes': 10,
            'price': 3,
        }
        url = self.get_detail_url(recipe.id)
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)
