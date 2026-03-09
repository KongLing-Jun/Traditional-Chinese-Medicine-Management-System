from rest_framework import permissions, serializers, viewsets

from accounts.api_permissions import RBACPermission
from accounts.services import log_operation

from .models import Herb


class HerbSerializer(serializers.ModelSerializer):
    class Meta:
        model = Herb
        fields = [
            "id",
            "herb_code",
            "herb_name",
            "alias_name",
            "category",
            "nature_taste",
            "meridian_tropism",
            "efficacy",
            "indication",
            "origin_place",
            "storage_method",
            "unit",
            "reference_price",
            "description",
            "extra_attributes",
            "status",
            "created_at",
            "updated_at",
        ]


class HerbViewSet(viewsets.ModelViewSet):
    queryset = Herb.objects.all()
    serializer_class = HerbSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    search_fields = ["herb_code", "herb_name", "alias_name", "efficacy", "indication"]
    filterset_fields = ["category", "status"]
    ordering_fields = ["herb_code", "herb_name", "reference_price", "created_at", "updated_at"]
    permission_code_map = {
        "list": "herb.view",
        "retrieve": "herb.view",
        "create": "herb.create",
        "update": "herb.update",
        "partial_update": "herb.update",
        "destroy": "herb.delete",
    }

    def perform_create(self, serializer):
        herb = serializer.save()
        log_operation(
            user=self.request.user,
            module_name="herb",
            operation_type="create",
            request=self.request,
            request_param=f"herb_id={herb.id}",
        )

    def perform_update(self, serializer):
        herb = serializer.save()
        log_operation(
            user=self.request.user,
            module_name="herb",
            operation_type="update",
            request=self.request,
            request_param=f"herb_id={herb.id}",
        )

    def perform_destroy(self, instance):
        herb_id = instance.id
        instance.delete()
        log_operation(
            user=self.request.user,
            module_name="herb",
            operation_type="delete",
            request=self.request,
            request_param=f"herb_id={herb_id}",
        )
