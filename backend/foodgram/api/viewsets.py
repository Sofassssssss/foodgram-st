from collections import defaultdict
from datetime import datetime
import re
from django.http import FileResponse
from io import BytesIO
from django.db.models import Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import viewsets, UserViewSet
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import (FollowUserSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SimplifiedRecipeSerializer)
from recipes.models import (Ingredient, Recipe,
                            FavoriteRecipe, ShoppingList, RecipeIngredient)
from users.models import Follow
from .filters import RecipeFilter, IngredientFilter
from .pagination import Pagination
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class MyUserViewSet(UserViewSet):
    """Viewset for users."""

    queryset = User.objects.all()
    pagination_class = Pagination

    @action(["get"], detail=False, permission_classes=(IsAuthenticated, ))
    def me(self, request, *args, **kwargs):
        """Get current user."""
        user = request.user
        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar",
            permission_classes=(IsAuthenticated, ))
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

        else:
            user.avatar = None
            user.save()
            serializer = self.get_serializer(user,
                                             context={"request": request})
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe",
            permission_classes=(IsAuthenticated,))
    def subscribes_control(self, request, id=None):
        """
        Create or delete subscription to the user.
        """
        user = request.user
        following = get_object_or_404(User, pk=id)

        if request.method == "POST":
            if user == following:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, following=following)

            try:
                limit = int(request.query_params.get('recipes_limit', 0))
            except ValueError:
                limit = 0

            recipes_qs = following.recipes.all()
            if limit > 0:
                recipes_qs = recipes_qs[:limit]

            recipes_list = []
            for recipe in recipes_qs:
                recipes_list.append({
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': request.build_absolute_uri(recipe.image.url) if recipe.image else None,
                    'cooking_time': recipe.cooking_time,
                })

            response_data = {
                "email": following.email,
                "id": following.id,
                "username": following.username,
                "first_name": following.first_name,
                "last_name": following.last_name,
                "is_subscribed": True,
                "recipes": recipes_list,
                "recipes_count": recipes_qs.count(),
                "avatar": request.build_absolute_uri(following.avatar.url) if following.avatar else None,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        else:
            """
            В ревью к строкам 134:140 был написан комментарий 
            Замените на get_object_or_404(...).delete().
            Однако в документации к API написано:
             400 Ошибка отписки (Например, если не был подписан)
             Следовательно при изменении кода следуя комментарию, postman_collection не проходит,
             был оставлен изначальный код.
            """
            follow_instance = Follow.objects.filter(user=user, following=following).first()
            if not follow_instance:
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Viewset for list of user subscriptions."""

    serializer_class = FollowUserSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('id',)

    def get_queryset(self):
        return User.objects.filter(pk__in=self.request.user.
                                   follows.values_list('following', flat=True))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class IngredientViewSet(ReadOnlyModelViewSet):
    """Viewset for ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset for recipes."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)
    pagination_class = Pagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

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

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        self.get_object()
        recipe_url = reverse('recipes:get_recipe_link', args=(pk,))
        absolute_url = request.build_absolute_uri(recipe_url)

        return Response({'short-link': absolute_url},
                        status=status.HTTP_200_OK)

    @staticmethod
    def handle_post_delete_relation(request, model, recipe):
        user = request.user
        if request.method == 'POST':
            obj, created = (
                model.objects.get_or_create(user=user, recipe=recipe))
            if not created:
                return Response(
                    {'errors': f'Рецепт "{recipe.name}" уже '
                               f'в {model._meta.verbose_name}.'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = (
                SimplifiedRecipeSerializer(recipe,
                                           context={'request': request}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            """
            В ревью был написан комментарий
            Рекомендую заменить строки 208:213 (сейчас это строки 200:205) на get_object_or_404(...).delete().
            Однако в документации к API написано:
             400 Ошибка удаления из списка покупок (Например, когда рецепта там не было)
             Следовательно при изменении кода следуя комментарию, postman_collection не проходит,
             был оставлен изначальный код.
            """
            deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'errors': f'Рецепта "{recipe.name}" нет '
                               f'в {model._meta.verbose_name}.'},
                    status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_post_delete_relation(
            request=request,
            model=ShoppingList,
            recipe=recipe
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Download shopping cart as txt."""
        user = request.user
        recipes = Recipe.objects.filter(shopping_cart__user=user)
        ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)

        shopping_data = defaultdict(float)

        for item in ingredients:
            ingredient_name = item.ingredient.name
            ingredient_name_upper = ingredient_name[0].upper() + ingredient_name[1:]
            key = f"{ingredient_name_upper} ({item.ingredient.measurement_unit})"
            shopping_data[key] += item.amount

        product_lines = []
        for idx, (ingredient, amount) in enumerate(shopping_data.items(), start=1):
            match = re.search(r'\((.*?)\)', ingredient)
            measurement_unit = match.group(1) if match else ''
            ingredient_name = re.sub(r'\s*\(.*?\)', '', ingredient).strip()
            product_lines.append(f"{idx}. {ingredient_name} — {amount} {measurement_unit}")

        recipe_lines = []
        unique_recipes = set()
        for recipe in recipes:
            if recipe not in unique_recipes:
                unique_recipes.add(recipe)
                author_name = recipe.author.get_full_name() or recipe.author.username
                recipe_lines.append(f"{recipe.name} (Автор: {author_name})")

        content = '\n'.join([
            f"Список покупок. Составлен: {datetime.now().strftime('%d %b %Y %H:%M:%S')}.",
            "",
            "Продукты:",
            *product_lines,
            "",
            "Рецепты:",
            *recipe_lines,
        ])

        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)

        response = FileResponse(buffer, as_attachment=True, filename='shopping-list.txt')
        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_post_delete_relation(
            request=request,
            model=FavoriteRecipe,
            recipe=recipe,
        )
