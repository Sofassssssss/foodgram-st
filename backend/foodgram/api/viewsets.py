from django.db.models import Exists, OuterRef, Value
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet, viewsets
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .base_viewsets import ListRetrieveViewSet, ListViewSet
from .serializers import (CustomUserSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          RecipeWriteSerializer, SimplifiedRecipeSerializer)
from users.models import CustomUser
from recipes.models import (Ingredient, Recipe,
                            FavoriteRecipe, ShoppingList, ShortLink)
from .filters import RecipeFilter, IngredientFilter
from .pagination import CustomPagination


class CustomUserViewSet(UserViewSet):
    """Viewset for users."""

    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['list', 'create', 'retrieve']:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self):
        """Get serializer depending on the action."""
        if self.action == "create":
            if settings.USER_CREATE_PASSWORD_RETYPE:
                return settings.SERIALIZERS.user_create_password_retype
            return settings.SERIALIZERS.user_create
        if self.action == "set_password":
            if settings.SET_PASSWORD_RETYPE:
                return settings.SERIALIZERS.set_password_retype
            return settings.SERIALIZERS.set_password
        return self.serializer_class

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        """Get current user."""
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar_controls(self, request):
        """Update or delete avatar."""
        user = request.user

        if request.method == "PUT":
            if 'avatar' not in request.data or not request.data.get('avatar'):
                return Response(
                    {"avatar": ["Это поле не может быть пустым."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(
                user, data=request.data,
                partial=True, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": serializer.data.get("avatar")},
                            status=status.HTTP_200_OK)

        if request.method == "DELETE":
            user.avatar = None
            user.save()
            serializer = self.get_serializer(user,
                                             context={"request": request})
            return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(ListViewSet):
    """Viewset for list of user subscriptions."""

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('id',)

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class IngredientViewSet(ListRetrieveViewSet):
    """Viewset for ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

    def get_queryset(self):
        return super().get_queryset()


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset for recipes."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(user=user,
                                                  recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingList.objects.filter(user=user,
                                                recipe=OuterRef('pk'))
                )
            ).all()
        return Recipe.objects.annotate(
            is_favorited=Value(False),
            is_in_shopping_cart=Value(False)
        ).all()

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied('Вы не можете редактировать чужой рецепт.')
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied('Вы не можете удалить чужой рецепт.')
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Authentication credentials '
                                   'were not provided.')
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()

        short_link_obj, _ = ShortLink.objects.get_or_create(recipe=recipe)
        short_path = f'recipes/{short_link_obj.code}/'
        short_url = f'http://localhost/{short_path}'

        return Response({'short-link': short_url},
                        status=status.HTTP_200_OK)

    @staticmethod
    def _generate_short_code(recipe_id):
        import base64
        return (base64.urlsafe_b64encode(str(recipe_id).encode()).
                decode().rstrip('='))

    @staticmethod
    def handle_post_delete_relation(request, model, recipe, relation_name):
        user = request.user
        if request.method == 'POST':
            obj, created = (
                model.objects.get_or_create(user=user, recipe=recipe))
            if not created:
                return Response(
                    {'errors': f'Рецепт уже в {relation_name}.'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = (
                SimplifiedRecipeSerializer(recipe,
                                           context={'request': request}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=user, recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'errors': f'Рецепта нет в {relation_name}.'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_post_delete_relation(
            request=request,
            model=ShoppingList,
            recipe=recipe,
            relation_name='списке покупок'
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_post_delete_relation(
            request=request,
            model=FavoriteRecipe,
            recipe=recipe,
            relation_name='избранном'
        )
