from rest_framework_nested.routers import DefaultRouter
from django.urls import path, include


from .viewsets import (FoodgramUserViewSet, FollowViewSet,
                       IngredientViewSet, RecipeViewSet)

router = DefaultRouter()

router.register('users/subscriptions', FollowViewSet, basename='subscriptions')
router.register('users', FoodgramUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
