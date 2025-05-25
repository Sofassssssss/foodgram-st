from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to any user.

    Write permissions are granted only to the authenticated
    author of the object.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author == request.user


# class UserPermission(permissions.BasePermission):
#
#     def has_permission(self, request, view):
#         if view.action in ['list', 'retrieve', 'create']:
#             return True
#         return request.user and request.user.is_authenticated

