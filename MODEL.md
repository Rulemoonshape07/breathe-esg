# Data Model — Breathe ESG Emissions Ingestion

## Core Design Decisions

### Multi-Tenancy
Every `EmissionRecord` has a required FK to `Company`. All API queries filter by company.
This is row-level tenancy rather than schema-level — acceptable for a prototype; production would add
`company` to every index and enforce it at the query layer.

### EmissionRecord — Central Table

| Field | Purpose |
|---|---|
| `company` | FK to Company — multi-tenancy anchor |
| `source_type` | `sap` / `utility` / `travel` — which ingestion pipeline produced this |
| `source_file` | Filename of the upload batch — trace back to origin |
| `source_row` | Row number in the CSV — enables exact error reproduction |
| `ingested_at` | Auto-timestamp — immutable, set on creation |
| `last_edited_at` + `edited_by` | Track if an analyst manually corrected a value |
| `scope` | `scope1` / `scope2` / `scope3` — GHG Protocol categorization |
| `category` | Granular: `diesel`, `electricity`, `flight`, `hotel`, `taxi`, etc. |
| `raw_value` + `raw_unit` | Exactly as received from source — never modified |
| `normalized_value_kg_co2e` | Always kg CO₂e — computed at ingestion using emission factors |
| `activity_period_start/end` | Actual activity period (not ingestion date — billing periods ≠ calendar months) |
| `status` | `pending` → `approved` / `rejected` / `suspicious` |
| `locked_for_audit` | Boolean — once true, no edits permitted |
| `flag_reason` | Why the system auto-flagged this row as suspicious |

### Scope Categorization
- **Scope 1** (Direct): SAP fuel data — diesel, petrol, LPG, natural gas combustion
- **Scope 2** (Indirect electricity): Utility meter consumption × India grid factor (0.82 kg CO₂e/kWh, CEA 2023)
- **Scope 3** (Value chain): Business travel — flights, hotels, ground transport

### Source-of-Truth Tracking
Every record carries `source_file` + `source_row`. If an analyst questions a number, we can open the
original CSV and point to the exact row. The `UploadBatch` table stores the filename and parse statistics.
If the record was manually edited, `last_edited_at` and `edited_by` are populated.

### Unit Normalization Strategy
Raw values are stored as-is (`raw_value`, `raw_unit`). Normalization happens at parse time:
1. Convert unit to base unit (litres, kWh, km, nights) using `UNIT_CONVERTERS` lookup
2. Apply emission factor → kg CO₂e stored in `normalized_value_kg_co2e`
3. Raw values are never overwritten — if emission factors update, we can re-compute

Emission factors used:
- Diesel: 2.68 kg CO₂e/L (GHG Protocol)
- Petrol: 2.31 kg CO₂e/L
- Natural gas: 2.04 kg CO₂e/m³
- Electricity: 0.82 kg CO₂e/kWh (India CEA grid factor 2023)
- Flights: 0.255 kg CO₂e/km (short haul), 0.195 (long haul >3000km) (ICAO)
- Hotel: 31 kg CO₂e/room-night (HCMI standard)

### Audit Trail
`AuditLog` records every state change:
- `ingested` — system creates on upload
- `approved` / `rejected` — analyst action with timestamp + note
- Every log entry has `performed_by` and `performed_at`

Once `locked_for_audit = True`, the approve/reject API returns 400. Lock is set manually by admin
before sending to auditors.

### UploadBatch Table
Tracks each file upload with parse statistics: rows_total, rows_success, rows_failed, rows_suspicious.
Links back to the company and source type. Error messages stored in `error_log` for debugging.

## What Would Change in Production
- Schema-level multi-tenancy (separate schemas per client) for strict data isolation
- Emission factor versioning — factors update annually, need to track which version was used
- User authentication — analyst identity currently passed as string, should be auth.User FK
- PostgreSQL instead of SQLite for concurrent writes
- S3 or GCS for file storage instead of local disk
