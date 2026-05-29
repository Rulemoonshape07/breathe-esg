from rest_framework import serializers
from .models import UploadBatch

class UploadBatchSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    class Meta:
        model = UploadBatch
        fields = '__all__'
