from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.staticfiles.views import serve
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,re_path
from django.views.i18n import JavaScriptCatalog
import os



urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    re_path(
        r"^\.well-known/(?P<path>.*)$",
        serve,
        {"document_root": os.path.join(settings.BASE_DIR / ".well-known")},
    ),
]

urlpatterns += i18n_patterns(
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', admin.site.urls),
    path('',include('users.urls')),
    path('',include('core.urls')),
    path('',include('cluster.urls')),
    path('',include('destination.urls')),
   
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
       