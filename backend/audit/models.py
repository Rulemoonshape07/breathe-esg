from django.db import models

class AuditLog(models.Model):
    emission_record = models.ForeignKey('emissions.EmissionRecord', on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50)
    performed_by = models.CharField(max_length=100)
    performed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    previous_value = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} by {self.performed_by} at {self.performed_at}"

    class Meta:
        ordering = ['-performed_at']