from flask_mail import Message
from flask import url_for
from . import mail

def send_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message('Password Reset Request',
                  sender='silas@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('main.reset_password', token=token, _external=True)}
If you did not make this request, simply ignore this email.
'''
    mail.send(msg)
