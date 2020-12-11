from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Ingredient
from core.models import Recipe
from core.models import Tag
from recipe import serializers


class RecipeItemViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    """Manage items in the database"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        queryset = self.queryset
        if int(self.request.query_params.get('assigned_only', 0)):
            queryset = queryset.filter(recipe__isnull=False).distinct()
        return queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """Create a new object associated with the logged in user"""
        serializer.save(user=self.request.user)


class TagViewSet(RecipeItemViewSet):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(RecipeItemViewSet):
    """Manage ingredients in the database"""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage ingredients in the database"""
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def __params_to_ints(self, params):
        """Convert a CSV of string IDs to list of integers"""
        return list(map(int, params.split(','))) if params else []

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        queryset = self.queryset

        tags_param = self.request.query_params.get('tags', '')
        if tags_param:
            tag_ids = self.__params_to_ints(tags_param)
            queryset = queryset.filter(tags__id__in=tag_ids)

        ingredients_param = self.request.query_params.get('ingredients', '')
        if ingredients_param:
            ingredient_ids = self.__params_to_ints(ingredients_param)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
