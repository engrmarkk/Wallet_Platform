from flask_mail import Message
from flask import render_template
from extensions import mail
from celery import shared_task


@shared_task
def send_email_users(subject, email, template_name, html_context: dict, send_body = None):
    try:
        print(f"Got notification for subject: {subject}: template_name: {template_name}")
        msg = Message(
            subject=subject,
            sender="Easytransact <easytransact.send@gmail.com>",
            recipients=[email] if isinstance(email, str) else email,
        )
        if send_body:
            msg.body = send_body
        else:
            msg.html = render_template(
                template_name, **html_context
            )
        mail.send(msg)
        return "Sent successfully"
    except Exception as e:
        print(f"Error from sending mail: {e}")
        return None
