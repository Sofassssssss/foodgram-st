from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (Recipe, Ingredient,
                            FavoriteRecipe, ShoppingList, RecipeIngredient)

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
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
        read_only_fields = fields
        model = User

    def get_is_subscribed(self, obj):
        """Check subscribe."""
        user = self.context['request'].user
        return user.is_authenticated and user.follows.filter(
            following=obj).exists()


class SimplifiedRecipeSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for recipes.

    It is used in displaying recipes of people who are
    subscribed to by the user.
    """

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = fields
        model = Recipe


class FollowUserSerializer(FoodgramUserSerializer):
    """Subscriptions serializer."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
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
        read_only_fields = fields

    def get_recipes(self, obj):
        """Get related recipes."""
        recipes_limit = int(
            self.context.get('request').query_params.get('recipes_limit', 10 ** 10)
        )
        return SimplifiedRecipeSerializer(
            obj.recipes.all()[:recipes_limit], many=True, context=self.context
        ).data


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """
    Serializer for ingredients in recipe.
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
        read_only_fields = fields
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


class RecipeReadSerializer(serializers.ModelSerializer):
    """Recipe serializer."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = FoodgramUserSerializer()
    ingredients = IngredientRecipeReadSerializer(source='recipe_ingredients',
                                                 many=True, read_only=True)

    class Meta:
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')
        read_only_fields = fields
        model = Recipe

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated and
                FavoriteRecipe.objects.filter(user=user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingList.objects.filter(user=user, recipe=obj).exists()
        return False


class IngredientRecipeWriteSerializer(serializers.Serializer):
    """
    Serializers for ingredients in recipe.

    Write is available
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Serializers  recipe.

    Write is available.
    """

    author = FoodgramUserSerializer(
        read_only=True, default=CurrentUserDefault())
    image = Base64ImageField()
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'cooking_time',
        )
        model = Recipe

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')

        if ingredients is None:
            raise ValidationError('Ингредиенты должны быть указаны.')

        if not ingredients:
            raise ValidationError('Нельзя сохранить рецепт без ингредиентов.')

        ingredients_id_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            ingredients_id_list.append(ingredient_id)

        if len(ingredients_id_list) != len(set(ingredients_id_list)):
            raise ValidationError('Один ингредиент нельзя написать дважды.')

        image = attrs.get('image')
        if not image:
            raise ValidationError({'image': 'Это поле не может быть пустым.'})

        return attrs

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data

    @staticmethod
    def _add_ingredients(recipe, ingredients):
        """Add list of ingredients of recipe."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'].id,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self._add_ingredients(
            super().update(instance, validated_data),
            ingredients
        )
        return instance
