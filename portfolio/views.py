from django.http import Http404
from django.shortcuts import redirect, render
from .models import Project, Testimonial, Team
from django.utils import timezone
from django.contrib import messages
from .utils import send_contact_email

def homepage(request):
    projects = Project.objects.filter(
        is_featured=True,
        completion_date__lte=timezone.now()
    ).order_by('-completion_date')[:3]
    testimonials = Testimonial.objects.filter(is_active=True)

    context = {
        'projects': projects,
        'testimonials': testimonials,
    }
    
    return render(request, 'portfolio/homepage.html', context)


def about(request):
    team_members = Team.objects.filter(is_active=True).order_by('order')
    context = {
        'team_members': team_members,
    }
    return render(request, 'portfolio/about.html', context)



def contact(request):
    if request.method == 'POST':
        try:
            budget_value = request.POST.get('budget')
            budget_ranges = {
                'small': '$5,000 - $10,000',
                'medium': '$10,000 - $25,000',
                'large': '$25,000 - $50,000',
                'enterprise': '$50,000+'
            }

            contact_data = {
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'project_type': request.POST.get('project_type'),
                'budget': budget_ranges.get(budget_value, 'Not specified'),
                'message': request.POST.get('message')
            }
            
            # Validate data
            if not all(contact_data.values()):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('contact')

            # Send emails
            send_contact_email(contact_data)
            
            messages.success(request, 'Thank you! Your message has been sent successfully. We\'ll get back to you soon.')
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            return redirect('contact')
    
    return render(request, 'portfolio/contact.html')

def services(request):
    return render(request, 'portfolio/services.html')


def service_detail(request, service_slug):
    templates = {
        'web-development': 'portfolio/services/web_development.html',
        'web-design': 'portfolio/services/web_design.html',
        'app-development': 'portfolio/services/app_development.html',
        'seo': 'portfolio/services/seo.html',
        'ui-ux-design': 'portfolio/services/ui_ux_design.html',
        'blockchain-development': 'portfolio/services/blockchain_development.html',
        'business-registration': 'portfolio/services/business_registration.html',
        'content-writing': 'portfolio/services/content_writing.html',
    }
    
    template = templates.get(service_slug)
    
    if not template:
        raise Http404("Service not found")
    
    return render(request, template)

def projects(request):
    featured_project = Project.objects.filter(top_rated=True).first()
    projects = Project.objects.all()
    testimonials = Testimonial.objects.filter(is_active=True)
    
    # Get unique categories for filter
    categories = Project.objects.values_list('category', flat=True).distinct()
    
    context = {
        'featured_project': featured_project,
        'projects': projects,
        'testimonials': testimonials,
        'categories': categories
    }
    
    return render(request, 'portfolio/projects.html', context)