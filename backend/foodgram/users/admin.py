from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from users.models import User, Follow
from recipes.models import Recipe


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Administration panel for user model.

    Search by email and username is available.
    """

    model = User

    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_tag',
        'recipe_count',
        'following_count',
        'follows_count',
        'is_active',
    )

    list_editable = (
        'is_active',
    )

    search_fields = (
        'email',
        'username'
    )

    search_help_text = ('Доступен поиск по адресу '
                        'электронной почты или имени пользователя')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {
            'fields': ('avatar',)
        }),
    )

    @admin.display(description='ФИО')
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_tag(self, obj):
        if obj.avatar:
            return (f'<img src="{obj.avatar.url}" width="50" height="50" '
                    f'style="object-fit: cover; border-radius: 50%;" />')
        return '—'

    @admin.display(description='Рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписок')
    def following_count(self, obj):
        return obj.follows.count()

    @admin.display(description='Подписчиков')
    def follows_count(self, obj):
        return obj.authors.count()
