from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
import random
import string

from constants import INGREDIENT_NAME_LEN, UNIT_LEN, RECIPE_LEN
from users.models import User


class Ingredient(models.Model):
    """Model for ingredient."""

    name = models.CharField(max_length=INGREDIENT_NAME_LEN,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=UNIT_LEN,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Model for recipe."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(max_length=RECIPE_LEN,
                            verbose_name='Название рецепта')
    image = models.ImageField(upload_to='recipes/', verbose_name='Картинка')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(1)])

    pub_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_recipes')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецепте'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return (f'{self.ingredient.name} — {self.amount} '
                f'({self.ingredient.measurement_unit})')


class UserAndRecipe(models.Model):
    """Special base model which contains user and recipe."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_user_recipe_unique'
            ),
        ]
        abstract = True
        ordering = ('user', 'recipe')


class FavoriteRecipe(UserAndRecipe):
    """Model for favorite recipes."""

    class Meta(UserAndRecipe.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self) -> str:
        return (f'Пользователь {self.user} добавил в '
                f'избранное рецепт {self.recipe}')


class ShoppingList(UserAndRecipe):
    """Model for shopping list."""

    class Meta(UserAndRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'

    def __str__(self) -> str:
        return f'{self.recipe} в списке покупок у {self.user}'
