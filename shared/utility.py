import re
import threading
import phonenumbers
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError
# from decouple import config
# from twilio.rest import Client


email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
username_regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{3,28}[a-zA-Z0-9]$")


def check_email_or_phone(email_or_phone):
    if re.fullmatch(email_regex, email_or_phone):
        email_or_phone = 'email'
    else:
        try:
            phone_number = phonenumbers.parse(email_or_phone, None)
            if phonenumbers.is_valid_number(phone_number):
                email_or_phone = 'phone'
        except phonenumbers.phonenumberutil.NumberParseException:
            error = {
                'success': False,
                'message': "Invalid email or phone number",
            }
            raise ValidationError(error)
    return email_or_phone


def check_user_type(user_input):
    if re.fullmatch(username_regex, user_input):
        user_input = 'username'
    elif re.fullmatch(email_regex, user_input):
        user_input = 'email'
    else:
        try:
            phone_number = phonenumbers.parse(user_input, None)
            if phonenumbers.is_valid_number(phone_number):
                user_input = 'phone'
        except phonenumbers.phonenumberutil.NumberParseException:
            error = {
                'success': False,
                'message': "You must enter a username, email or phone number",
            }
            raise ValidationError(error)
    return user_input



class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Email:

    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']],
        )
        if data.get('content_type') == 'html':
            email.content_subtype = 'html'
        EmailThread(email).start()


def send_email(email, code):
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {'code': code},
    )
    Email.send_email(
        {
            'subject': "Registration",
            'to_email': email,
            'body': html_content,
            'content_type': "html",
        }
    )

# def send_phone_number(phone_number, code):
#     account_sid = config('account_sid')
#     auth_token = config('auth_token')
#     client = Client(account_sid, auth_token)
#     client.messages.create(
#         body=f"Sizning tasdiqlash kodingiz {code}.",
#         from_='+998941234567',
#         to=f'{phone_number}',
#
#     )
