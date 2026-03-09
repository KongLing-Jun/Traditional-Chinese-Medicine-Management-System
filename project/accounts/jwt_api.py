from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import OperationLog
from .services import log_operation
from .models import User


class JWTUserSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.role_code", read_only=True)
    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "real_name",
            "email",
            "phone",
            "is_active",
            "role_code",
            "role_name",
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role.role_code if user.role else ""
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = JWTUserSerializer(self.user).data
        return data


@method_decorator(csrf_exempt, name="dispatch")
class JWTLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        username = request.data.get("username", "")
        user = get_user_model().objects.filter(username=username).first() if username else None
        result = (
            OperationLog.RESULT_SUCCESS
            if response.status_code == status.HTTP_200_OK
            else OperationLog.RESULT_FAILED
        )
        log_operation(
            user=user,
            module_name="auth",
            operation_type="login",
            request=request,
            result=result,
            request_param=f"username={username}",
        )
        return response


@method_decorator(csrf_exempt, name="dispatch")
class JWTRefreshAPIView(TokenRefreshView):
    permission_classes = [AllowAny]


@method_decorator(csrf_exempt, name="dispatch")
class JWTLogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_operation(
            user=request.user,
            module_name="auth",
            operation_type="logout",
            request=request,
            result=OperationLog.RESULT_SUCCESS,
        )
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
