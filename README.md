# Проект Foodgram

## Описание 

Данное веб-приложение позволяет читать и делиться рецептами, добавлять понравившиеся в избранное, а также подписываться на авторов рецептов.

Также есть возможность добавить рецепт(-ы) в корзину и скачать для них список покупок в .txt формате. 
В этом списке будут все продукты, необходимые для приготовления рецепта(-ов), а если в каких-то рецептах ингредиенты повторяются, то вы получите их суммарное количество!

Реализовано CI/CD проекта с помощью GitHub Actions.

## Стек технологий

Веб-сервер: [![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)

Frontend фреймворк: [![React](https://img.shields.io/badge/-React-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)

Backend фреймворк:   [![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)

API фреймворк: [![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)

База данных: [![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)

## Архитектура приложения 

Веб-сервер nginx перенаправляет запросы клиентов к контейнерам frontend и backend, либо к хранилищам (volume) статики и файлов.

Контейнер nginx взаимодействует с контейнером backend через gunicorn.

Контейнер frontend взаимодействует с контейнером backend посредством API-запросов.

## Документация к проекту

Документация для API после установки доступна по адресу

```url
    http://localhost/api/docs/
```

## Admin зона

Admin зона django после установки доступна по адресу

```url
    http://localhost/admin/
```

## Запуск проекта через Docker

**Для такого запуска на компьютере должно быть приложение Docker!**

1. Клонировать репозиторий и перейти в него в командной строке:

    ```bash
    git clone <ссылка с git-hub>
    ```

2. Шаблон наполнения .env можно посмотреть в файле .env.example. Файл с переменными окружения должен лежать в корневой директории.
(SECRET_KEY см. в файле backend/foodgram/foodgram/settings.py)
   
   **Переменную DB_HOST не менять!**

3. Находясь в папке infra/ поднять контейнеры

    ```bash
    docker compose up -d --build
    ```
4. По адресу http://localhost будет доступно веб-приложение


5. Выполнить миграции:

    ```bash
    docker compose exec backend python manage.py migrate
    ```

6. Собрать статику:

    ```bash
    docker compose exec backend python manage.py collectstatic --no-input
    ```

7. Наполнить базу заранее заготовленными файлами:

    **Для импорта заранее созданных пользователей.**

    ```bash
    docker compose exec backend python manage.py import_users
    ```
    
    **Для импорта ингредиентов и рецептов.**
    
    ```bash
    docker compose exec backend python manage.py import_recipes_data
    ```
   
8. Создать суперпользователя (для доступа в admin зону django):

    ```bash
    docker compose exec backend python manage.py createsuperuser
    ```
