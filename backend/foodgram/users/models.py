from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from api.constants import (MAX_NAME_LEN, MAX_SURNAME_LEN,
                           MAX_USERNAME_LEN, MAX_EMAIL_LEN)


class CustomUser(AbstractUser):
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
        'Имя пользователя',
        max_length=MAX_USERNAME_LEN,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Допускаются только буквы, цифры и символы @.+-_'
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
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Фолловер',
    )
    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
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
