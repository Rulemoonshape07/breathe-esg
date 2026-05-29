"""
Parsers for each data source.
SAP: flat file CSV (BAPI export format) — chosen because it's the most common
     format companies actually email/SFTP. IDoc is too complex for a prototype,
     OData requires live SAP connectivity. Flat file is realistic for batch ingestion.
Utility: CSV portal export — most utility portals (PG&E, Adani, MSEDCL) offer
         a "Download as CSV" button. PDF parsing would require OCR which is fragile.
Travel: Concur/Navan CSV expense report export — both platforms have a standard
        report export. API access requires OAuth setup not feasible in 4 days.
"""
import pandas as pd
import io
from datetime import datetime
import re

# Emission factors (kg CO2e per unit) — from GHG Protocol / IPCC AR5
EMISSION_FACTORS = {
    # Fuel (Scope 1)
    'diesel': 2.68,        # kg CO2e per litre
    'petrol': 2.31,        # kg CO2e per litre
    'gasoline': 2.31,
    'natural_gas': 2.04,   # kg CO2e per m3
    'lpg': 1.51,           # kg CO2e per litre
    # Electricity (Scope 2) — India grid average
    'electricity': 0.82,   # kg CO2e per kWh (India CEA 2023)
    # Travel (Scope 3)
    'flight_short': 0.255, # kg CO2e per km per passenger (< 3h)
    'flight_long': 0.195,  # kg CO2e per km per passenger (intercontinental)
    'hotel': 31.0,         # kg CO2e per room-night
    'taxi': 0.21,          # kg CO2e per km
    'train': 0.041,        # kg CO2e per km
    'rental_car': 0.17,    # kg CO2e per km
}

# Unit normalizers — convert everything to a base unit before applying emission factor
UNIT_CONVERTERS = {
    'l': 1, 'litre': 1, 'litres': 1, 'liter': 1, 'liters': 1,
    'gal': 3.785, 'gallon': 3.785, 'gallons': 3.785,
    'kwh': 1, 'kw-h': 1,
    'mwh': 1000,
    'gj': 277.78,           # GJ to kWh
    'm3': 1, 'cubic_meter': 1,
    'kg': 1,
    'km': 1, 'kilometer': 1, 'kilometres': 1,
    'mi': 1.609, 'mile': 1.609, 'miles': 1.609,
    'night': 1, 'room_night': 1,
}

# Airport distance lookup (km) — common routes; real deployment uses a geo API
AIRPORT_DISTANCES = {
    ('DEL','BOM'): 1148, ('BOM','DEL'): 1148,
    ('DEL','BLR'): 1740, ('BLR','DEL'): 1740,
    ('BOM','BLR'): 843,  ('BLR','BOM'): 843,
    ('DEL','HYD'): 1253, ('HYD','DEL'): 1253,
    ('BOM','HYD'): 710,  ('HYD','BOM'): 710,
    ('DEL','CCU'): 1305, ('CCU','DEL'): 1305,
    ('LHR','JFK'): 5539, ('JFK','LHR'): 5539,
    ('LHR','DEL'): 6700, ('DEL','LHR'): 6700,
    ('SIN','DEL'): 4150, ('DEL','SIN'): 4150,
    ('DXB','DEL'): 2190, ('DEL','DXB'): 2190,
}

def normalize_unit(value, unit):
    """Convert value to base unit. Returns (normalized_value, base_unit)."""
    unit_clean = unit.lower().strip().replace(' ', '_')
    factor = UNIT_CONVERTERS.get(unit_clean, None)
    if factor is None:
        return value, unit  # unknown unit, return as-is
    return value * factor, unit_clean

def get_emission_factor(category, base_unit):
    cat = category.lower().strip()
    for key in EMISSION_FACTORS:
        if key in cat or cat in key:
            return EMISSION_FACTORS[key]
    return None

def flag_suspicious(value, category, source_type):
    """Return a reason string if row looks suspicious, else empty string."""
    if value <= 0:
        return "Zero or negative activity value"
    if source_type == 'sap':
        if category in ['diesel','petrol'] and value > 50000:
            return f"Unusually high fuel volume: {value} L — verify plant code"
    if source_type == 'utility':
        if value > 1000000:
            return f"Electricity reading {value} kWh exceeds monthly threshold — possible meter multiplier error"
    if source_type == 'travel':
        if category == 'flight' and value > 20000:
            return f"Flight distance {value} km seems high — verify airport codes"
    return ""


