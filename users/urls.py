from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/users/profile/update/'
    ), name='password_change'),
    

    # role-based dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('procurement/dashboard/', views.procurement_dashboard, name='procurement_dashboard'),
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('warehouse/dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('dashboard/', views.default_dashboard, name='default_dashboard'),  # optional fallback
]
