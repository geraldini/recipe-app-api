from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('tag', views.TagViewSet)
router.register('ingredient', views.IngredientViewSet)
router.register('recipe', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
