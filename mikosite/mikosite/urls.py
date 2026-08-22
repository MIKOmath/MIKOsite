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

from rest_framework.permissions import AllowAny
from rest_framework.routers import APIRootView, DefaultRouter
from seminars.api_views import (
    CalendarViewSet,
    GoogleFormViewSet,
    PreviousEditionViewSet,
    ReminderViewSet,
    SeminarGroupViewSet,
    SeminarViewSet,
)
from accounts import views as account_views
from seminars import views as seminar_views
from mainSite.api_views import (
    PartnerViewSet,
    PostViewSet,
    RegistrationEventViewSet,
)
from olympiads.api_views import OlympiadStageViewSet, OlympiadViewSet
from accounts.api_views import UserViewSet, LinkedAccountViewSet, UserActivityViewSet, ActivityScoreViewSet


class PublicAPIRootView(APIRootView):
    """Index of available endpoints."""

    permission_classes = (AllowAny,)


class PublicRootRouter(DefaultRouter):
    APIRootView = PublicAPIRootView


router = PublicRootRouter()
router.register(r'calendar', CalendarViewSet, basename='calendar')
router.register(r'seminar-groups', SeminarGroupViewSet)
router.register(r'seminars', SeminarViewSet)
router.register(r'previous-editions', PreviousEditionViewSet)
router.register(r'olympiads', OlympiadViewSet)
router.register(r'olympiad-stages', OlympiadStageViewSet)
router.register(r'registration-events', RegistrationEventViewSet)
router.register(r'partners', PartnerViewSet)
router.register(r'posts', PostViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'linked-accounts', LinkedAccountViewSet)
router.register(r'user-activity', UserActivityViewSet, basename='user-activity')
router.register(r'activity-scores', ActivityScoreViewSet)
router.register(r'google-form-template', GoogleFormViewSet)
router.register(r'reminders', ReminderViewSet)

urlpatterns = [
    # Ahead of the admin's own URLs, so its login form is never reached.
    path('admin/login/', account_views.admin_login),
    path('admin/', admin.site.urls),
    path("", include("mainSite.urls")),
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('kolo/', include('seminars.urls')),
    path('editions/', seminar_views.previous_editions, name='previous_editions'),
    # path("bazahintow/", include("hintBase.urls")),
    path('api/', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns.extend(debug_toolbar_urls())

handler400 = 'mainSite.views.bad_request'
handler403 = 'mainSite.views.permission_denied'
handler404 = 'mainSite.views.page_not_found'
handler500 = 'mainSite.views.server_error'

admin.site.site_header = "TEST Admin Panel MIKO" if settings.DEBUG else "Administracja MIKO"
admin.site.site_title = "MIKO Admin"
