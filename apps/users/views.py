from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer

User = get_user_model()

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class custom_token_obtain_pair(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(["POST"])
def logout_user(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
