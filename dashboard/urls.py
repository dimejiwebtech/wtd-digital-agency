from django.urls import path
from . import views

urlpatterns = [
path('', views.dashboard, name='dashboard'),

# Post Management
path('posts/', views.posts, name='posts'),
path('posts/bulk-action/', views.bulk_action, name='bulk_action'),
path('posts/add-post/', views.add_post, name='add_post'),
path('posts/edit-post/<int:pk>/', views.edit_post, name='edit_post'),
path('posts/delete-post/<int:pk>/', views.delete_post, name='delete_post'),
path('posts/restore-post/<int:pk>/', views.restore_post, name='restore_post'),
path('post-preview/<int:pk>/', views.preview_post, name='preview_post'),
path('auto-save-post/', views.auto_save_post, name='auto_save_post'),
path('generate-slug/', views.generate_slug_ajax, name='generate_slug'),
path('remove-featured-image/', views.remove_featured_image, name='remove_featured_image'),
# Post Management

# categories, add, edit, view & delete
path('posts/categories/', views.categories, name='categories'),
path('posts/categories/add/', views.add_category, name='add_category'),
path('posts/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
path('posts/categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
path('categories/<slug:slug>/', views.view_category, name='view_category'),
# categories, add, edit, view & delete

# comments
path('comments/', views.comment, name='comments'),
path('comments/bulk-action/', views.bulk_comment_action, name='bulk_comment_action'),
path('comments/approve/<int:comment_id>/', views.comment_approve, name='comment_approve'),
path('comments/unapprove/<int:comment_id>/', views.comment_unapprove, name='comment_unapprove'),
path('comments/delete/<int:comment_id>/', views.comment_delete, name='comment_delete'),
path('comments/edit/<int:comment_id>/', views.comment_edit, name='comment_edit'),
path('comments/reply/<int:comment_id>/', views.comment_reply, name='comment_reply'),
# comments

# Pages Management
path('pages/', views.pages, name='pages'),
path('pages/bulk-action/', views.bulk_action_pages, name='bulk_action_pages'),
path('pages/add-page/', views.add_page, name='add_page'),
path('pages/edit-page/<int:pk>/', views.edit_page, name='edit_page'),
path('pages/delete-page/<int:pk>/', views.delete_page, name='delete_page'),
path('pages/restore-page/<int:pk>/', views.restore_page, name='restore_page'),
path('pages/auto-save/', views.auto_save_page, name='auto_save_page'),
path('pages/generate-slug/', views.generate_slug_ajax_page, name='generate_slug_page'),
path('page-preview/<int:pk>/', views.preview_page, name='preview_page'),
# Pages Management

# Media management URLs
path('media/', views.media_library, name='media_library'),
path('media/add-media/', views.add_media, name='add_media'),
path('media/<int:media_id>/', views.media_detail, name='media_detail'),
path('media/<int:media_id>/update/', views.update_media, name='update_media'),
path('media/<int:media_id>/delete/', views.delete_media, name='delete_media'),
path('media/bulk-delete/', views.bulk_delete_media, name='bulk_delete_media'),
# Media management URLs

# Projects
path('projects/', views.projects, name='projects'),
path('projects/add/', views.add_project, name='add_project'),
path('projects/edit/<int:pk>/', views.edit_project, name='edit_project'),
path('projects/delete/<int:pk>/', views.delete_project, name='delete_project'),

# Testimonials
path('testimonials/', views.testimonials, name='testimonials'),
path('testimonials/add/', views.add_testimonial, name='add_testimonial'),
path('testimonials/edit/<int:pk>/', views.edit_testimonial, name='edit_testimonial'),
path('testimonials/delete/<int:pk>/', views.delete_testimonial, name='delete_testimonial'),
# Testimonials

# Team
path('team/', views.team, name='team'),
path('team/add-member/', views.add_member, name='add_member'),
path('team/edit-member/<int:pk>/', views.edit_member, name='edit_member'),
path('team/delete-member/<int:pk>/', views.delete_member, name='delete_member'),
# Team

# Users
path('users/', views.user_list, name='users'),
path('users/add-user/', views.add_user, name='add_user'),
path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
path('users/profile/', views.profile, name='profile'),
path('users/profile/<int:user_id>/', views.profile, name='edit_user_profile'),
# Users

# Login/Logout
path('login/', views.login, name='login'),
path('logout/', views.logout, name='logout'),
  
]