"""
URL configuration for pms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

print("✅ Root urls.py is loaded")

admin.site.site_header = "K12 PMS"
admin.site.site_title = "K12 PMS Admin Portal"
admin.site.index_title = "Welcome to K12 Product Management System"

from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('test/', lambda request: HttpResponse("Root test route works!")),  # TEMP TEST
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('purchase_requests/', include('purchase_requests.urls')),
    path('procurement/', include('procurement.urls')),
    path('inventory/', include('inventory.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
