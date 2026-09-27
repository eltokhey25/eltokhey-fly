"""
dashboard/permissions.py
Role-based access decorators for every dashboard view.
These are the only thing standing between a logged-in staff account and the
admin, so they are applied per view rather than once at the URL level.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view):
    """Require an authenticated staff (or superuser) account.

    Anonymous visitors are redirected to the dashboard login; authenticated
    non-staff users get a 403 so a normal customer account cannot wander in.

    Args:
        view (callable): The view function to protect.

    Returns:
        callable: The wrapped view, preserving the original signature and
            name via functools.wraps.
    """
    @wraps(view)
    @login_required(login_url='dashboard:login')
    def wrapped(request, *args, **kwargs):
        """Reject the request unless the user is staff or a superuser.

        Args:
            request (HttpRequest): The incoming request.
            *args: Positional args for the protected view.
            **kwargs: Keyword args for the protected view.

        Returns:
            HttpResponse: Whatever the protected view returns.

        Raises:
            PermissionDenied: For any authenticated user without staff rights.
        """
        # is_superuser implies is_staff, but both are checked explicitly so a
        # custom user model cannot accidentally open a hole here.
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied('ليس لديك صلاحية الوصول إلى لوحة التحكم.')
        return view(request, *args, **kwargs)

    return wrapped


def superuser_required(view):
    """Restrict a view to superusers only (user management).

    Stacks on top of staff_required, so the wrapped view is safe to mount
    without repeating the login check.

    Args:
        view (callable): The view function to protect.

    Returns:
        callable: The wrapped view.
    """
    @wraps(view)
    @staff_required
    def wrapped(request, *args, **kwargs):
        """Reject the request unless the user is a superuser.

        Args:
            request (HttpRequest): The incoming request.
            *args: Positional args for the protected view.
            **kwargs: Keyword args for the protected view.

        Returns:
            HttpResponse: Whatever the protected view returns.

        Raises:
            PermissionDenied: For staff accounts that are not superusers.
        """
        if not request.user.is_superuser:
            raise PermissionDenied('إدارة المستخدمين متاحة لمدير النظام فقط.')
        return view(request, *args, **kwargs)

    return wrapped