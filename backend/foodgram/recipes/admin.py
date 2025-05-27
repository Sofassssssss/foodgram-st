from django.contrib import admin
from django.db.models import Count, OuterRef
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter

from .models import (Ingredient, Recipe, ShoppingList,
                     FavoriteRecipe)


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    pass


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    pass


class IngredientsInline(admin.StackedInline):
    """Inline form for managing ingredient relationships."""

    model = Recipe.ingredients.through
    extra = 2


class HasRecipesFilter(admin.SimpleListFilter):
    """Filter: does ingredient have any related recipes."""

    title = 'есть в рецептах'
    parameter_name = 'has_recipes'

    LOOKUP_CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipe__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipe__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Administration panel for ingredient model.

    Search by name is available.
    """

    list_display = (
        'name',
        'measurement_unit',
        'recipes_count',
    )
    list_per_page = 50
    search_fields = (
        'name',
        'measurement_unit'
    )
    list_filter = ('measurement_unit', HasRecipesFilter)
    search_help_text = 'Доступен поиск по названию ингредиента'
    actions_on_bottom = True

    @admin.display(ordering='recipes_ingredient',
                   description='Рецептов')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


class CookingTimeFilter(SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_group'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = list(qs.values_list('cooking_time', flat=True).distinct())
        if len(times) < 3:
            return []
        times.sort()
        n = times[len(times) // 3]
        m = times[(2 * len(times)) // 3]
        return [
            (f'lt{n}', f'быстрее {n} мин'),
            (f'range{n}_{m}', f'от {n} до {m} мин'),
            (f'gte{m}', f'долго (от {m} мин)'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if value.startswith('lt'):
                return queryset.filter(cooking_time__lt=int(value[2:]))
            elif value.startswith('gte'):
                return queryset.filter(cooking_time__gte=int(value[3:]))
            elif value.startswith('range'):
                parts = value[5:].split('_')
                if len(parts) == 2:
                    lower = int(parts[0])
                    upper = int(parts[1])
                    return queryset.filter(cooking_time__gte=lower, cooking_time__lt=upper)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Administration panel for recipe model."""

    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorite_count',
        'show_ingredients',
        'show_image',
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

    list_filter = (
        'author',
        CookingTimeFilter,
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
        description='Рецептов.',
    )
    def favorite_count(self, recipe):
        return recipe.favorite_count

    @admin.display(ordering='Ingredients',
                   description='Продукты')
    @mark_safe
    def show_ingredients(self, recipe):
        recipe_ingredients = recipe.recipe_ingredients.all()
        lines = [
            f'{ri.ingredient.name} — {ri.amount} {ri.ingredient.measurement_unit}'
            for ri in recipe_ingredients
        ]
        return '<br>'.join(lines)

    @admin.display(ordering='Image',
                   description='Изображение')
    @mark_safe
    def show_image(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="100" height="100">'
        return '—'
