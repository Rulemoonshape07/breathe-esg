from django.db import models
from companies.models import Company

class UploadBatch(models.Model):
    SOURCE_CHOICES = [('sap','SAP'),('utility','Utility'),('travel','Travel')]
    STATUS_CHOICES = [('processing','Processing'),('done','Done'),('failed','Failed')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    filename = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    rows_total = models.IntegerField(default=0)
    rows_success = models.IntegerField(default=0)
    rows_failed = models.IntegerField(default=0)
    rows_suspicious = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.company.name} | {self.source_type} | {self.filename}"

    class Meta:
        ordering = ['-uploaded_at']
