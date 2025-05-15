from django.contrib import admin

from users.models import CustomUser, Follow

admin.site.register(Follow)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Administration panel for user model.

    Search by email and username is available.
    """

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
    )

    list_editable = (
        'is_active',
    )

    list_filter = (
        'email',
        'username',
    )

    search_fields = (
        'email',
        'username'
    )

    search_help_text = ('Доступен поиск по адресу '
                        'электронной почты или имени пользователя')
