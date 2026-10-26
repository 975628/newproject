from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "visibility", "joined_date")
    list_filter = ("visibility", "joined_date")
    search_fields = ("user__username", "user__email", "location")
