from django.contrib import admin
from .models import Project, Team, Testimonial

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'completion_date', 'is_featured', 'top_rated')
    list_filter = ('category', 'is_featured', 'top_rated')
    search_fields = ('title', 'description', 'client')
    date_hierarchy = 'completion_date'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'rating', 'is_active')
    list_filter = ('rating', 'is_active')
    search_fields = ('name', 'company', 'message')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'position', 'bio')


