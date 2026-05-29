from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/companies/', include('companies.urls')),
    path('api/emissions/', include('emissions.urls')),
    path('api/ingestion/', include('ingestion.urls')),
    path('api/audit/', include('audit.urls')),
]
