from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):

    # has_permission 就是看你有没有 view write 权限（所有请求类型都回过来）
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if not request.user.is_superuser:
                return False
            else:
                return True

    # has_object_permission 是对单个结果， 比如 id 为 1 的数据 判断你有没有权限(也就是put/delete请求才会过来)
    # def has_object_permission(self, request, view, obj):
    #     # Read permissions are allowed to any request,
    #     # so we'll always allow GET, HEAD or OPTIONS requests.
    #     if request.method in permissions.SAFE_METHODS:
    #         return True
    #     else:
    #         if not request.user.is_superuser:
    #             return False
    #         else:
    #             return True