def parse_sap_csv(file_content, company, batch):
    """
    SAP flat file (BAPI/SE16 export format).
    Columns: PLANT, MATERIAL, DESCRIPTION, QUANTITY, UNIT, POSTING_DATE, DOC_NUMBER
    German variants: WERK, MENGE, EINHEIT, BUCHUNGSDATUM handled via rename map.
    """
    errors = []
    records = []

    # Handle German column headers — SAP German installations are common
    rename_map = {
        'WERK': 'PLANT', 'MENGE': 'QUANTITY', 'EINHEIT': 'UNIT',
        'BUCHUNGSDATUM': 'POSTING_DATE', 'MATERIAL': 'MATERIAL',
        'BEZEICHNUNG': 'DESCRIPTION', 'BELEGNUMMER': 'DOC_NUMBER',
        # Also handle lowercase
        'werk': 'PLANT', 'menge': 'QUANTITY', 'einheit': 'UNIT',
    }

    try:
        df = pd.read_csv(io.StringIO(file_content), dtype=str)
        df.columns = [rename_map.get(c.strip(), c.strip().upper()) for c in df.columns]

        required = ['PLANT', 'MATERIAL', 'QUANTITY', 'UNIT', 'POSTING_DATE']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        batch.rows_total = len(df)

        for i, row in df.iterrows():
            try:
                raw_qty = float(str(row.get('QUANTITY', '')).replace(',', '.'))
                raw_unit = str(row.get('UNIT', 'L')).strip()
                material = str(row.get('MATERIAL', '')).strip().lower()
                description = str(row.get('DESCRIPTION', '')).strip()
                plant = str(row.get('PLANT', '')).strip()
                date_str = str(row.get('POSTING_DATE', '')).strip()

                # Date parsing — SAP uses DD.MM.YYYY, MM/DD/YYYY, YYYYMMDD
                activity_date = None
                for fmt in ['%d.%m.%Y', '%m/%d/%Y', '%Y%m%d', '%Y-%m-%d', '%d-%m-%Y']:
                    try:
                        activity_date = datetime.strptime(date_str, fmt).date()
                        break
                    except:
                        continue

                # Classify material into fuel category
                category = 'unknown'
                scope = 'scope1'
                if any(x in material or x in description.lower() for x in ['diesel','dies']):
                    category = 'diesel'
                elif any(x in material or x in description.lower() for x in ['petrol','gasoline','benzin']):
                    category = 'petrol'
                elif any(x in material or x in description.lower() for x in ['gas','lpg','erdgas']):
                    category = 'natural_gas'
                else:
                    category = material[:30] if material else 'fuel'

                norm_val, norm_unit = normalize_unit(raw_qty, raw_unit)
                ef = get_emission_factor(category, norm_unit)
                co2e = round(norm_val * ef, 4) if ef else None

                flag = flag_suspicious(raw_qty, category, 'sap')
                rec_status = 'suspicious' if flag else 'pending'

                records.append({
                    'company': company,
                    'source_type': 'sap',
                    'source_file': batch.filename,
                    'source_row': i + 2,
                    'scope': scope,
                    'category': category,
                    'raw_value': raw_qty,
                    'raw_unit': raw_unit,
                    'normalized_value_kg_co2e': co2e,
                    'activity_period_start': activity_date,
                    'activity_period_end': activity_date,
                    'location': plant,
                    'description': f"{description} | Plant: {plant} | Doc: {row.get('DOC_NUMBER','')}",
                    'status': rec_status,
                    'flag_reason': flag,
                })
                batch.rows_success += 1
                if flag:
                    batch.rows_suspicious += 1

            except Exception as e:
                errors.append(f"Row {i+2}: {str(e)}")
                batch.rows_failed += 1

    except Exception as e:
        errors.append(f"File parse error: {str(e)}")

    return records, errors


