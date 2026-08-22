"""Site-wide admin panel tweaks, applied by importing this module."""
from django.contrib import admin

# (heading the group sorts under, place within it). Unlisted models keep
# their alphabetical place.
INDEX_GROUPS = {
    'Bio': ("wizytówki", 0),
    'Badge': ("wizytówki", 1),
}

_default_get_app_list = admin.site.get_app_list


def _grouped_app_list(request, app_label=None):
    app_list = _default_get_app_list(request, app_label)
    for app in app_list:
        app['models'].sort(
            key=lambda model: INDEX_GROUPS.get(
                model['object_name'], (model['name'].lower(), 0),
            )
        )
    return app_list


admin.site.get_app_list = _grouped_app_list
