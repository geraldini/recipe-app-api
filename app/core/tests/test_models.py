from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models


def sample_user(email='test@gmail.com', password='somepassword'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class TestModels(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email -- successfully"""
        email = "test@gmail.com"
        password = "passwordTest!23"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_user_email_normalized(self):
        """Test the email for a new iser is normalized"""
        email = "test@GMAIL.com"
        user = get_user_model().objects.create_user(email, 'test123')
        self.assertEqual(user.email, email.lower())

    def test_create_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_superuser(self):
        """Test creation of a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Indian',
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Rice',
        )
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            name='Chicken Tikka Masala',
            time_minutes=5,
            price=4.0,
        )
        self.assertEqual(str(recipe), recipe.name)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        test_uuid = 'test-uuid'
        mock_uuid.return_value = test_uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        expected_path = f'uploads/recipe/{test_uuid}.jpg'
        self.assertEqual(file_path, expected_path)
