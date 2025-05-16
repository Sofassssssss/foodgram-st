import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from users.models import CustomUser


class Command(BaseCommand):
    help = 'Импортирует пользователей из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str,
                            help="Путь к JSON файлу с пользователями")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']

        CustomUser.objects.all().delete()
        self.stdout.write(self.style.WARNING('Все записи CustomUser удалены перед импортом.'))

        User = CustomUser

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Ошибка при декодировании JSON файла.'))
            return

        for item in users_data:
            email = item.get('email')
            username = item.get('username')
            first_name = item.get('first_name', '')
            last_name = item.get('last_name', '')
            password = item.get('password')

            if not (email and username and password):
                self.stdout.write(self.style.WARNING(
                    f'Пропущена запись с недостающими обязательными полями: {item}'))
                continue

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Пользователь "{username}" успешно создан.'))
            else:
                self.stdout.write(self.style.WARNING(f'Пользователь "{username}" уже существует.'))

        self.stdout.write(self.style.SUCCESS('Импорт пользователей завершён.'))
