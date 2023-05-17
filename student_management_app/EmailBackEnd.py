from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.mail import send_mail


class EmailBackEnd(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None


def send_mail_to_student(email, username, password, first_name, last_name, enrolment_num):
    message = f"""
    Dear student {first_name.capitalize()} {last_name.capitalize()}.
    
    Welcome to Virtual Study Center. Here you can view all the your progress, attendance and even access study 
    materials plus lectures for your respected course. 
    
    Your registered enrolment number is : {enrolment_num}
    
    Login Credentials:
    Username: {email}
    Password: {password}
    
    Contact your respective department faculty for any changes.
    """

    send_mail(
        "You have been successfully registered to Virtual Study Center!!!",
        message,
        settings.BASE_EMAIL_ID,
        [email],
        fail_silently=False,
    )
