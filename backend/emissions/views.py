from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import EmissionRecord
from .serializers import EmissionRecordSerializer
from audit.models import AuditLog

class EmissionRecordViewSet(viewsets.ModelViewSet):
    queryset = EmissionRecord.objects.select_related('company').all()
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        company = self.request.query_params.get('company')
        source = self.request.query_params.get('source_type')
        status_filter = self.request.query_params.get('status')
        scope = self.request.query_params.get('scope')
        if company:
            qs = qs.filter(company_id=company)
        if source:
            qs = qs.filter(source_type=source)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if scope:
            qs = qs.filter(scope=scope)
        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        if record.locked_for_audit:
            return Response({'error': 'Record is locked for audit'}, status=400)
        record.status = 'approved'
        record.reviewed_by = request.data.get('reviewed_by', 'analyst')
        record.reviewed_at = timezone.now()
        record.review_note = request.data.get('note', '')
        record.save()
        AuditLog.objects.create(
            emission_record=record,
            action='approved',
            performed_by=record.reviewed_by,
            note=record.review_note
        )
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        record = self.get_object()
        if record.locked_for_audit:
            return Response({'error': 'Record is locked for audit'}, status=400)
        record.status = 'rejected'
        record.reviewed_by = request.data.get('reviewed_by', 'analyst')
        record.reviewed_at = timezone.now()
        record.review_note = request.data.get('note', '')
        record.save()
        AuditLog.objects.create(
            emission_record=record,
            action='rejected',
            performed_by=record.reviewed_by,
            note=record.review_note
        )
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        from django.db.models import Sum, Count
        qs = self.get_queryset()
        return Response({
            'total_records': qs.count(),
            'pending': qs.filter(status='pending').count(),
            'approved': qs.filter(status='approved').count(),
            'rejected': qs.filter(status='rejected').count(),
            'suspicious': qs.filter(status='suspicious').count(),
            'total_kg_co2e': qs.filter(status='approved').aggregate(t=Sum('normalized_value_kg_co2e'))['t'] or 0,
            'by_scope': {
                'scope1': qs.filter(scope='scope1').aggregate(t=Sum('normalized_value_kg_co2e'))['t'] or 0,
                'scope2': qs.filter(scope='scope2').aggregate(t=Sum('normalized_value_kg_co2e'))['t'] or 0,
                'scope3': qs.filter(scope='scope3').aggregate(t=Sum('normalized_value_kg_co2e'))['t'] or 0,
            },
            'by_source': {
                'sap': qs.filter(source_type='sap').count(),
                'utility': qs.filter(source_type='utility').count(),
                'travel': qs.filter(source_type='travel').count(),
            }
        })
