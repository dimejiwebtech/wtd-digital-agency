from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Case, When, Value, IntegerField
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.messages import get_messages
from WTD import settings
from blog.forms import CommentForm
from .models import Page, Post, Category, Comment
from django.contrib.auth.models import User



def blog(request):
    featured_posts = Post.objects.published().filter(is_featured=True).order_by('-published_date')[:3]
    featured_ids = list(featured_posts.values_list('id', flat=True))
    
    posts = Post.objects.published().exclude(id__in=featured_ids).order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts, 4)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'blog/blog.html', {
        'featured_posts': featured_posts,
        'page_obj': page_obj,
    })

def posts_by_category_page_or_post(request, slug):
    # Check if it's a category
    category = Category.objects.filter(slug=slug).first()
    if category:
        posts = Post.objects.filter(status='published', category=category).order_by('-published_date')
        paginator = Paginator(posts, 6)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'category': category,
            'categories': Category.objects.all(),
        }
        return render(request, 'blog/posts_by_category.html', context)
    
    # Check if it's a page
    page = Page.objects.filter(slug=slug, status='published').first()
    if page:
        context = {'single_page': page}
        return render(request, 'blog/single_page.html', context)

    # If not category or page, treat as single post
    single_post = get_object_or_404(Post, slug=slug, status='published')
    
    # Related posts by category
    post_categories = single_post.category.all()
    related_posts = Post.objects.filter(
        category__in=post_categories,
        status='published'
    )[:4]
    
    sidebar_related_posts = Post.objects.filter(
        category__in=post_categories,
        status='published'
    )[:5]

    # Comment handling
    comment_form = CommentForm()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        parent_id = request.POST.get('parent_id')
        
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = single_post
            if parent_id:
                comment.parent = Comment.objects.get(id=parent_id)
            comment.save()
            
            send_mail(
                subject=f'New comment on "{single_post.title}"',
                message=f'A new comment by {comment.name} is awaiting approval.\n\nComment: {comment.body}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
            
            messages.success(request, 'Your comment is awaiting approval.')
            return redirect('posts_by_category_or_post', slug=slug)

    # Comments
    show_all = request.GET.get('show_all_comments')
    if show_all:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies')
    else:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies')[:10]

    total_comments = single_post.comments.filter(approved=True, parent=None).count()
    
    view_messages = []
    if request.method == 'POST':
        view_messages = [msg for msg in get_messages(request) if 'comment' in str(msg).lower()]

    context = {
        'single_post': single_post,
        'related_posts': related_posts,
        'sidebar_related_posts': sidebar_related_posts,
        'comment_form': comment_form,
        'comments': comments,
        'total_comments': total_comments,
        'show_all': show_all,
        'view_messages': view_messages,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/single_blog.html', context)


def search(request):
    keyword = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if keyword:
        posts = Post.objects.filter(
            Q(title__icontains=keyword) | 
            Q(content__icontains=keyword) | 
            Q(excerpt__icontains=keyword),
            status='published'
        ).annotate(
            relevance=Case(
                When(title__iexact=keyword, then=Value(3)),
                When(title__icontains=keyword, then=Value(2)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('-relevance', '-published_date')
    else:
        posts = Post.objects.none()
    
    paginator = Paginator(posts, 9)
    page_obj = paginator.get_page(page_number)
    
    # AJAX for live search or load more
    if is_ajax:
        is_live = request.GET.get('live') == '1'
        template = 'blog/partials/live_search.html' if is_live else 'blog/partials/search_cards.html'
        html = render_to_string(template, {'page_obj': page_obj, 'keyword': keyword})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'total': paginator.count
        })
    
    context = {
        'page_obj': page_obj,
        'keyword': keyword,
        'total_results': paginator.count,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/search.html', context)

def author_page(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author, status='published').order_by('-published_date')
    
    # Get author's most popular posts (you can customize this logic)
    featured_posts = posts[:3]
    

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author': author,
        'page_obj': page_obj,
        'total_posts': posts.count(),
        'featured_posts': featured_posts,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/author_page.html', context)