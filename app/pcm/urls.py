from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Admin Website PCM"
admin.site.site_title = "Admin PCM"
admin.site.index_title = "Kelola konten website"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("website.urls")),
]

# Local development only; on EC2, Nginx (Level 1) or S3 (Level 2+) serves media.
if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
