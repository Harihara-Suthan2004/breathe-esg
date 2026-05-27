"""
URL configuration for core_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ingestion.urls')),  
]

# --- AUTOMATIC PRODUCTION SUPERUSER WORKAROUND ---
# Since Render's Free Tier blocks access to the interactive 'Shell' feature,
# this code programmatically generates your core admin credentials on application boot.
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("No administrative profiles located. Seeding default superuser configuration...")
        User.objects.create_superuser(
            username='admin',
            email='admin@breatheesg.com',
            password='ProductionAdminPassword123!'
        )
        print("Superuser account 'admin' provisioned successfully.")
except Exception as e:
    print(f"Superuser seeding cycle bypassed or database context uninitialized: {e}")