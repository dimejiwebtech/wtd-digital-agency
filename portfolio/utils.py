from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_contact_email(contact_data):
    """
    Sends contact form data to admin and confirmation to user
    """
    # Send email to admin
    admin_subject = f"New Contact Form Submission from {contact_data['name']}"
    admin_message = render_to_string('portfolio/emails/admin_notification.html', {
        'name': contact_data['name'],
        'email': contact_data['email'],
        'project_type': contact_data['project_type'],
        'message': contact_data['message']
    })

    send_mail(
        admin_subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        html_message=admin_message,
        fail_silently=False
    )

    # Send confirmation email to user
    user_subject = "Thank you for contacting us!"
    user_message = render_to_string('portfolio/emails/user_confirmation.html', {
        'name': contact_data['name']
    })

    send_mail(
        user_subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [contact_data['email']],
        html_message=user_message,
        fail_silently=False
    )