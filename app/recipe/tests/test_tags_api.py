from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from core.models import Recipe
from core.models import Tag
from recipe.serializers import TagSerializer
from recipe.tests.test_api_base import TestPublicApi
from recipe.tests.test_api_base import TestPrivateApi


class TestPublicTagsApi(TestPublicApi):
    """Test the publicly available tags API"""

    API_URL = reverse('recipe:tag-list')

    def test_login_required(self):
        """Test that login is required to retrieve tags"""
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateTagsApi(TestPrivateApi):

    API_URL = reverse('recipe:tag-list')

    def test_retrieve_tags(self):
        """Test retrieving tags for an authenticated user"""
        Tag.objects.create(user=self.user, name='Italian')
        Tag.objects.create(user=self.user, name='Indian')

        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_user_tags(self):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'npassosg@gmail.com',
            'otherpassword',
        )
        Tag.objects.create(user=user2, name='Indian')

        user_tags = ['Pastries', 'Tex Mex']
        for tag in user_tags:
            Tag.objects.create(user=self.user, name=tag)

        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(user_tags))
        for tag in response.data:
            self.assertIn(tag['name'], user_tags)

    def test_create_tag_successful(self):
        """Test creation of a new tag"""
        payload = {
            'name': 'Portuguese',
        }
        self.client.post(self.API_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()

        self.assertTrue(exists)

    def test_create_empty_tag(self):
        """Test creating a new tag with an empty name"""
        payload = {
            'name': '',
        }
        response = self.client.post(self.API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags that are assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')
        recipe = Recipe.objects.create(
            user=self.user,
            name='Avocado toast',
            price=7.5,
            time_minutes=5,
        )
        recipe.tags.add(tag1)

        response = self.client.get(self.API_URL, {'assigned_only': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer1 = TagSerializer(tag1)

        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer1.data, response.data)

    def test_retrieve_tags_assigned_to_recipe_unique(self):
        """Test that filtering assigned tags are unique"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')

        recipe1 = Recipe.objects.create(
            user=self.user,
            name='Avocado toast',
            price=7.5,
            time_minutes=5,
        )
        recipe1.tags.add(tag1)

        recipe2 = Recipe.objects.create(
            user=self.user,
            name='Eggs benedict',
            price=15.0,
            time_minutes=12,
        )
        recipe2.tags.add(tag1)

        response = self.client.get(self.API_URL, {'assigned_only': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer1 = TagSerializer(tag1)

        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer1.data, response.data)
