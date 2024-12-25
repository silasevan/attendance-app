from flask_mail import Message
from flask import render_template, current_app
from threading import Thread
from app import mail
import jwt
from datetime import datetime, timedelta

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    try:
        token = user.get_reset_password_token()
        send_email('[ATTENDACE-APP] Reset Your Password',
            sender=current_app.config['ADMINS'][0],
            recipients=[user.email],
            text_body=render_template('email/reset_password.txt', user=user, token=token),
            html_body=render_template('email/reset_password.html', user=user, token=token))
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")
