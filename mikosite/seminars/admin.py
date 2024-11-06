from django.contrib import admin
from .models import Seminar, SeminarGroup

admin.site.register(SeminarGroup)
admin.site.register(Seminar)
