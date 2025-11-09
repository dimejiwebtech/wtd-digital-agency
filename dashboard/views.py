import os
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.http import JsonResponse, QueryDict
from blog.models import Category, Page, Post, Comment
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify

from dashboard.forms import PageForm, PostForm, ProjectForm
from media_manager.models import MediaFile
from portfolio.models import Project, Testimonial

def build_filtered_url(base_url, **params):
    query_dict = QueryDict(mutable=True)
    for key, value in params.items():
        if value and value != 'all' and value != '':
            query_dict[key] = value
    
    if query_dict:
        return f"{base_url}?{query_dict.urlencode()}"
    return base_url

def dashboard(request):
    posts_count = Post.objects.filter(status='published').count()
    pages_count = Page.objects.filter(status='published').count()
    comments_count = Comment.objects.filter(approved=True).count()
    pending_comments_count = Comment.objects.filter(approved=False).count()
    projects_count = Project.objects.count()
    
    context = {
        'posts_count': posts_count,
        'pages_count': pages_count,
        'comments_count': comments_count,
        'pending_comments_count': pending_comments_count,
        'projects_count': projects_count,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


def posts(request):
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '').strip()
    
    
    posts_queryset = Post.objects.select_related('author').prefetch_related('category').annotate(
    comment_count=Count('comments', filter=Q(comments__approved=True))
)
    # Filter by trash status
    if status_filter == 'trash':
        posts_queryset = posts_queryset.filter(is_trashed=True)
    else:
        posts_queryset = posts_queryset.filter(is_trashed=False)
    
    
    if search_query:
        posts_queryset = posts_queryset.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    if status_filter == 'mine':
        posts_queryset = posts_queryset.filter(author=request.user)
    elif status_filter == 'published':
        posts_queryset = posts_queryset.filter(status='published')
    elif status_filter == 'draft':
        posts_queryset = posts_queryset.filter(status='draft')
    
    # Category filtering
    if category_filter != 'all':
        try:
            posts_queryset = posts_queryset.filter(category_id=int(category_filter))
        except (ValueError, TypeError):
            pass
    
    # Date filtering
    if date_filter != 'all':
        try:
            year, month = date_filter.split('-')
            posts_queryset = posts_queryset.filter(
                published_date__year=int(year),
                published_date__month=int(month)
            )
        except (ValueError, IndexError):
            pass
    
    posts_queryset = posts_queryset.order_by('-created_at')
    
    # Get counts for tabs
    def get_tab_counts(user):
        base_posts = Post.objects.select_related('author')
        return {
            'all': base_posts.filter(is_trashed=False).count(),
            'mine': base_posts.filter(is_trashed=False, author=user).count(),
            'published': base_posts.filter(is_trashed=False, status='published').count(),
            'draft': base_posts.filter(is_trashed=False, status='draft').count(),
            'trash': base_posts.filter(is_trashed=True).count(),
        }

    tab_counts = get_tab_counts(request.user)

    categories = Category.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(posts_queryset, 20)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    
    # Generate date options (last 12 months)
    def get_date_options():
        date_options = []
        current_date = timezone.now()
        for i in range(12):
            if current_date.month - i <= 0:
                month = current_date.month - i + 12
                year = current_date.year - 1
            else:
                month = current_date.month - i
                year = current_date.year
            
            date = current_date.replace(year=year, month=month, day=1)
            date_options.append({
                'value': date.strftime('%Y-%m'),
                'label': date.strftime('%B %Y')
            })
        return date_options
    
    context = {
        'posts': posts_page,
        'categories': categories,
        'tab_counts': tab_counts,
        'current_status': status_filter,
        'current_category': category_filter,
        'date_options': date_filter,
        'search_query': search_query,
        'total_items': paginator.count,
        'current_page': posts_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': posts_page.has_previous(),
        'has_next': posts_page.has_next(),
        'previous_page': posts_page.previous_page_number() if posts_page.has_previous() else None,
        'next_page': posts_page.next_page_number() if posts_page.has_next() else None,
    }
    
    return render(request, 'dashboard/posts/posts.html', context)


