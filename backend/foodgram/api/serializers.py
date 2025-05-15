import base64
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from rest_framework.exceptions import ValidationError

from users.models import CustomUser, Follow
from recipes.models import (Recipe, Ingredient,
                            FavoriteRecipe, ShoppingList, RecipeIngredient)


class FavoriteShoppingMixin:
    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return (FavoriteRecipe.
                    objects.filter(user=user, recipe=obj).exists())
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingList.objects.filter(user=user, recipe=obj).exists()
        return False


class Base64ImageField(serializers.ImageField):
    """
    Custom Django REST Framework Base64 field.

    Used for handling image uploads encoded in Base64 format.

    Example base64 input:

    data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """User serializer."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        model = CustomUser

    def get_is_subscribed(self, obj):
        """Check subscribe."""
        user = self.context['request'].user
        return user.is_authenticated and user.follower.filter(
            following=obj).exists()

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class SimplifiedRecipeSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for recipes.

    It is used in displaying recipes of people who are
    subscribed to by the user.
    """

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    image = serializers.ImageField(read_only=True)
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class FollowSerializer(serializers.ModelSerializer):
    """Subscriptions serializer."""

    id = serializers.ReadOnlyField(source='following.id')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    username = serializers.ReadOnlyField(source='following.username')
    email = serializers.ReadOnlyField(source='following.email')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(source='following.avatar', required=False)

    class Meta:
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        model = Follow

    def get_recipes(self, obj):
        """Get related recipes."""
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        queryset = obj.following.recipes.all()
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        serializer = SimplifiedRecipeSerializer(queryset, many=True)
        return serializer.data

    def validate(self, data):
        request_user = self.context['request'].user
        target_user_id = self.context.get('user_id')

        if request_user.id == target_user_id:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя.'
            )

        if (self.context['request'].method == "POST" and Follow.objects.filter(
                user=request_user,
                following_id=target_user_id
                ).exists()):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого человека, '
                'подписаться дважды нельзя.'
            )
        if (self.context['request'].method == "DELETE" and not
            Follow.objects.filter(
            user=request_user,
            following_id=target_user_id
        ).exists()):
            raise serializers.ValidationError(
                'Вы не можете отписаться от того, на кого не подписывались.'
            )
        return data

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=self.context['request'].user,
                                     following=obj.following).exists()

    @staticmethod
    def get_recipes_count(obj):
        return obj.following.recipes.count()


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for ingredients in recipe.

    Only for reading.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )
        model = RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    """Ingredients serializer."""

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredient


class RecipeSerializer(FavoriteShoppingMixin,
                       serializers.ModelSerializer):
    """Recipe serializer."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer()
    ingredients = IngredientRecipeSerializer(source='recipe_ingredients',
                                             many=True, read_only=True)

    class Meta:
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')
        model = Recipe


class IngredientRecipeWriteSerializer(serializers.Serializer):
    """
    Serializers for ingredients in recipe.

    Write is available
    """

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(FavoriteShoppingMixin,
                            serializers.ModelSerializer):
    """
    Serializers  recipe.

    Write is available.
    """

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(
        read_only=True, default=CurrentUserDefault())
    image = Base64ImageField()
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )

    class Meta:
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )
        read_only_fields = (
            'author',
        )
        model = Recipe

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')

        if self.instance:
            if ingredients is None:
                raise ValidationError('Ингредиенты '
                                      'обязательны при обновлении рецепта.')

        if ingredients is None:
            raise ValidationError('Ингредиенты должны быть указаны.')

        if not ingredients:
            raise ValidationError('Нельзя сохранить рецепт без ингредиентов.')

        ingredients_id_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            if not ingredient_id:
                raise ValidationError('Каждый ингредиент должен содержать id.')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise ValidationError(f'Ингредиент с id '
                                      f'{ingredient_id} не существует.')
            ingredients_id_list.append(ingredient_id)

        if len(ingredients_id_list) != len(set(ingredients_id_list)):
            raise ValidationError('Не надо писать ингредиент дважды, '
                                  'лучше суммировать их.')

        return attrs

    def get_is_favorited(self, obj):
        """Check that recipe is favorite."""
        return (FavoriteRecipe.objects.filter
                (user=self.context['request'].user,
                 recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        """Check that recipe in shopping cart."""
        return ShoppingList.objects.filter(user=self.context['request'].user,
                                           recipe=obj).exists()

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    @staticmethod
    def _add_ingredients(recipe, ingredients):
        """Add list of ingredients of recipe."""
        data = []
        for ingredient in ingredients:
            data.append(RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ))
        RecipeIngredient.objects.bulk_create(data)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        instance.save()
        self._add_ingredients(instance, ingredients)
        return instance
