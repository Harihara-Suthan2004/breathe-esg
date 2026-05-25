from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    """
    Achieves Multi-Tenancy. 
    Every enterprise client belongs to an Organization.
    Data is isolated strictly by this key.
    """
    name = models.CharField(db_index=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RawSourcePayload(models.Model):
    """
    Tracks Source-of-Truth Provenance.
    Stores the exact, unaltered data that came out of SAP, the utility portal, or Concur.
    """
    SOURCE_TYPES = [
        ('SAP', 'SAP ERP Export'),
        ('UTILITY', 'Utility Portal CSV'),
        ('TRAVEL', 'Corporate Travel API'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='raw_payloads')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    raw_payload = models.JSONField(help_text="Stores the exact raw row/JSON map received from the source system")
    ingested_at = models.DateTimeField(auto_now_add=True)


class NormalizedEmissionRecord(models.Model):
    """
    The clean, unified schema after running normalization logic.
    Maps messy data to explicit Scopes and standardizes calculations.
    """
    SCOPE_CHOICES = [
        ('SCOPE_1', 'Scope 1 - Direct Emissions (Fuel/Procurement)'),
        ('SCOPE_2', 'Scope 2 - Indirect Emissions (Electricity)'),
        ('SCOPE_3', 'Scope 3 - Value Chain (Business Travel)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('SUSPICIOUS', 'Flagged / Suspicious'),
        ('APPROVED', 'Approved & Locked'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='records')
    source_payload = models.OneToOneField(RawSourcePayload, on_delete=models.CASCADE, related_name='normalized_record')
    
    # ESG Meta Categorization
    ghg_scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    category_label = models.CharField(max_length=100, help_text="e.g., Diesel Fuel, Purchased Electricity, Economy Flight")
    
    # Non-calendar aligned billing periods or active transaction window
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Original Data Inflow Profile
    original_quantity = models.DecimalField(max_digits=15, decimal_places=4)
    original_unit = models.CharField(max_length=50, help_text="e.g., Liters, kWh, Gallons, Miles")
    
    # Standardized Normalization Calculations
    co2e_emissions_mt = models.DecimalField(max_digits=15, decimal_places=4, help_text="Calculated Metric Tons of CO2e emissions")
    
    # Status & Audit Locks
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    analyst_notes = models.TextField(blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Prevent manual changes if the record has already been locked for audit
        if self.pk:
            original = NormalizedEmissionRecord.objects.get(pk=self.pk)
            if original.is_locked:
                raise ValueError("This record is officially locked for auditing and cannot be modified.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.organization.name} - {self.ghg_scope} - {self.status}"


class AuditLog(models.Model):
    """
    Immutable Audit Trail.
    Logs every historical action, who did it, and the data changes for legal verification.
    """
    record = models.ForeignKey(NormalizedEmissionRecord, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, help_text="e.g., STATUS_CHANGE, VALUE_EDIT, DATA_LOCK")
    old_value = models.JSONField(blank=True, null=True, help_text="Snapshot before modification")
    new_value = models.JSONField(blank=True, null=True, help_text="Snapshot after modification")
    timestamp = models.DateTimeField(auto_now_add=True)