def bulk_action(request):
    """Handle bulk actions for posts"""
    if request.method == 'POST':
        action = request.POST.get('action')
        post_ids = request.POST.getlist('post_ids')
        
        # Get current filter parameters to preserve state
        status_filter = request.GET.get('status', 'all')
        category_filter = request.GET.get('category', 'all')
        date_filter = request.GET.get('date', 'all')
        search_query = request.GET.get('search', '').strip()
        page = request.GET.get('page', '1')
        
        if not post_ids:
            messages.error(request, 'No posts selected.')
            redirect_url = reverse('posts') + f'?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}'
            return redirect(redirect_url)
        
        posts_to_update = Post.objects.filter(id__in=post_ids)
        
        if action == 'trash':
            posts_to_update.update(
                is_trashed=True,
                trashed_at=timezone.now(),
                trashed_by=request.user,
                status='trashed'  
            )
            messages.success(request, f'{len(post_ids)} posts moved to trash.')
            
        elif action == 'restore':
            posts_to_update.update(
                is_trashed=False,
                trashed_at=None,
                trashed_by=None,
                status='draft' 
            )
            messages.success(request, f'{len(post_ids)} posts restored as drafts.')
            
        elif action == 'delete':
            posts_to_update.delete()
            messages.success(request, f'{len(post_ids)} posts permanently deleted.')
            
        elif action == 'publish':
            posts_to_update = posts_to_update.exclude(status='published')
            posts_to_update.update(status='published', published_date=timezone.now())
            messages.success(request, f'{len(post_ids)} posts published.')
            
        elif action == 'draft':
            posts_to_update.update(status='draft')
            messages.success(request, f'{len(post_ids)} posts moved to draft.')
        
        # Build redirect URL with preserved parameters
        redirect_url = reverse('posts') + f'?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}'
        return redirect(redirect_url)
    
    return redirect('posts')


