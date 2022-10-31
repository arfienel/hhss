from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        print(obj)
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user_creator == request.user