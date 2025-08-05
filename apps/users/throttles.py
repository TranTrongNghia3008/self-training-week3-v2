from rest_framework.throttling import SimpleRateThrottle
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None

        username = request.data.get("username")
        if username:
            try:
                user = User.objects.get(username=username)
                if getattr(user, "is_locked", False):
                    return None 
            except User.DoesNotExist:
                pass

        ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }
