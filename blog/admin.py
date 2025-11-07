# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Post, Page, Category, Comment, UserProfile


class BaseContentAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    actions = ['move_to_trash', 'restore_from_trash', 'mark_as_published', 'mark_as_draft']
    
    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()
    
    def status_badge(self, obj):
        if obj.is_trashed:
            return format_html('<span style="color: #dc3545;">🗑️ Trashed</span>')
        
        colors = {'draft': '#ffc107', 'published': '#28a745'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#666'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def move_to_trash(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.move_to_trash(user=request.user)
            count += 1
        self.message_user(request, f'{count} item(s) moved to trash.')
    move_to_trash.short_description = 'Move selected to trash'
    
    def restore_from_trash(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_trashed=True):
            obj.restore_from_trash()
            count += 1
        self.message_user(request, f'{count} item(s) restored from trash.')
    restore_from_trash.short_description = 'Restore from trash'
    
    def mark_as_published(self, request, queryset):
        queryset.update(status='published', published_date=timezone.now())
    mark_as_published.short_description = 'Mark as published'
    
    def mark_as_draft(self, request, queryset):
        queryset.update(status='draft')
    mark_as_draft.short_description = 'Mark as draft'


@admin.register(Post)
class PostAdmin(BaseContentAdmin):
    list_display = ['title', 'author_display_name', 'status_badge', 'is_featured', 'published_date', 'page_views']
    list_filter = ['status', 'is_featured', 'is_trashed', 'category', 'created_at']
    search_fields = ['title', 'content', 'author_name']
    filter_horizontal = ['category']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt', 'featured_image')
        }),
        ('Post Settings', {
            'fields': ('category', 'is_featured'),
        }),
        ('Publishing', {
            'fields': ('status', 'published_date')
        }),
        ('SEO', {
            'fields': ('seo_description', 'seo_keywords'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('read_time', 'page_views'),
            'classes': ('collapse',)
        }),
    ]
    
    def get_changeform_initial_data(self, request):
        return {'author': request.user}
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Page)
class PageAdmin(BaseContentAdmin):
    list_display = ['title', 'status_badge', 'published_date', 'page_views']
    list_filter = ['status', 'is_trashed', 'created_at']
    search_fields = ['title', 'content']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        ('Publishing', {
            'fields': ('status', 'published_date')
        }),
        ('SEO', {
            'fields': ('seo_description', 'seo_keywords'),
        }),
    ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at', 'order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def post_count(self, obj):
        return obj.posts.filter(is_trashed=False).count()
    post_count.short_description = 'Posts'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'created_on', 'approved']
    list_filter = ['approved', 'created_on']
    search_fields = ['name', 'email', 'body']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'bio',)
    search_fields = ('user__username', 'user__email', 'bio')