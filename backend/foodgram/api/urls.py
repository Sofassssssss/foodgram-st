from rest_framework_nested.routers import DefaultRouter
from django.urls import path, include


from .viewsets import (CustomUserViewSet, FollowViewSet,
                       IngredientViewSet, RecipeViewSet)
from .views import subscribes_control, download_shopping_cart

router = DefaultRouter()

router.register('users/subscriptions', FollowViewSet, basename='subscriptions')
router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('users/<int:user_id>/subscribe/',
         subscribes_control, name='subscribe'),
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name='download_shopping_cart'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
