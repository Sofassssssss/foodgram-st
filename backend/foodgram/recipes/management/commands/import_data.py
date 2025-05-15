import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str,
                            help="Путь к JSON файлу с ингредиентами")

    def handle(self, *args, **kwargs):
        """Import data from json file to db."""
        file_path = kwargs['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Ошибка при декодировании JSON файла.'))
            return

        for ingredient in ingredients_data:
            name = ingredient.get('name')
            measurement_unit = ingredient.get('measurement_unit')

            ingredient_instance, created = (
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                ))
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Ингредиент '
                                       f'"{ingredient_instance}" '
                                       f'успешно создан.'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Ингредиент '
                                       f'"{ingredient_instance}" '
                                       f'уже существует.'))

        self.stdout.write(
            self.style.SUCCESS('Импорт ингредиентов завершён.'))
