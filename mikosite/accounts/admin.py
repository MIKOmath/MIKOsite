from django.contrib import admin
from .models import User, LinkedAccount


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-is_superuser', '-is_staff', 'username')

admin.site.register(User, UserAdmin)
admin.site.register(LinkedAccount)