def trash_post(request, post_id):
    """Move single post to trash"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
        
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = reverse('posts') + f'?status={status}&category={category}&date={date}&search={search}&page={page}'
    return redirect(redirect_url)
    

def restore_post(request, post_id):
    """Restore single post from trash"""
    post = get_object_or_404(Post, id=post_id, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = build_filtered_url('posts', status=status, category=category, date=date, search=search, page=page)
    return redirect(redirect_url)

def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file 
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post.author = request.user
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            if selected_categories:
                post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post published successfully!')
            else:
                messages.success(request, 'Post saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm()
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/posts/add_post.html', {
        'form': form,
        'all_categories': all_categories,
    })

def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile 
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post = form.save(commit=False)
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title, exclude_id=post.id)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post updated and published!')
            else:
                messages.success(request, 'Post updated and saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/posts/add_post.html', {
        'form': form,
        'post': post,
        'all_categories': all_categories,
    })

def post_form_view(request, pk=None):
    """Unified view for both add and edit post functionality"""
    post = get_object_or_404(Post, pk=pk) if pk else None
    
    # Check permissions for editing
    if post and post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post_obj = form.save(commit=False)
            
            if not post:  # New post
                post_obj.author = request.user
            
            # Handle status and publish date
            if 'save_draft' in request.POST:
                post_obj.status = 'draft'
            elif 'publish' in request.POST:
                post_obj.status = 'published'
                if not post_obj.published_date:
                    post_obj.published_date = timezone.now()
            
            # Auto-generate slug if needed
            if not post_obj.slug and post_obj.title:
                post_obj.slug = generate_unique_slug(post_obj.title, exclude_id=post_obj.id if post else None)
            
            post_obj.save()
            
            # Handle category (multiple selection)
            selected_categories = request.POST.getlist('category')
            post_obj.save()
            if selected_categories:
                post_obj.category.set(selected_categories)
            else:
                post_obj.category.clear()
            
            success_msg = f"Post {'updated' if post else 'created'} and {'published' if post_obj.status == 'published' else 'saved as draft'}!"
            messages.success(request, success_msg)
            
            return redirect('edit_post', pk=post_obj.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    return render(request, 'dashboard/posts/add_post.html', {
        'form': form,
        'post': post,
        'all_categories': Category.objects.all(),
    })

def generate_unique_slug(title, exclude_id=None):
    """Generate a unique slug from title"""
    base_slug = slugify(title) or 'post'
    slug = base_slug
    counter = 1
    
    while True:
        queryset = Post.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return slug
            
        slug = f"{base_slug}-{counter}"
        counter += 1

@csrf_exempt
def auto_save_post(request):
    """Enhanced auto-save with comprehensive field support"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        saveable_fields = ['title', 'content', 'excerpt', 'seo_description', 'seo_keywords', 'slug']
        
        if post_id:
            # Update existing post
            post = get_object_or_404(Post, pk=post_id, author=request.user)
            
            # Update basic fields
            for field in saveable_fields:
                if field in data and data[field] is not None:
                    setattr(post, field, data[field])
            
            # Auto-generate slug if title changed and no custom slug
            if data.get('title') and not data.get('slug'):
                post.slug = generate_unique_slug(data['title'], exclude_id=post.id)
            elif not post.slug:  # Add this line
                post.slug = generate_unique_slug(post.title or 'untitled', exclude_id=post.id)
            
            post.status = 'draft'
            post.save()
            
            # Handle category after saving
            category_ids = data.get('category', [])
            if category_ids:
                try:
                    valid_categories = Category.objects.filter(pk__in=category_ids)
                    post.category.set(valid_categories)
                except (ValueError, TypeError):
                    pass
            else:
                post.category.clear()
            
        else:
            # Create new post
            post_data = {field: data.get(field, '') for field in saveable_fields}
            post_data.update({
                'author': request.user,
                'status': 'draft'
            })
            
            if post_data['title'] and not post_data['slug']:
                post_data['slug'] = generate_unique_slug(post_data['title'])
            elif not post_data['slug']:  
                post_data['slug'] = generate_unique_slug('untitled')  
            
            post = Post.objects.create(**post_data)
            
            # Handle category for new post
            category_id = data.get('category')
            if category_id and category_id != '':
                try:
                    category = Category.objects.get(pk=int(category_id))
                    post.category = category
                    post.save()
                except (Category.DoesNotExist, ValueError, TypeError):
                    pass
        
        return JsonResponse({
            'success': True,
            'post_id': post.pk,
            'slug': post.slug,
            'message': 'Auto-saved'
        })
        
    except Exception as e:
        print(f"Auto-save error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def generate_slug_ajax(request):
    """Generate slug from title via AJAX"""
    title = request.GET.get('title', '')
    post_id = request.GET.get('post_id')
    
    if not title:
        return JsonResponse({'slug': '', 'error': 'No title provided'})
    
    exclude_id = int(post_id) if post_id and post_id.isdigit() else None
    slug = generate_unique_slug(title, exclude_id=exclude_id)
    
    return JsonResponse({'slug': slug})

@csrf_exempt
def remove_featured_image(request):
    """Remove featured image via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        if not post_id:
            return JsonResponse({'success': False, 'error': 'No post ID provided'})
        
        post = get_object_or_404(Post, pk=post_id, author=request.user)
        
        if post.featured_image:
            # Remove file from storage
            if os.path.exists(post.featured_image.path):
                os.remove(post.featured_image.path)
            
            post.featured_image = None
            post.save()
        
        return JsonResponse({'success': True, 'message': 'Featured image removed successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
  
def delete_post(request, pk):
    """Delete single post (move to trash)"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
    
    return redirect('posts')


def restore_post(request, pk):
    """Restore single post from trash"""
    post = get_object_or_404(Post, pk=pk, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    return redirect('posts')
    
def preview_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only preview your own posts.')
        return redirect('dashboard')
    
    
    if post.status == 'published':
        return redirect('posts_by_category_page_or_post', slug=post.slug)
    
    
    if post.status == 'draft':
        context = {
            'single_post': post,  
            'is_preview': True,
            'preview_notice': 'This is a preview of your draft post.',
            'comments': [], 

        }
        return render(request, 'blog/preview_single_blog.html', context)
    
    # Fallback for other statuses
    return redirect('dashboard')


def categories(request):
    search_query = request.GET.get('search', '')
    categories_list = Category.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__status='published'))
    ).order_by('name')
    
    if search_query:
        categories_list = categories_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(categories_list, 20) 
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'dashboard/categories.html', context)


