from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.notifications.tasks import send_notification_email
from .serializers import RegisterSerializer

User = get_user_model()
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