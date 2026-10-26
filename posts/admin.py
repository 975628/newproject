from django.contrib import admin

from .models import Comment, Like, Post, Report


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "audience", "created_at", "comments_enabled")
    list_filter = ("audience", "comments_enabled", "created_at")
    search_fields = ("author__username", "content")
    inlines = (CommentInline,)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("reporter", "post", "comment", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reporter__username", "reason")
    actions = ("mark_reviewed", "dismiss_reports")

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        queryset.update(status="reviewed")

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        queryset.update(status="dismissed")


admin.site.register(Like)
