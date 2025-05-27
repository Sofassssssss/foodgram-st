import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты  из JSON файлов'

    INGREDIENTS_FILE = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')

    def handle(self, *args, **kwargs):
        try:
            with open(self.INGREDIENTS_FILE, 'r', encoding='utf-8') as f:
                ingredients = [Ingredient(**data) for data in json.load(f)]
                ingredients_to_insert = Ingredient.objects.count()
                Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

                inserted_ingredients = Ingredient.objects.count()

                inserted_count = inserted_ingredients - ingredients_to_insert
                self.stdout.write(self.style.SUCCESS(f'Импорт продуктов завершён. '
                                                     f'Загружено {inserted_count} элементов.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки продуктов '
                                               f'из файла {self.INGREDIENTS_FILE}: {e}'))
