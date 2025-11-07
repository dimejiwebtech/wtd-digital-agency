from .models import Category
from django.db.models import Count, Q

def get_categories(request):
    categories = list(
        Category.objects.annotate(
            posts_count=Count('posts', filter=Q(posts__status='published'))
        ).order_by('order') 
    )

    return {
        'categories': categories
    }
