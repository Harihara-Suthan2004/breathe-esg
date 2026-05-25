from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
import json

from .models import NormalizedEmissionRecord, AuditLog, Organization
from .serializers import NormalizedEmissionRecordSerializer

class EmissionRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Normalized Emission Records to be viewed, updated, and locked.
    Includes built-in multi-tenancy filtering and automated audit logging.
    """
    queryset = NormalizedEmissionRecord.objects.all().order_by('-created_at')
    serializer_class = NormalizedEmissionRecordSerializer

    def get_queryset(self):
        """
        Multi-Tenancy Guard:
        Allows filtering by a URL parameter `org_id` to separate distinct corporate clients.
        """
        queryset = self.queryset
        org_id = self.request.query_params.get('org_id')
        if org_id is not None:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def update(self, request, *args, **kwargs):
        """
        Overrides default update to catch modifications and write them to the AuditLog.
        Implements an absolute freeze barrier if `is_locked` is active.
        """
        record = self.get_object()
        
        # 1. Enforce strict audit lock rule
        if record.is_locked:
            return Response(
                {"error": "This record is officially locked for auditing and cannot be modified."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # 2. Capture baseline state before changes happen
        old_snapshot = {
            "status": record.status,
            "analyst_notes": record.analyst_notes,
            "is_locked": record.is_locked
        }
        
        # 3. Perform standard serialization update
        serializer = self.get_serializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_record = serializer.save()
        
        # 4. Capture the newly updated state
        new_snapshot = {
            "status": updated_record.status,
            "analyst_notes": updated_record.analyst_notes,
            "is_locked": updated_record.is_locked
        }
        
        # 5. Programmatically create an immutable audit trail entry
        AuditLog.objects.create(
            record=updated_record,
            user=request.user if request.user.is_authenticated else None,
            action="ANALYST_MODIFICATION",
            old_value=old_snapshot,
            new_value=new_snapshot
        )
        
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def lock_record(self, request, pk=None):
        """
        Custom action endpoint to explicitly freeze a row for auditors.
        """
        record = self.get_object()
        if record.is_locked:
            return Response({"message": "Record is already locked."}, status=status.HTTP_400_BAD_REQUEST)
            
        record.is_locked = True
        record.status = 'APPROVED'
        record.save()
        
        AuditLog.objects.create(
            record=record,
            user=request.user if request.user.is_authenticated else None,
            action="AUDIT_LOCK_FINALIZED",
            old_value={"is_locked": False, "status": record.status},
            new_value={"is_locked": True, "status": "APPROVED"}
        )
        
        return Response({"status": "Record successfully locked and finalized for audit."})
