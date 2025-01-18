"""
URL configuration for mikosite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from seminars.api_views import SeminarGroupViewSet, SeminarViewSet, GoogleFormViewSet
from mainSite.api_views import PostImageViewSet, PostViewSet
from accounts.api_views import UserViewSet, LinkedAccountViewSet, UserActivityViewSet, ActivityScoreViewSet

router = DefaultRouter()
router.register(r'seminar-groups', SeminarGroupViewSet)
router.register(r'seminars', SeminarViewSet)
router.register(r'posts', PostViewSet)
router.register(r'post-images', PostImageViewSet)
router.register(r'users', UserViewSet)
router.register(r'linked-accounts', LinkedAccountViewSet)
router.register(r'user-activity', UserActivityViewSet, basename='user-activity')
router.register(r'activity-scores', ActivityScoreViewSet)
router.register(r'google-form-template', GoogleFormViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("mainSite.urls")),
    path('', include('accounts.urls')),
    path('kolo/', include('seminars.urls')),
    path("bazahintow/", include("hintBase.urls")),
    path('api/', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "TEST Admin Panel MIKO" if settings.DEBUG else "Administracja MIKO"
admin.site.site_title = "MIKO Admin"
