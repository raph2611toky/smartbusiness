from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .views import swagger_password_protect
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Smart Business",
        default_version='v1',
        description="API pour Smart Business",
        terms_of_service="#",
        contact=openapi.Contact(email="contact@monapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[AllowAny]
)

protected_swagger = swagger_password_protect(schema_view.with_ui('swagger', cache_timeout=0))
protected_redoc = swagger_password_protect(schema_view.with_ui('redoc', cache_timeout=0))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    
    path('api/docs/', protected_swagger, name='schema-swagger-ui'),
    path('api/redoc/', protected_redoc, name='schema-redoc'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)