def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not category_name:
            messages.error(request, 'Category name is required', extra_tags='category')
            return redirect('categories')
        
        if not slug:
            slug = slugify(category_name)
        else:
            slug = slugify(slug)
        
        if Category.objects.filter(name__iexact=category_name).exists():
            messages.error(request, 'Category with this name already exists', extra_tags='category')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, 'Category with this slug already exists', extra_tags='category')
            return redirect('categories')
        
        try:
            Category.objects.create(
                name=category_name,
                slug=slug,
                description=description if description else ''
            )
            messages.success(request, f'Category "{category_name}" added successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error adding category: {str(e)}', extra_tags='category')
    
    return redirect('categories')

def edit_category(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not category_name:
            messages.error(request, 'Category name is required', extra_tags='category')
            return redirect('categories')
        
        if not slug:
            slug = slugify(category_name)
        else:
            slug = slugify(slug)
        
        # Check for duplicates 
        if Category.objects.filter(name__iexact=category_name).exclude(id=category_id).exists():
            messages.error(request, 'Category with this name already exists', extra_tags='category')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
            messages.error(request, 'Category with this slug already exists', extra_tags='category')
            return redirect('categories')
        
        try:
            category.name = category_name
            category.slug = slug
            category.description = description if description else ''
            category.save()
            messages.success(request, f'Category "{category_name}" updated successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}', extra_tags='category')
    
    return redirect('categories')

def delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category_name = category.name
        
        # Check if category has posts
        post_count = category.posts.count()
        if post_count > 0:
            messages.error(request, f'Cannot delete category "{category_name}" because it has {post_count} post(s) assigned to it', extra_tags='category')
            return redirect('categories')
        
        try:
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}', extra_tags='category')
    
    return redirect('categories')


