from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

from apps.notifications.tasks import send_notification_email
from .serializers import RegisterSerializer
from .throttles import LoginRateThrottle

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise AuthenticationFailed(_("Username and password are required"))

        try:
            user_obj = User.objects.get(username=username)
            # Account has been locked
            if getattr(user_obj, "is_locked", False):
                return Response({"detail": "This account is locked."}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            user_obj = None  # User does not exist (will not increment failed_attempts)

        user = authenticate(username=username, password=password)

        if user is None:
            # If username exists then increase the number of wrong attempts
            if user_obj:
                user_obj.failed_login_attempts += 1
                if user_obj.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user_obj.is_locked = True
                    
                    send_notification_email.delay(
                        subject="Your account has been locked",
                        message="You have entered the wrong password too many times. Please contact admin.",
                        recipient_email=user_obj.email
                    )
                user_obj.save()
            raise AuthenticationFailed(_("No active account found with the given credentials"))

        # If login is correct but locked
        if getattr(user, "is_locked", False):
            return Response({"detail": "This account is locked."}, status=status.HTTP_403_FORBIDDEN)

        # Reset count wrong if correct
        user.failed_login_attempts = 0
        user.save()

        return super().post(request, *args, **kwargs)
    
class UnlockUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Unlock user account by username (admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username"],
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={
            200: openapi.Response(description="User unlocked"),
            404: "User not found",
            403: "Not authorized",
        }
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
            user.is_locked = False
            user.failed_login_attempts = 0
            user.save()
            return Response({"detail": f"User '{username}' has been unlocked."})
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ForgotPasswordView(APIView):
    @swagger_auto_schema(
        operation_description="Send reset password email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL)
            },
        ),
        responses={200: "If the email exists, reset link will be sent."}
    )
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f"https://your-frontend.com/reset-password/:{uid}/:{token}"

            send_notification_email.delay(
                subject="Reset your password",
                message=f"Click the link to reset your password: {reset_link}",
                recipient_email=user.email
            )
        # Always return success to prevent email enumeration
        return Response({"message": "If the email is registered, a reset link will be sent."}, status=status.HTTP_200_OK)
    
class ResetPasswordView(APIView):
    @swagger_auto_schema(
        operation_description="Reset password with token",
        manual_parameters=[
            openapi.Parameter("uidb64", openapi.IN_PATH, type=openapi.TYPE_STRING),
            openapi.Parameter("token", openapi.IN_PATH, type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["password"],
            properties={
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password")
            }
        ),
        responses={200: "Password reset successful"}
    )
    def post(self, request, uidb64, token):
        password = request.data.get("password")
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError("Invalid user")

        if not default_token_generator.check_token(user, token):
            raise ValidationError("Invalid or expired token")

        user.set_password(password)
        user.save()
        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user = self.user
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        })
    
class GithubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user = self.user
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        })