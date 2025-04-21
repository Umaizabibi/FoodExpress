from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_first_name', 'user', 'phone')
    search_fields = ('user__username', 'user__first_name', 'phone')

    @admin.display(ordering='user__first_name', description='First Name')
    def get_first_name(self, obj):
        return obj.user.first_name

admin.site.register(Profile, ProfileAdmin)