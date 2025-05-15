from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
import random
import string

from api.constants import INGREDIENT_NAME_LEN, UNIT_LEN, RECIPE_LEN
from users.models import CustomUser


class Ingredient(models.Model):
    """Model for ingredient."""

    name = models.CharField(max_length=INGREDIENT_NAME_LEN,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=UNIT_LEN,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
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
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(max_length=RECIPE_LEN,
                            verbose_name='Название рецепта')
    image = models.ImageField(upload_to='recipes/', verbose_name='Картинка')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(1,
                              "Время приготовления рецепта "
                              "не должно быть меньше 1 минуты.")])

    pub_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class ShortLink(models.Model):
    """Model for short link to recipe."""

    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE,
                                  related_name='short_link',
                                  verbose_name='Рецепт', )
    code = models.CharField(max_length=10, unique=True, editable=False,
                            verbose_name='Уникальный код')

    class Meta:
        verbose_name = 'Короткая ссылка на рецепт'
        verbose_name_plural = 'Короткие ссылки на рецепт'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_code():
        while True:
            code = ''.join(random.choices(
                string.ascii_letters + string.digits, k=6))
            if not ShortLink.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f'{self.recipe}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_recipes')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1,
                                      "Рецепт должен состоять "
                                      "хотя бы из 2 ингредиентов.")])

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
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
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ['user', 'recipe']


class FavoriteRecipe(UserAndRecipe):
    """Model for favorite recipes."""

    class Meta(UserAndRecipe.Meta):
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'user', ],
                name='unique_favorite_recipe'
            ),
        )
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'

    def __str__(self) -> str:
        return (f'Пользователь {self.user} добавил в '
                f'избранное рецепт {self.recipe}')


class ShoppingList(UserAndRecipe):
    """Model for shopping list."""

    class Meta(UserAndRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'user', ],
                name='unique_shopping_list'
            ),
        )

    def __str__(self) -> str:
        return f'{self.recipe} в списке покупок у {self.user}'
