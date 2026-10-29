from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either the username or the email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if not username or password is None:
            return None

        users = UserModel.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).order_by("id")
        for user in users:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
