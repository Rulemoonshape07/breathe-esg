from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import UploadBatch
from .serializers import UploadBatchSerializer
from .parsers import parse_sap_csv, parse_utility_csv, parse_travel_csv
from emissions.models import EmissionRecord
from audit.models import AuditLog
from companies.models import Company

class UploadBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UploadBatch.objects.select_related('company').all()
    serializer_class = UploadBatchSerializer

class IngestView(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        file = request.FILES.get('file')
        source_type = request.data.get('source_type')
        company_id = request.data.get('company_id')

        if not all([file, source_type, company_id]):
            return Response({'error': 'file, source_type, and company_id are required'}, status=400)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=404)

        batch = UploadBatch.objects.create(
            company=company,
            source_type=source_type,
            filename=file.name,
            status='processing'
        )

        try:
            content = file.read().decode('utf-8', errors='replace')
            parsers = {'sap': parse_sap_csv, 'utility': parse_utility_csv, 'travel': parse_travel_csv}
            parser = parsers.get(source_type)
            if not parser:
                raise ValueError(f"Unknown source type: {source_type}")

            records_data, errors = parser(content, company, batch)

            created = []
            for rd in records_data:
                rec = EmissionRecord.objects.create(**rd)
                AuditLog.objects.create(
                    emission_record=rec,
                    action='ingested',
                    performed_by='system',
                    note=f"Ingested from {file.name} via {source_type} parser"
                )
                created.append(rec.id)

            batch.status = 'done'
            batch.error_log = '\n'.join(errors)
            batch.save()

            return Response({
                'batch_id': batch.id,
                'rows_total': batch.rows_total,
                'rows_success': batch.rows_success,
                'rows_failed': batch.rows_failed,
                'rows_suspicious': batch.rows_suspicious,
                'errors': errors[:10],
                'record_ids': created,
            })

        except Exception as e:
            batch.status = 'failed'
            batch.error_log = str(e)
            batch.save()
            return Response({'error': str(e)}, status=500)
