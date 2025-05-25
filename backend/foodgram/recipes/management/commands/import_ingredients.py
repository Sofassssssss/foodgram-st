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
                ingredients_data = json.load(f)
                ingredients = [Ingredient(**data) for data in ingredients_data]
                Ingredient.objects.bulk_create(ingredients)

                ingredients_count = len(ingredients)
                self.stdout.write(self.style.SUCCESS(f'Импорт ингредиентов завершён. '
                                                     f'Загружено {ingredients_count} элементов.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки продуктов: {e}'))
            return
