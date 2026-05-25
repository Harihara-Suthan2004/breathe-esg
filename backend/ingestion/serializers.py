from rest_framework import serializers
from .models import NormalizedEmissionRecord, Organization, AuditLog

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    source_type = serializers.CharField(source='source_payload.source_type', read_only=True)
    
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'id', 'organization', 'organization_name', 'source_type', 
            'ghg_scope', 'category_label', 'start_date', 'end_date', 
            'original_quantity', 'original_unit', 'co2e_emissions_mt', 
            'status', 'analyst_notes', 'is_locked', 'created_at', 'updated_at'
        ]
        # Prevent the frontend from directly manipulating critical calculation parameters
        read_only_fields = ['co2e_emissions_mt', 'ghg_scope', 'created_at', 'updated_at']