def view_category(request, slug):
    """Public view for category posts"""
    category = get_object_or_404(Category, slug=slug)
    
    posts = Post.objects.filter(status='published', category=category).order_by('-published_date')
    paginator = Paginator(posts, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/posts_by_category.html', context)


#comments
def comment(request):
    # Get filter parameters
    status = request.GET.get('status', 'all')
    page = request.GET.get('page', 1)
    
    # Base queryset
    comments = Comment.objects.select_related('post').order_by('-created_on')
    
    # Apply status filters
    if status == 'mine':
        comments = comments.filter(post__author=request.user)
    elif status == 'pending':
        comments = comments.filter(approved=False)
    elif status == 'approved':
        comments = comments.filter(approved=True)
    
    # Count for each status
    all_count = Comment.objects.count()
    mine_count = Comment.objects.filter(post__author=request.user).count()
    pending_count = Comment.objects.filter(approved=False).count()
    approved_count = Comment.objects.filter(approved=True).count()
    
    # Pagination
    paginator = Paginator(comments, 10)
    page_obj = paginator.get_page(page)
    
    context = {
        'comments': page_obj,
        'current_status': status,
        'all_count': all_count,
        'mine_count': mine_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/comments.html', context)

def bulk_comment_action(request):
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        comment_ids = request.POST.getlist('comment_ids')
        
        if comment_ids:
            comments = Comment.objects.filter(id__in=comment_ids)
            
            if action == 'approve':
                comments.update(approved=True)
            elif action == 'unapprove':
                comments.update(approved=False)
            elif action == 'delete':
                comments.delete()
    
    return redirect('comments')


def comment_approve(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = True
    comment.save()
    return redirect('comments')


def comment_unapprove(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = False
    comment.save()
    return redirect('comments')

def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return redirect('comments')


def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        new_body = request.POST.get('comment_body')
        if new_body:
            comment.body = new_body
            comment.save()
    return redirect('comments')

def comment_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            Comment.objects.create(
                post=comment.post,
                parent=comment,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                body=reply_text,
                approved=True
            )
    return redirect('comments')

# Page Management
def pages(request):
    """Pages view - mirrors posts logic"""
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    pages_queryset = Page.objects.all()
    
    # Filter by trash status first
    if status_filter == 'trash':
        pages_queryset = pages_queryset.filter(is_trashed=True)
    else:
        pages_queryset = pages_queryset.filter(is_trashed=False)
    
    # Apply filters
    if search_query:
        pages_queryset = pages_queryset.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    if status_filter == 'published':
        pages_queryset = pages_queryset.filter(status='published')
    elif status_filter == 'draft':
        pages_queryset = pages_queryset.filter(status='draft')
    
    if date_filter != 'all':
        try:
            year, month = date_filter.split('-')
            pages_queryset = pages_queryset.filter(
                published_date__year=int(year),
                published_date__month=int(month)
            )
        except (ValueError, IndexError):
            pass
    
    pages_queryset = pages_queryset.order_by('-created_at')
    
    # Tab counts
    def get_tab_counts():
        base_pages = Page.objects.all()
        return {
            'all': base_pages.filter(is_trashed=False).count(),
            'published': base_pages.filter(is_trashed=False, status='published').count(),
            'draft': base_pages.filter(is_trashed=False, status='draft').count(),
            'trash': base_pages.filter(is_trashed=True).count(),
        }

    tab_counts = get_tab_counts()
    
    # Pagination
    paginator = Paginator(pages_queryset, 20)
    page_number = request.GET.get('page', 1)
    pages_page = paginator.get_page(page_number)
    
    context = {
        'pages': pages_page,
        'tab_counts': tab_counts,
        'current_status': status_filter,
        'current_date': date_filter,
        'search_query': search_query,
        'total_items': paginator.count,
        'current_page': pages_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': pages_page.has_previous(),
        'has_next': pages_page.has_next(),
        'previous_page': pages_page.previous_page_number() if pages_page.has_previous() else None,
        'next_page': pages_page.next_page_number() if pages_page.has_next() else None,
    }
    
    return render(request, 'dashboard/pages/pages.html', context)



def bulk_action_pages(request):
    """Handle bulk actions for pages"""
    if request.method == 'POST':
        action = request.POST.get('action')
        page_ids = request.POST.getlist('page_ids')
        
        status_filter = request.GET.get('status', 'all')
        date_filter = request.GET.get('date', 'all')
        search_query = request.GET.get('search', '').strip()
        page = request.GET.get('page', '1')
        
        if not page_ids:
            messages.error(request, 'No pages selected.')
            return redirect(f'pages?status={status_filter}&date={date_filter}&search={search_query}&page={page}')
        
        pages_to_update = Page.objects.filter(id__in=page_ids)
        
        if action == 'trash':
            pages_to_update.update(
                is_trashed=True,
                trashed_at=timezone.now(),
                trashed_by=request.user,
                status='trashed'
            )
            messages.success(request, f'{len(page_ids)} pages moved to trash.')
            
        elif action == 'restore':
            pages_to_update.update(
                is_trashed=False,
                trashed_at=None,
                trashed_by=None,
                status='draft'
            )
            messages.success(request, f'{len(page_ids)} pages restored as drafts.')
            
        elif action == 'delete':
            pages_to_update.delete()
            messages.success(request, f'{len(page_ids)} pages permanently deleted.')
            
        elif action == 'publish':
            pages_to_update = pages_to_update.exclude(status='published')
            pages_to_update.update(status='published', published_date=timezone.now())
            messages.success(request, f'{len(page_ids)} pages published.')
            
        elif action == 'draft':
            pages_to_update.update(status='draft')
            messages.success(request, f'{len(page_ids)} pages moved to draft.')
        
        redirect_url = reverse('pages') + f'?status={status_filter}&date={date_filter}&search={search_query}&page={page}'
        return redirect(redirect_url)
    
    return redirect('pages')

def trash_page(request, page_id):
    """Move single page to trash"""
    page = get_object_or_404(Page, id=page_id)
    
    if request.method == 'POST':
        page.is_trashed = True
        page.trashed_at = timezone.now()
        page.trashed_by = request.user
        page.status = 'trashed'
        page.save()
        
        messages.success(request, f'Page "{page.title}" moved to trash.')
    
    status = request.GET.get('status', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page_num = request.GET.get('page', '1')
    
    redirect_url = build_filtered_url('pages', status=status, date=date, search=search, page=page_num)
    return redirect(redirect_url)

def restore_page(request, page_id):
    """Restore single page from trash"""
    page = get_object_or_404(Page, id=page_id, is_trashed=True)
    
    if request.method == 'POST':
        page.is_trashed = False
        page.trashed_at = None
        page.trashed_by = None
        page.status = 'draft'
        page.save()
        
        messages.success(request, f'Page "{page.title}" restored as draft.')
    
    status = request.GET.get('status', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page_num = request.GET.get('page', '1')
    
    redirect_url = build_filtered_url('pages', status=status, date=date, search=search, page=page_num)
    return redirect(redirect_url)

def add_page(request):
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            
            # Handle status
            if 'save_draft' in request.POST:
                page.status = 'draft'
            elif 'publish' in request.POST:
                page.status = 'published'
                if not page.published_date:
                    page.published_date = timezone.now()
            
            # Generate slug if not provided
            if not page.slug and page.title:
                page.slug = generate_unique_slug_page(page.title)
            
            page.save()
            
            if page.status == 'published':
                messages.success(request, 'Page published successfully!')
            else:
                messages.success(request, 'Page saved as draft!')
                
            return redirect('edit_page', pk=page.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PageForm()
    
    return render(request, 'dashboard/pages/add_page.html', {'form': form})


def edit_page(request, pk):
    page = get_object_or_404(Page, pk=pk)
    
    if request.method == 'POST':
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            
            # Handle status
            if 'save_draft' in request.POST:
                page.status = 'draft'
            elif 'publish' in request.POST:
                page.status = 'published'
                if not page.published_date:
                    page.published_date = timezone.now()
            
            # Generate slug if not provided
            if not page.slug and page.title:
                page.slug = generate_unique_slug_page(page.title, exclude_id=page.id)
            
            page.save()
            
            if page.status == 'published':
                messages.success(request, 'Page updated and published!')
            else:
                messages.success(request, 'Page updated and saved as draft!')
                
            return redirect('edit_page', pk=page.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PageForm(instance=page)
    
    return render(request, 'dashboard/pages/add_page.html', {'form': form, 'page': page})

def delete_page(request, pk):
    page = get_object_or_404(Page, pk=pk)
    
    if request.method == 'POST':
        page.is_trashed = True
        page.trashed_at = timezone.now()
        page.trashed_by = request.user
        page.status = 'draft'
        page.save()
    
    return redirect('pages')

def restore_page(request, pk):
    page = get_object_or_404(Page, pk=pk, is_trashed=True)
    
    if request.method == 'POST':
        page.is_trashed = False
        page.trashed_at = None
        page.trashed_by = None
        page.status = 'draft'
        page.save()
    
    return redirect('pages')


def generate_unique_slug_page(title, exclude_id=None):
    """Generate a unique slug from title for pages"""
    base_slug = slugify(title) or 'page'
    slug = base_slug
    counter = 1
    
    while True:
        queryset = Page.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return slug
            
        slug = f"{base_slug}-{counter}"
        counter += 1


@csrf_exempt
def auto_save_page(request):
    """Auto-save for pages"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        page_id = data.get('page_id')
        
        saveable_fields = ['title', 'content', 'excerpt', 'seo_description', 'seo_keywords', 'slug']
        
        if page_id:
            page = get_object_or_404(Page, pk=page_id)
            
            for field in saveable_fields:
                if field in data and data[field] is not None:
                    setattr(page, field, data[field])
            
            if data.get('title') and not data.get('slug'):
                page.slug = generate_unique_slug_page(data['title'], exclude_id=page.id)
            elif not page.slug:
                page.slug = generate_unique_slug_page(page.title or 'untitled', exclude_id=page.id)
            
            page.status = 'draft'
            page.save()
        else:
            page_data = {field: data.get(field, '') for field in saveable_fields}
            page_data['status'] = 'draft'
            
            if page_data['title'] and not page_data['slug']:
                page_data['slug'] = generate_unique_slug_page(page_data['title'])
            elif not page_data['slug']:
                page_data['slug'] = generate_unique_slug_page('untitled')
            
            page = Page.objects.create(**page_data)
        
        return JsonResponse({
            'success': True,
            'page_id': page.pk,
            'slug': page.slug,
            'message': 'Auto-saved'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def generate_slug_ajax_page(request):
    """Generate slug from title via AJAX for pages"""
    title = request.GET.get('title', '')
    page_id = request.GET.get('page_id')
    
    if not title:
        return JsonResponse({'slug': '', 'error': 'No title provided'})
    
    exclude_id = int(page_id) if page_id and page_id.isdigit() else None
    slug = generate_unique_slug_page(title, exclude_id=exclude_id)
    
    return JsonResponse({'slug': slug})


def preview_page(request, pk):
    """Preview page functionality"""
    page = get_object_or_404(Page, pk=pk)
    
    if page.status == 'published':
        return redirect('posts_by_category_page_or_post', slug=page.slug)
    
    if page.status == 'draft':
        context = {
            'single_page': page,
            'is_preview': True,
            'preview_notice': 'This is a preview of your draft page.',
        }
        return render(request, 'blog/preview_page.html', context)
    
    return redirect('pages')


# Media Library
def media_library(request):
    """Main media library view with filtering and pagination"""
    
    # Get filter parameters
    media_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', 'all')
    
    # Base queryset
    media_files = MediaFile.objects.all()
    
    # Apply filters
    if media_type != 'all':
        media_files = media_files.filter(category=media_type)
    
    if search_query:
        media_files = media_files.filter(
            Q(file__icontains=search_query) |
            Q(alt_text__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Date filtering (simplified)
    if date_filter != 'all':
        pass
    
    
    paginator = Paginator(media_files, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Check if this is NOT a request from the post editor
        if 'post-editor' in request.GET:
            # Return JSON for post editor modal
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
        elif request.GET.get('page'):  # load more 
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
    
    # Get media type counts for filter buttons
    media_counts = {
        'all': MediaFile.objects.count(),
        'image': MediaFile.objects.filter(category='image').count(),
        'document': MediaFile.objects.filter(category='document').count(),
        'video': MediaFile.objects.filter(category='video').count(),
        'audio': MediaFile.objects.filter(category='audio').count(),
        'other': MediaFile.objects.filter(category='other').count(),
    }
    
    context = {
        'media_files': page_obj,
        'media_type': media_type,
        'search_query': search_query,
        'date_filter': date_filter,
        'media_counts': media_counts,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return render(request, 'dashboard/media_library/media.html', context)


def add_media(request):
    """Add new media files page"""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        uploaded_files = []
        
        for file in files:
            # Create MediaFile instance
            media_file = MediaFile(file=file)
            
            # Set alt_text to filename without extension
            media_file.alt_text = os.path.splitext(file.name)[0]
            
            media_file.save()
            uploaded_files.append(media_file)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX response - check if request came from media library
            referer = request.META.get('HTTP_REFERER', '')
            
            files_data = []
            for media in uploaded_files:
                files_data.append({
                    'id': media.id,
                    'name': os.path.basename(media.file.name),
                    'url': media.file.url,
                    'type': media.file_type,
                    'size': media.file_size,
                })
            
            response_data = {
                'success': True,
                'files': files_data,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)'
            }
            
            # If not from media library page, redirect to media library
            if 'media/' not in referer or 'add-media' in referer:
                response_data['redirect'] = '/dashboard/media/' 
            
            return JsonResponse(response_data)
        else:
            messages.success(request, f'Successfully uploaded {len(uploaded_files)} file(s)')
            return redirect('/dashboard/media/')  
    
    return render(request, 'dashboard/media_library/add_media.html')


def media_detail(request, media_id):
    """Get media file details for modal"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': media_file.id,
            'url': media_file.file.url,
            'name': os.path.basename(media_file.file.name),
            'type': media_file.file_type,
            'size': media_file.file_size,
            'alt_text': media_file.alt_text,
            'description': media_file.description,
            'created_at': media_file.created_at.strftime('%B %d, %Y'),
            'file_extension': media_file.file_extension,
            'thumbnail_url': media_file.get_thumbnail_url(),
            'dimensions': getattr(media_file, 'dimensions', None),  
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def update_media(request, media_id):
    """Update media file details"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        
        # Update fields
        media_file.alt_text = data.get('alt_text', media_file.alt_text)
        media_file.description = data.get('description', media_file.description)
        media_file.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media updated successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def delete_media(request, media_id):
    """Delete media file"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        media_file.delete() 
        
        return JsonResponse({
            'success': True,
            'message': 'Media deleted successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def bulk_delete_media(request):
    """Bulk delete media files"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        media_ids = data.get('media_ids', [])
        
        if media_ids:
            deleted_count = 0
            for media_id in media_ids:
                try:
                    media_file = MediaFile.objects.get(id=media_id)
                    media_file.delete()
                    deleted_count += 1
                except MediaFile.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {deleted_count} file(s)'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Projects
def projects(request):
    project_list = Project.objects.all().order_by('-created_at')
    
    context = {
        'projects': project_list,
        'total_projects': project_list.count(),
    }
    return render(request, 'dashboard/projects.html', context)


def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project added successfully!')
            return redirect('projects')
        else:
            messages.error(request, 'Error adding project. Please check the form.')
    return redirect('projects')


def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('projects')
        else:
            messages.error(request, 'Error updating project. Please check the form.')
    return redirect('projects')


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
    return redirect('projects')

# Testimonials
def testimonials(request):
    testimonials_list = Testimonial.objects.all().order_by('-created_at')
    context = {
        'testimonials': testimonials_list
    }
    return render(request, 'dashboard/testimonials.html', context)

def add_testimonial(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        position = request.POST.get('position')
        company = request.POST.get('company')
        message = request.POST.get('message')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        Testimonial.objects.create(
            name=name,
            position=position,
            company=company,
            message=message,
            image=image,
            is_active=is_active
        )
        messages.success(request, 'Testimonial added successfully!', extra_tags='testimonial')
        return redirect('testimonials')
    
    return redirect('testimonials')

def edit_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        testimonial.name = request.POST.get('name')
        testimonial.position = request.POST.get('position')
        testimonial.company = request.POST.get('company')
        testimonial.message = request.POST.get('message')
        testimonial.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            testimonial.image = request.FILES.get('image')
        
        testimonial.save()
        messages.success(request, 'Testimonial updated successfully!', extra_tags='testimonial')
        return redirect('testimonials')
    
    return redirect('testimonials')

def delete_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        testimonial.delete()
        messages.success(request, 'Testimonial deleted successfully!', extra_tags='testimonial')
    
    return redirect('testimonials')