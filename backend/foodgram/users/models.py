from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from constants import (MAX_NAME_LEN, MAX_SURNAME_LEN,
                           MAX_USERNAME_LEN, MAX_EMAIL_LEN)


class User(AbstractUser):
    """Custom user model."""

    first_name = models.CharField(
        'Имя',
        max_length=MAX_NAME_LEN
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_SURNAME_LEN,
    )

    username = models.CharField(
        'Никнейм',
        max_length=MAX_USERNAME_LEN,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
            )
        ]
    )

    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=MAX_EMAIL_LEN,
    )

    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """User subscriptions."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Фолловеры',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Авторы',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow',
            ),
        )
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self) -> str:
        return f'{self.user} subscribed to the author {self.following}'
