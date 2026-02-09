"""
Role-Based Access Control Decorators

Custom decorators to protect views based on user roles:
- @role_required('admin') - Admin only
- @role_required('staff') - Panchayat Staff only
- @role_required('citizen') - Citizen only
- @role_required(['staff', 'admin']) - Multiple roles allowed
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(allowed_roles):
    """
    Decorator to restrict view access based on user role
    
    Usage:
        @role_required('admin')
        def admin_only_view(request):
            pass
        
        @role_required(['staff', 'admin'])
        def staff_and_admin_view(request):
            pass
    
    Args:
        allowed_roles: String or list of allowed role(s)
    """
    
    # Convert single role to list for uniform handling
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user_role = request.user.role
            
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    f"Access denied. This page requires {', '.join(allowed_roles)} role."
                )
                return redirect('home')
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator shortcut for admin-only views
    
    Usage:
        @admin_required
        def admin_view(request):
            pass
    """
    return role_required('admin')(view_func)


def staff_required(view_func):
    """
    Decorator shortcut for staff-only views
    
    Usage:
        @staff_required
        def staff_view(request):
            pass
    """
    return role_required('staff')(view_func)


def citizen_required(view_func):
    """
    Decorator shortcut for citizen-only views
    
    Usage:
        @citizen_required
        def citizen_view(request):
            pass
    """
    return role_required('citizen')(view_func)


def staff_or_admin_required(view_func):
    """
    Decorator shortcut for staff or admin views
    
    Usage:
        @staff_or_admin_required
        def management_view(request):
            pass
    """
    return role_required(['staff', 'admin'])(view_func)
