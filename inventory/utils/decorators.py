from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def warehouse_roles_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('login')

        if request.user.role not in ['WarehouseHead']:
            messages.error(request, "You are not authorized to access this page.")
            return redirect('not_authorized')  # You can create a nice unauthorized page

        return view_func(request, *args, **kwargs)
    return wrapper
