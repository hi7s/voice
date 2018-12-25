from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
                  url(r'^', include('blog.urls')),
                  url(r'^blog/', include('blog.urls')),
                  url(r'^admin/', include(admin.site.urls)),
                  url(r'^ckeditor/', include('ckeditor_uploader.urls'))
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
