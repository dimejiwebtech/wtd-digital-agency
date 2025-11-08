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
  
]