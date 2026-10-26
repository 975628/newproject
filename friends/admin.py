from django.contrib import admin

from .models import Block, Follow, FriendRequest

admin.site.register(Follow)
admin.site.register(FriendRequest)
admin.site.register(Block)
