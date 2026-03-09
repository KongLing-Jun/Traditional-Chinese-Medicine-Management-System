from rest_framework import permissions, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_permissions import RBACPermission
from .models import OperationLog, PermissionEntry, Role, User
from .navigation import build_visible_menu
from .services import log_operation


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "role_name", "role_code", "description", "status"]


class PermissionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionEntry
        fields = ["id", "permission_name", "permission_code", "permission_type", "path", "description"]


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.role_name", read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "real_name",
            "email",
            "phone",
            "gender",
            "role",
            "role_name",
            "is_active",
            "is_staff",
            "last_login",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class OperationLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            "id",
            "user",
            "user_name",
            "module_name",
            "operation_type",
            "request_method",
            "request_url",
            "request_param",
            "operation_result",
            "ip_address",
            "created_at",
        ]


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    permission_code_map = {"GET": "role.view"}


class PermissionEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PermissionEntry.objects.all()
    serializer_class = PermissionEntrySerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    permission_code_map = {"GET": "permission.view"}


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("role").all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    search_fields = ["username", "real_name", "email", "phone"]
    filterset_fields = ["role", "is_active", "is_staff"]
    permission_code_map = {
        "list": "user.view",
        "retrieve": "user.view",
        "create": "user.create",
        "update": "user.update",
        "partial_update": "user.update",
        "destroy": "user.delete",
    }

    def perform_create(self, serializer):
        user = serializer.save()
        log_operation(
            user=self.request.user,
            module_name="user",
            operation_type="create",
            request=self.request,
            request_param=f"user_id={user.id}",
        )

    def perform_update(self, serializer):
        user = serializer.save()
        log_operation(
            user=self.request.user,
            module_name="user",
            operation_type="update",
            request=self.request,
            request_param=f"user_id={user.id}",
        )

    def perform_destroy(self, instance):
        user_id = instance.id
        instance.delete()
        log_operation(
            user=self.request.user,
            module_name="user",
            operation_type="delete",
            request=self.request,
            request_param=f"user_id={user_id}",
        )


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OperationLog.objects.select_related("user").all()
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    filterset_fields = ["module_name", "operation_type", "operation_result", "user"]
    search_fields = ["module_name", "operation_type", "request_url", "request_param", "ip_address"]
    ordering_fields = ["created_at"]
    permission_code_map = {"GET": "log.view"}


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AccessAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "permissions": sorted(request.user.get_permission_codes()),
                "menu": build_visible_menu(request.user),
            }
        )
