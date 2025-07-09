from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, render
from django.contrib import messages
from .forms import ProfileUpdateForm
from django.contrib.auth.decorators import login_required


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # login using username
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Redirect based on role
            if user.role == 'Admin':
                return redirect('main_dashboard')
            elif user.role == 'ProcurementManager':
                return redirect('procurement_dashboard')
            elif user.role == 'DepartmentUser':
                return redirect('department_dashboard')
            elif user.role == 'WarehouseHead':
                return redirect('warehouse_dashboard')
            elif user.role == 'WarehouseManager':
                return redirect('warehouse_dashboard')
            else:
                return redirect('default_dashboard')  # fallback
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'main_app/login.html')



def logout_user(request):
    if request.user is not None:
        logout(request)
    return redirect("/")

@login_required
def update_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # redirect to profile or home page
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'users/update_profile.html', {'form': form, 'page_title': 'Update Profile'})




def admin_dashboard(request):
    return render(request, 'dashboards/admin.html')

def procurement_dashboard(request):
    return render(request, 'procurement/home_content.html')

def department_dashboard(request):
    return render(request, 'inventory/home_content.html')

def warehouse_dashboard(request):
    return render(request, 'inventory/home_content.html')

def default_dashboard(request):
    return render(request, 'dashboards/default.html')