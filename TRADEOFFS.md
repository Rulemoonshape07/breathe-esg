# Tradeoffs — Three Things I Deliberately Did Not Build

## 1. User Authentication and Role-Based Access

**Not built.** The API has no auth — any request is allowed.

**Why not:** Setting up Django auth + JWT + React login adds ~4 hours and zero domain value for this
prototype. The evaluators care about data model quality and ingestion logic, not whether I can wire up 
a login page.

**What the real version needs:** Auth is critical. Analysts should only see their assigned companies. 
There should be separate roles: `ingestion_admin` (can upload), `analyst` (can review), `auditor` 
(read-only, locked records only). Django's built-in auth + DRF token auth is the right path. 
In production, SSO via the client's identity provider (Okta, Azure AD) is standard.

## 2. Emission Factor Versioning

**Not built.** Emission factors are hardcoded constants in `parsers.py`.

**Why not:** Factor versioning requires a `EmissionFactor` model with effective date ranges, 
a re-computation job to retroactively update `normalized_value_kg_co2e` when factors change, 
and a UI to manage factors. This is ~2 days of work and only matters after the first year of data.

**What the real version needs:** The GHG Protocol and IPCC update factors periodically. India's CEA 
grid factor changes every year. A client running a 3-year emissions inventory needs to recompute 
historical data with the factors valid at that time. The model should store `emission_factor_used` 
and `emission_factor_version` on each record.

## 3. PDF Utility Bill Ingestion

**Not built.** Only CSV utility exports are supported, not PDF bills.

**Why not:** PDF parsing is fragile — it requires either layout-aware extraction (pdfplumber) or 
OCR (Tesseract), and utility bill formats vary by provider, state, and billing system version. 
Getting robust PDF parsing right for even 3 utility providers would take the full 4 days alone.

**What the real version needs:** A PDF ingestion pipeline using pdfplumber for machine-readable PDFs 
and Tesseract + a trained layout model for scanned bills. Realistically, this is a dedicated 
microservice problem, not something you bolt onto a Django app. Some companies solve this by 
contracting with utility data aggregators (Urjanet, Arcadia) who handle the bill parsing and 
expose a normalized API.
