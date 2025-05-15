from django.contrib import admin
from django.db.models import Count, OuterRef

from .models import (Ingredient, Recipe, ShortLink,
                     ShoppingList, FavoriteRecipe)

admin.site.register(ShortLink)
admin.site.register(ShoppingList)
admin.site.register(FavoriteRecipe)


class IngredientsInline(admin.StackedInline):
    """Inline form for managing ingredient relationships."""

    model = Recipe.ingredients.through
    extra = 2


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Administration panel for ingredient model.

    Search by name is available.
    """

    list_display = (
        'name',
        'measurement_unit',
    )
    list_per_page = 50
    search_fields = (
        'name',
    )
    search_help_text = 'Доступен поиск по названию ингредиента'
    actions_on_bottom = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Administration panel for recipe model."""

    list_display = (
        'name',
        'author',
    )

    inlines = (
        IngredientsInline,
    )

    fields = (
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
        'favorite_count',
    )
    readonly_fields = (
        'favorite_count',
    )
    search_fields = (
        'name',
        'author__username'
    )

    search_help_text = 'Доступен поиск по названию или автору рецепта'

    def get_queryset(self, request):
        return Recipe.objects.annotate(
            favorite_count=Count(
                FavoriteRecipe.objects.filter(
                    recipe=OuterRef('pk')).values('id')
            )
        )

    @admin.display(
        ordering='favorite_count',
        description='Число добавлений рецепта в избранное',
    )
    def favorite_count(self, obj):
        return obj.favorite_count
