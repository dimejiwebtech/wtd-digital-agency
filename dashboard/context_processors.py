from blog.models import Comment


def comment_notifications(request):
    """Add pending comments count to all templates"""
    return {
        'pending_comments_count': Comment.objects.filter(approved=False).count()
    }

def user_role_context(request):
    """Add user role information to template context"""
    context = {
        'is_administrator': False,
        'is_author': False,
        'user_groups_debug': [],  # For debugging
    }
    
    if request.user.is_authenticated:
        user_groups = list(request.user.groups.values_list('name', flat=True))
        context['user_groups_debug'] = user_groups  # Debug info
        
        # Check for Administrator (case-insensitive)
        context['is_administrator'] = any(
            group.lower() == 'administrator' for group in user_groups
        )
        
        # Check for Author (case-insensitive) 
        context['is_author'] = any(
            group.lower() == 'author' for group in user_groups
        )
        
        # Fallback: if user is superuser, treat as administrator
        if request.user.is_superuser:
            context['is_administrator'] = True
    
    return context