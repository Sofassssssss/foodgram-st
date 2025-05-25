import json
import os
import shutil
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.conf import settings
from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class Command(BaseCommand):
    help = 'Импортирует рецепты и связи RecipeIngredient из JSON файлов'

    RECIPES_FILE = os.path.join(settings.BASE_DIR, 'data', 'recipes.json')
    RECIPE_INGREDIENTS_FILE = os.path.join(settings.BASE_DIR, 'data', 'recipe_ingredients.json')
    PHOTOS_SRC_DIR = os.path.join(settings.BASE_DIR, 'data', 'recipes_photo')
    PHOTOS_DST_DIR = os.path.join(settings.MEDIA_ROOT, 'recipes')

    def handle(self, *args, **kwargs):
        self.import_recipes()
        self.import_recipe_ingredients()

    def import_recipes(self):
        os.makedirs(self.PHOTOS_DST_DIR, exist_ok=True)
        copied = 0
        for filename in os.listdir(self.PHOTOS_SRC_DIR):
            src_path = os.path.join(self.PHOTOS_SRC_DIR, filename)
            dst_path = os.path.join(self.PHOTOS_DST_DIR, filename)
            if os.path.isfile(src_path):
                shutil.copy(src_path, dst_path)
                copied += 1
        self.stdout.write(self.style.SUCCESS(f'Скопировано {copied} изображений.'))

        try:
            with open(self.RECIPES_FILE, 'r', encoding='utf-8') as f:
                recipes_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки рецептов: {e}'))
            return

        Recipe.objects.all().delete()
        self.stdout.write(self.style.WARNING('Все рецепты удалены перед импортом.'))

        for item in recipes_data:
            try:
                author = User.objects.get(id=item.get('author'))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Автор id={item.get("author")} не найден.'))
                continue

            pub_date = parse_datetime(item.get('pub_date')) if item.get('pub_date') else None

            recipe, created = Recipe.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'author': author,
                    'name': item.get('name'),
                    'image': item.get('image'),
                    'text': item.get('text'),
                    'cooking_time': item.get('cooking_time'),
                    'pub_date': pub_date
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Рецепт "{recipe.name}" {"создан" if created else "обновлён"}'))

        self.stdout.write(self.style.SUCCESS('Импорт рецептов завершён.'))

    def import_recipe_ingredients(self):
        try:
            with open(self.RECIPE_INGREDIENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки RecipeIngredient: {e}'))
            return

        RecipeIngredient.objects.all().delete()
        self.stdout.write(self.style.WARNING('Все RecipeIngredient удалены перед импортом.'))

        for item in data:
            try:
                recipe = Recipe.objects.get(id=item['recipe'])
                ingredient = Ingredient.objects.get(id=item['ingredient'])
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=item['amount']
                )
            except (Recipe.DoesNotExist, Ingredient.DoesNotExist):
                self.stdout.write(self.style.WARNING(
                    f'Пропущена запись: рецепт={item.get("recipe")}, ингредиент={item.get("ingredient")}'))

        self.stdout.write(self.style.SUCCESS('Импорт RecipeIngredient завершён.'))
