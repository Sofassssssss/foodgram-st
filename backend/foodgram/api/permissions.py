from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to any user.

    Write permissions are granted only to the authenticated
    author of the object.
    """

    message = 'У вас недостаточно прав для редактирования.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and obj.author == request.user
