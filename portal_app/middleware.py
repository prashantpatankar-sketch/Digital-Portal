"""
Role-Based Access Control Middleware

This middleware enforces role-based access control rules:
- Admin: Full access to /admin/ routes
- Panchayat Staff: Access to /staff/ routes
- Citizen: Access to /citizen/ routes
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based URL access control
    
    Access Rules:
    - /admin/ routes: Admin only
    - /staff/ routes: Panchayat Staff and Admin
    - /citizen/ routes: Citizens and all authenticated users
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for unauthenticated users (let login_required handle it)
        if not request.user.is_authenticated:
            return None
        
        # Get the current path
        path = request.path
        user_role = request.user.role
        
        # Define role-based access rules
        management_paths = [
            '/admin-dashboard/',
            '/panel/',
        ]
        staff_paths = ['/staff-dashboard/', '/staff/applications/', '/staff/review/']
        citizen_paths = [
            '/dashboard/',
            '/apply/',
            '/my-applications/',
            '/application/',
            '/pay-tax/',
            '/file-complaint/',
            '/my-complaints/',
            '/complaint/',
        ]
        
        # Check management routes (staff and admin)
        if any(path.startswith(management_path) for management_path in management_paths):
            if user_role not in ['staff', 'admin']:
                messages.error(request, "Access denied. Staff or admin privileges required.")
                return redirect('home')
        
        # Check staff routes
        elif any(path.startswith(staff_path) for staff_path in staff_paths):
            if user_role not in ['staff', 'admin']:
                messages.error(request, "Access denied. Panchayat Staff privileges required.")
                return redirect('home')
        
        # Check citizen routes
        elif any(path.startswith(citizen_path) for citizen_path in citizen_paths):
            # All authenticated users can access citizen routes
            pass
        
        return None
