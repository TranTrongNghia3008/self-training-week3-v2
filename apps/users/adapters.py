from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        print(sociallogin.account.extra_data)
        # If user already exists → allow auto login (do not create new)
        email = user_email(sociallogin.user)
        if User.objects.filter(email=email).exists():
            return True

        # If not exists, allow to create new user
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        extra = sociallogin.account.extra_data

        if user.username:
            return user

        base_username = extra.get("login")

        if not base_username:
            base_username = extra.get("name")

        base_username = slugify(base_username) if base_username else "user"

        username = base_username
        index = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}-{index}"
            index += 1

        user.username = username

        if not user.email:
            user.email = extra.get("email", "")

        return user