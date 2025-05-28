import json
import os
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = ('Импортирует пользователей из JSON файла '
            '(без передачи пути через командную строку)')

    def handle(self, *args, **kwargs):
        file_path = os.path.join('data', 'users_hashed.json')

        User.objects.all().delete()
        self.stdout.write(self.style.WARNING('Все записи User '
                                             'удалены перед импортом.'))

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
