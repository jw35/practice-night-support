from django_use_email_as_username.models import BaseUser, BaseUserManager

class User(BaseUser):
    objects = BaseUserManager()

    def __str__(self):
        return self.get_full_name()

