from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_API_URL = reverse('recipe:tag-list')


class TestPublicTagsApi(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to retrieve tags"""
        response = self.client.get(TAGS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateTagsApi(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'nhpgeraldes@gmail.com',
            'password123',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags for an authenticated user"""
        Tag.objects.create(user=self.user, name='Italian')
        Tag.objects.create(user=self.user, name='Indian')

        response = self.client.get(TAGS_API_URL)
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

        response = self.client.get(TAGS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(user_tags))
        for tag in response.data:
            self.assertIn(tag['name'], user_tags)

    def test_create_tag_successful(self):
        """Test creation of a new tag"""
        payload = {
            'name': 'Portuguese',
        }
        self.client.post(TAGS_API_URL, payload)

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
        response = self.client.post(TAGS_API_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
