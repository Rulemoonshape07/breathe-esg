from django.db import models
from companies.models import Company

class SCOPE(models.TextChoices):
    SCOPE1 = 'scope1', 'Scope 1 - Direct'
    SCOPE2 = 'scope2', 'Scope 2 - Indirect Electricity'
    SCOPE3 = 'scope3', 'Scope 3 - Value Chain'

class SOURCE_TYPE(models.TextChoices):
    SAP = 'sap', 'SAP Fuel/Procurement'
    UTILITY = 'utility', 'Utility Electricity'
    TRAVEL = 'travel', 'Corporate Travel'

class STATUS(models.TextChoices):
    PENDING = 'pending', 'Pending Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    SUSPICIOUS = 'suspicious', 'Flagged Suspicious'

class EmissionRecord(models.Model):
    # Multi-tenancy
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emissions')

    # Source tracking
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE.choices)
    source_file = models.CharField(max_length=500, blank=True)  # which upload produced this
    source_row = models.IntegerField(null=True, blank=True)      # row number in source file
    ingested_at = models.DateTimeField(auto_now_add=True)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    edited_by = models.CharField(max_length=100, blank=True)

    # Scope categorization
    scope = models.CharField(max_length=10, choices=SCOPE.choices)
    category = models.CharField(max_length=100)  # e.g. "diesel", "electricity", "flight"

    # Raw values (as received from source)
    raw_value = models.FloatField()
    raw_unit = models.CharField(max_length=50)

    # Normalized values (always in kg CO2e)
    normalized_value_kg_co2e = models.FloatField(null=True, blank=True)

    # Metadata
    activity_period_start = models.DateField(null=True, blank=True)
    activity_period_end = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # Review workflow
    status = models.CharField(max_length=20, choices=STATUS.choices, default=STATUS.PENDING)
    review_note = models.TextField(blank=True)
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Suspicious flag reason
    flag_reason = models.CharField(max_length=500, blank=True)

    # Audit lock — once locked, no edits allowed
    locked_for_audit = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} | {self.scope} | {self.category} | {self.raw_value} {self.raw_unit}"

    class Meta:
        ordering = ['-ingested_at']
