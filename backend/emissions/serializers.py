from rest_framework import serializers
from .models import EmissionRecord

class EmissionRecordSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    class Meta:
        model = EmissionRecord
        fields = '__all__'
