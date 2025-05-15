from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    """Special filter set for recipes."""

    is_favorited = filters.Filter(field_name='is_favorited')
    is_in_shopping_cart = filters.Filter(field_name='is_in_shopping_cart')
    author = filters.Filter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = [
            'is_favorited',
            'is_in_shopping_cart',
            'author',
        ]


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