def parse_utility_csv(file_content, company, batch):
    """
    Utility portal CSV export (e.g., MSEDCL, Tata Power, BESCOM style).
    Columns: METER_ID, ACCOUNT_NUMBER, BILLING_PERIOD_START, BILLING_PERIOD_END,
             CONSUMPTION_KWH, TARIFF_CATEGORY, LOCATION, BILL_NUMBER
    Note: Billing periods often don't align with calendar months (e.g., 18th to 17th).
    """
    errors = []
    records = []

    rename_map = {
        'meter_id': 'METER_ID', 'account': 'ACCOUNT_NUMBER',
        'period_start': 'BILLING_PERIOD_START', 'start': 'BILLING_PERIOD_START',
        'period_end': 'BILLING_PERIOD_END', 'end': 'BILLING_PERIOD_END',
        'consumption': 'CONSUMPTION_KWH', 'units': 'CONSUMPTION_KWH',
        'kwh': 'CONSUMPTION_KWH', 'energy_kwh': 'CONSUMPTION_KWH',
        'tariff': 'TARIFF_CATEGORY', 'location': 'LOCATION',
        'facility': 'LOCATION', 'site': 'LOCATION',
        'bill_no': 'BILL_NUMBER', 'invoice': 'BILL_NUMBER',
    }

    try:
        df = pd.read_csv(io.StringIO(file_content), dtype=str)
        df.columns = [rename_map.get(c.strip().lower(), c.strip().upper()) for c in df.columns]

        batch.rows_total = len(df)

        for i, row in df.iterrows():
            try:
                kwh = float(str(row.get('CONSUMPTION_KWH', '0')).replace(',', ''))
                location = str(row.get('LOCATION', '')).strip()
                meter = str(row.get('METER_ID', '')).strip()
                tariff = str(row.get('TARIFF_CATEGORY', 'commercial')).strip()
                bill_no = str(row.get('BILL_NUMBER', '')).strip()

                period_start = None
                period_end = None
                for col, target in [('BILLING_PERIOD_START', 'start'), ('BILLING_PERIOD_END', 'end')]:
                    val = str(row.get(col, '')).strip()
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']:
                        try:
                            parsed = datetime.strptime(val, fmt).date()
                            if target == 'start':
                                period_start = parsed
                            else:
                                period_end = parsed
                            break
                        except:
                            continue

                # Electricity is always Scope 2
                ef = EMISSION_FACTORS['electricity']  # India grid factor
                co2e = round(kwh * ef, 4)

                flag = flag_suspicious(kwh, 'electricity', 'utility')
                rec_status = 'suspicious' if flag else 'pending'

                records.append({
                    'company': company,
                    'source_type': 'utility',
                    'source_file': batch.filename,
                    'source_row': i + 2,
                    'scope': 'scope2',
                    'category': 'electricity',
                    'raw_value': kwh,
                    'raw_unit': 'kWh',
                    'normalized_value_kg_co2e': co2e,
                    'activity_period_start': period_start,
                    'activity_period_end': period_end,
                    'location': location,
                    'description': f"Meter: {meter} | Tariff: {tariff} | Bill: {bill_no}",
                    'status': rec_status,
                    'flag_reason': flag,
                })
                batch.rows_success += 1
                if flag:
                    batch.rows_suspicious += 1

            except Exception as e:
                errors.append(f"Row {i+2}: {str(e)}")
                batch.rows_failed += 1

    except Exception as e:
        errors.append(f"File parse error: {str(e)}")

    return records, errors


