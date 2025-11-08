from django import forms
from blog.models import Page, Post
from django.utils.text import slugify
from django.utils import timezone
from tinymce.widgets import TinyMCE

class BaseContentForm(forms.ModelForm):
    """Base form for Post and Page with shared fields and logic"""
    
    TITLE_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 text-xl border-0 border-b border-gray-300 focus:border-primary focus:outline-none bg-transparent placeholder-gray-500',
        'placeholder': 'Add title',
        'id': 'id_title'
    })
    
    SLUG_WIDGET = forms.TextInput(attrs={
        'class': 'text-sm px-2 py-1 border-0 border-b border-dashed border-gray-300 focus:border-primary focus:outline-none bg-transparent',
        'id': 'id_slug'
    })
    
    TEXTAREA_WIDGET = forms.Textarea(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
        'rows': 3,
    })
    
    INPUT_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
    })
    
    DATETIME_WIDGET = forms.DateTimeInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm',
        'type': 'datetime-local',
        'id': 'id_published_date'
    })
    
    IMAGE_WIDGET = forms.FileInput(attrs={
        'accept': 'image/*',
        'id': 'id_featured_image',
        'style': 'display: none;'
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make common fields optional
        self.fields['slug'].required = False
        self.fields['published_date'].required = False
        
        if 'featured_image' in self.fields:
            self.fields['featured_image'].required = False
            self.fields['featured_image_id'] = forms.CharField(required=False, widget=forms.HiddenInput())
        
        # Set initial datetime value for new content
        if not self.instance.pk and 'published_date' not in self.initial:
            self.initial['published_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_slug(self):
        """Generic slug validation - override model in subclass"""
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        if not slug and title:
            slug = slugify(title)
        
        if slug:
            # Get the model from Meta
            model = self.Meta.model
            queryset = model.objects.filter(slug=slug)
            
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                counter = 1
                original_slug = slug
                while model.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance.pk else 0).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
        
        return slug

    def clean_seo_description(self):
        """Validate SEO description length"""
        seo_description = self.cleaned_data.get('seo_description', '')
        if len(seo_description) > 160:
            raise forms.ValidationError('Meta description should not exceed 160 characters.')
        return seo_description

    def get_tinymce_widget(self):
        """Return TinyMCE widget with configuration"""
        return TinyMCE(attrs={
            'class': 'django-tinymce',
            'id': 'id_content'
        })


class PostForm(BaseContentForm):
    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'content', 'excerpt', 
            'featured_image', 'category', 'seo_description', 
            'seo_keywords', 'published_date'
        ]
        widgets = {
            'title': BaseContentForm.TITLE_WIDGET,
            'slug': BaseContentForm.SLUG_WIDGET,
            'excerpt': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'Write an excerpt (optional)',
                'id': 'id_excerpt'
            }),
            'seo_description': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'SEO meta description',
                'maxlength': '160',
                'id': 'id_seo_description'
            }),
            'seo_keywords': forms.TextInput(attrs={
                **BaseContentForm.INPUT_WIDGET.attrs,
                'placeholder': 'SEO keywords (comma separated)',
                'id': 'id_seo_keywords'
            }),
            'published_date': BaseContentForm.DATETIME_WIDGET,
            'featured_image': BaseContentForm.IMAGE_WIDGET,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override content widget with TinyMCE
        self.fields['content'].widget = self.get_tinymce_widget()


class PageForm(BaseContentForm):
    class Meta:
        model = Page
        fields = [
            'title', 'slug', 'content', 'excerpt', 'seo_description', 
            'seo_keywords', 'published_date'
        ]
        widgets = {
            'title': BaseContentForm.TITLE_WIDGET,
            'slug': BaseContentForm.SLUG_WIDGET,
            'excerpt': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'Write an excerpt (optional)',
                'id': 'id_excerpt'
            }),
            'seo_description': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'SEO meta description',
                'maxlength': '160',
                'id': 'id_seo_description'
            }),
            'seo_keywords': forms.TextInput(attrs={
                **BaseContentForm.INPUT_WIDGET.attrs,
                'placeholder': 'SEO keywords (comma separated)',
                'id': 'id_seo_keywords'
            }),
            'published_date': BaseContentForm.DATETIME_WIDGET,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override content widget with TinyMCE
        self.fields['content'].widget = self.get_tinymce_widget()