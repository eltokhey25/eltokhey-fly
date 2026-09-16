from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view):
    @wraps(view)
    @login_required(login_url='dashboard:login')
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied('ليس لديك صلاحية الوصول إلى لوحة التحكم.')
        return view(request, *args, **kwargs)

    return wrapped


def superuser_required(view):
    @wraps(view)
    @staff_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied('إدارة المستخدمين متاحة لمدير النظام فقط.')
        return view(request, *args, **kwargs)

    return wrapped