def parse_travel_csv(file_content, company, batch):
    """
    Concur/Navan expense report CSV export.
    Columns: EMPLOYEE_ID, TRAVEL_DATE, CATEGORY, ORIGIN, DESTINATION,
             DISTANCE_KM, TRANSPORT_MODE, HOTEL_NAME, NIGHTS, AMOUNT_USD
    If distance not provided, airport codes are used to look up distance.
    Categories: flight, hotel, taxi, train, rental_car
    """
    errors = []
    records = []

    rename_map = {
        'employee': 'EMPLOYEE_ID', 'emp_id': 'EMPLOYEE_ID',
        'date': 'TRAVEL_DATE', 'travel_date': 'TRAVEL_DATE',
        'trip_date': 'TRAVEL_DATE',
        'category': 'CATEGORY', 'expense_type': 'CATEGORY', 'type': 'CATEGORY',
        'origin': 'ORIGIN', 'from': 'ORIGIN', 'departure': 'ORIGIN',
        'destination': 'DESTINATION', 'to': 'DESTINATION', 'arrival': 'DESTINATION',
        'distance': 'DISTANCE_KM', 'distance_km': 'DISTANCE_KM', 'km': 'DISTANCE_KM',
        'mode': 'TRANSPORT_MODE', 'transport': 'TRANSPORT_MODE',
        'hotel': 'HOTEL_NAME', 'property': 'HOTEL_NAME',
        'nights': 'NIGHTS', 'room_nights': 'NIGHTS',
    }

    try:
        df = pd.read_csv(io.StringIO(file_content), dtype=str)
        df.columns = [rename_map.get(c.strip().lower(), c.strip().upper()) for c in df.columns]

        batch.rows_total = len(df)

        for i, row in df.iterrows():
            try:
                category_raw = str(row.get('CATEGORY', 'flight')).strip().lower()
                travel_date_str = str(row.get('TRAVEL_DATE', '')).strip()
                origin = str(row.get('ORIGIN', '')).strip().upper()
                destination = str(row.get('DESTINATION', '')).strip().upper()
                emp = str(row.get('EMPLOYEE_ID', '')).strip()

                travel_date = None
                for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']:
                    try:
                        travel_date = datetime.strptime(travel_date_str, fmt).date()
                        break
                    except:
                        continue

                # Classify category
                if 'flight' in category_raw or 'air' in category_raw:
                    category = 'flight'
                    scope = 'scope3'
                    # Try to get distance
                    dist_raw = str(row.get('DISTANCE_KM', '')).strip()
                    try:
                        distance = float(dist_raw)
                    except:
                        # Fall back to airport code lookup
                        distance = AIRPORT_DISTANCES.get((origin, destination), 1000)
                    # Short vs long haul
                    ef_key = 'flight_long' if distance > 3000 else 'flight_short'
                    ef = EMISSION_FACTORS[ef_key]
                    co2e = round(distance * ef, 4)
                    raw_val = distance
                    raw_unit = 'km'
                    desc = f"Flight: {origin}→{destination} | Emp: {emp}"
                    flag = flag_suspicious(distance, 'flight', 'travel')

                elif 'hotel' in category_raw or 'accommodation' in category_raw or 'lodging' in category_raw:
                    category = 'hotel'
                    scope = 'scope3'
                    try:
                        nights = float(str(row.get('NIGHTS', '1')).strip())
                    except:
                        nights = 1
                    ef = EMISSION_FACTORS['hotel']
                    co2e = round(nights * ef, 4)
                    raw_val = nights
                    raw_unit = 'night'
                    hotel_name = str(row.get('HOTEL_NAME', destination)).strip()
                    desc = f"Hotel: {hotel_name} | {nights} nights | Emp: {emp}"
                    flag = ""

                elif 'taxi' in category_raw or 'cab' in category_raw or 'uber' in category_raw:
                    category = 'taxi'
                    scope = 'scope3'
                    try:
                        distance = float(str(row.get('DISTANCE_KM', '10')).strip())
                    except:
                        distance = 10
                    ef = EMISSION_FACTORS['taxi']
                    co2e = round(distance * ef, 4)
                    raw_val = distance
                    raw_unit = 'km'
                    desc = f"Taxi/Cab: {origin}→{destination} | Emp: {emp}"
                    flag = ""

                elif 'train' in category_raw or 'rail' in category_raw:
                    category = 'train'
                    scope = 'scope3'
                    try:
                        distance = float(str(row.get('DISTANCE_KM', '100')).strip())
                    except:
                        distance = AIRPORT_DISTANCES.get((origin, destination), 100)
                    ef = EMISSION_FACTORS['train']
                    co2e = round(distance * ef, 4)
                    raw_val = distance
                    raw_unit = 'km'
                    desc = f"Train: {origin}→{destination} | Emp: {emp}"
                    flag = ""

                elif 'rental' in category_raw or 'car' in category_raw:
                    category = 'rental_car'
                    scope = 'scope3'
                    try:
                        distance = float(str(row.get('DISTANCE_KM', '50')).strip())
                    except:
                        distance = 50
                    ef = EMISSION_FACTORS['rental_car']
                    co2e = round(distance * ef, 4)
                    raw_val = distance
                    raw_unit = 'km'
                    desc = f"Rental Car: {origin}→{destination} | Emp: {emp}"
                    flag = ""

                else:
                    category = category_raw
                    scope = 'scope3'
                    raw_val = 0
                    raw_unit = 'unknown'
                    co2e = None
                    desc = f"Unknown category: {category_raw} | Emp: {emp}"
                    flag = f"Unrecognized travel category: {category_raw}"

                rec_status = 'suspicious' if flag else 'pending'

                records.append({
                    'company': company,
                    'source_type': 'travel',
                    'source_file': batch.filename,
                    'source_row': i + 2,
                    'scope': scope,
                    'category': category,
                    'raw_value': raw_val,
                    'raw_unit': raw_unit,
                    'normalized_value_kg_co2e': co2e,
                    'activity_period_start': travel_date,
                    'activity_period_end': travel_date,
                    'location': f"{origin}→{destination}",
                    'description': desc,
                    'status': rec_status,
                    'flag_reason': flag,
                })
                batch.rows_success += 1
                if flag:
                    batch.rows_suspicious += 1

            except Exception as e:
                errors.append(f"Row {i+2}: {str(e)}")
                batch.rows_failed += 1

    except Exception as e:
        errors.append(f"File parse error: {str(e)}")

    return records, errors
