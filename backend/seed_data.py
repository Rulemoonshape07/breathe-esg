"""Seed realistic sample data for all 3 sources."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from companies.models import Company
from emissions.models import EmissionRecord
from audit.models import AuditLog
from ingestion.models import UploadBatch
from datetime import date

# Create companies
c1, _ = Company.objects.get_or_create(name="Tata Steel Ltd", slug="tata-steel", defaults={'industry': 'Manufacturing'})
c2, _ = Company.objects.get_or_create(name="Infosys BPM", slug="infosys-bpm", defaults={'industry': 'IT Services'})

# Create batches
b1 = UploadBatch.objects.create(company=c1, source_type='sap', filename='TATA_STEEL_FUEL_Q1_2024.csv', status='done', rows_total=6, rows_success=5, rows_failed=1, rows_suspicious=1)
b2 = UploadBatch.objects.create(company=c1, source_type='utility', filename='MSEDCL_Q1_2024_METERS.csv', status='done', rows_total=4, rows_success=4, rows_failed=0, rows_suspicious=1)
b3 = UploadBatch.objects.create(company=c2, source_type='travel', filename='INFOSYS_CONCUR_Q1_2024.csv', status='done', rows_total=5, rows_success=5, rows_failed=0, rows_suspicious=1)

# SAP records (Scope 1)
sap_records = [
    dict(company=c1, source_type='sap', source_file='TATA_STEEL_FUEL_Q1_2024.csv', source_row=2, scope='scope1', category='diesel', raw_value=12500.0, raw_unit='L', normalized_value_kg_co2e=33500.0, activity_period_start=date(2024,1,1), activity_period_end=date(2024,1,31), location='PLANT_JAMSHEDPUR', description='Diesel for DG sets | Plant: JAMSHEDPUR | Doc: 5000123456', status='approved', reviewed_by='priya.analyst', flag_reason=''),
    dict(company=c1, source_type='sap', source_file='TATA_STEEL_FUEL_Q1_2024.csv', source_row=3, scope='scope1', category='diesel', raw_value=9800.0, raw_unit='L', normalized_value_kg_co2e=26264.0, activity_period_start=date(2024,2,1), activity_period_end=date(2024,2,29), location='PLANT_KALINGANAGAR', description='Diesel for blast furnace vehicles | Plant: KALINGANAGAR | Doc: 5000123457', status='approved', reviewed_by='priya.analyst', flag_reason=''),
    dict(company=c1, source_type='sap', source_file='TATA_STEEL_FUEL_Q1_2024.csv', source_row=4, scope='scope1', category='petrol', raw_value=3200.0, raw_unit='L', normalized_value_kg_co2e=7392.0, activity_period_start=date(2024,3,1), activity_period_end=date(2024,3,31), location='PLANT_JAMSHEDPUR', description='Petrol for company vehicles | Plant: JAMSHEDPUR | Doc: 5000123460', status='pending', flag_reason=''),
    dict(company=c1, source_type='sap', source_file='TATA_STEEL_FUEL_Q1_2024.csv', source_row=5, scope='scope1', category='natural_gas', raw_value=85000.0, raw_unit='m3', normalized_value_kg_co2e=173400.0, activity_period_start=date(2024,1,1), activity_period_end=date(2024,1,31), location='PLANT_JAMSHEDPUR', description='Natural gas for furnaces | Plant: JAMSHEDPUR | Doc: 5000123461', status='suspicious', flag_reason='Unusually high fuel volume: 85000 m3 — verify plant code'),
    dict(company=c1, source_type='sap', source_file='TATA_STEEL_FUEL_Q1_2024.csv', source_row=6, scope='scope1', category='lpg', raw_value=450.0, raw_unit='L', normalized_value_kg_co2e=679.5, activity_period_start=date(2024,2,1), activity_period_end=date(2024,2,29), location='PLANT_KALINGANAGAR', description='LPG for canteen | Plant: KALINGANAGAR | Doc: 5000123462', status='pending', flag_reason=''),
]

# Utility records (Scope 2)
util_records = [
    dict(company=c1, source_type='utility', source_file='MSEDCL_Q1_2024_METERS.csv', source_row=2, scope='scope2', category='electricity', raw_value=125000.0, raw_unit='kWh', normalized_value_kg_co2e=102500.0, activity_period_start=date(2024,1,18), activity_period_end=date(2024,2,17), location='Jamshedpur Plant - Building A', description='Meter: MH-JMS-001 | Tariff: HT-Commercial | Bill: MSEDCL/24/001234', status='approved', reviewed_by='rahul.analyst', flag_reason=''),
    dict(company=c1, source_type='utility', source_file='MSEDCL_Q1_2024_METERS.csv', source_row=3, scope='scope2', category='electricity', raw_value=98400.0, raw_unit='kWh', normalized_value_kg_co2e=80688.0, activity_period_start=date(2024,2,18), activity_period_end=date(2024,3,17), location='Jamshedpur Plant - Building B', description='Meter: MH-JMS-002 | Tariff: HT-Commercial | Bill: MSEDCL/24/001235', status='pending', flag_reason=''),
    dict(company=c1, source_type='utility', source_file='MSEDCL_Q1_2024_METERS.csv', source_row=4, scope='scope2', category='electricity', raw_value=1250000.0, raw_unit='kWh', normalized_value_kg_co2e=1025000.0, activity_period_start=date(2024,1,18), activity_period_end=date(2024,2,17), location='Kalinganagar Plant - Smelter', description='Meter: OR-KLN-001 | Tariff: EHT-Industrial | Bill: CESU/24/000890', status='suspicious', flag_reason='Electricity reading 1250000 kWh exceeds monthly threshold — possible meter multiplier error'),
    dict(company=c1, source_type='utility', source_file='MSEDCL_Q1_2024_METERS.csv', source_row=5, scope='scope2', category='electricity', raw_value=45000.0, raw_unit='kWh', normalized_value_kg_co2e=36900.0, activity_period_start=date(2024,3,18), activity_period_end=date(2024,4,17), location='Admin Block', description='Meter: MH-ADM-001 | Tariff: LT-Commercial | Bill: MSEDCL/24/001560', status='pending', flag_reason=''),
]

# Travel records (Scope 3)
travel_records = [
    dict(company=c2, source_type='travel', source_file='INFOSYS_CONCUR_Q1_2024.csv', source_row=2, scope='scope3', category='flight', raw_value=1148.0, raw_unit='km', normalized_value_kg_co2e=292.74, activity_period_start=date(2024,1,15), activity_period_end=date(2024,1,15), location='DEL→BOM', description='Flight: DEL→BOM | Emp: EMP-10023', status='approved', reviewed_by='meera.analyst', flag_reason=''),
    dict(company=c2, source_type='travel', source_file='INFOSYS_CONCUR_Q1_2024.csv', source_row=3, scope='scope3', category='flight', raw_value=6700.0, raw_unit='km', normalized_value_kg_co2e=1306.5, activity_period_start=date(2024,2,10), activity_period_end=date(2024,2,10), location='DEL→LHR', description='Flight: DEL→LHR | Emp: EMP-10045', status='pending', flag_reason=''),
    dict(company=c2, source_type='travel', source_file='INFOSYS_CONCUR_Q1_2024.csv', source_row=4, scope='scope3', category='hotel', raw_value=3.0, raw_unit='night', normalized_value_kg_co2e=93.0, activity_period_start=date(2024,2,10), activity_period_end=date(2024,2,13), location='LHR→LHR', description='Hotel: The Marriott London | 3 nights | Emp: EMP-10045', status='pending', flag_reason=''),
    dict(company=c2, source_type='travel', source_file='INFOSYS_CONCUR_Q1_2024.csv', source_row=5, scope='scope3', category='taxi', raw_value=25.0, raw_unit='km', normalized_value_kg_co2e=5.25, activity_period_start=date(2024,1,15), activity_period_end=date(2024,1,15), location='BOM→BOM', description='Taxi/Cab: Airport to Office | Emp: EMP-10023', status='pending', flag_reason=''),
    dict(company=c2, source_type='travel', source_file='INFOSYS_CONCUR_Q1_2024.csv', source_row=6, scope='scope3', category='flight', raw_value=25000.0, raw_unit='km', normalized_value_kg_co2e=4875.0, activity_period_start=date(2024,3,5), activity_period_end=date(2024,3,5), location='DEL→SYD', description='Flight: DEL→SYD | Emp: EMP-10078', status='suspicious', flag_reason='Flight distance 25000 km seems high — verify airport codes'),
]

for rd in sap_records + util_records + travel_records:
    rec = EmissionRecord.objects.create(**rd)
    AuditLog.objects.create(emission_record=rec, action='ingested', performed_by='system', note='Seeded sample data')

print("✅ Sample data seeded successfully")
print(f"Companies: {Company.objects.count()}")
print(f"Emission records: {EmissionRecord.objects.count()}")
print(f"Upload batches: {UploadBatch.objects.count()}")
