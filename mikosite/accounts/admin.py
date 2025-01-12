from django.contrib import admin
from .models import User, LinkedAccount, DiscordAccount


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'is_staff')
    search_fields = ('username', 'name', 'surname', 'email')
    ordering = ('-is_staff',)

admin.site.register(User, UserAdmin)
admin.site.register(LinkedAccount)
admin.site.register(DiscordAccount)
