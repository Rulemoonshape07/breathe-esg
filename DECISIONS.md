# Decisions — Breathe ESG Emissions Ingestion

## SAP: Why Flat File CSV (not IDoc, not OData)

**Chose:** SAP SE16/ME2M flat file export as CSV

**Why:** IDoc is the "correct" SAP integration format but requires SAP BASIS configuration, 
middleware (typically SAP PI/PO or BTP), and a live connection. OData via SAP Gateway is 
similar — it's real-time but requires API credentials, VPN, and SAP Fiori configuration.

In practice, the sustainability or finance team pulls a flat file export from SE16 (table browser)
or uses ME2M (purchase orders by material) and emails it. That is the actual workflow at most 
mid-size enterprises.

**Column handling:** SAP German installations output `WERK` (plant), `MENGE` (quantity), 
`EINHEIT` (unit), `BUCHUNGSDATUM` (posting date). The parser has a rename map for these.

**Date formats:** SAP uses DD.MM.YYYY by default. Some configurations export MM/DD/YYYY or 
YYYYMMDD. The parser tries all three.

**What I'd ask the PM:** What SAP module is the client using — MM (materials management) or 
FI (financials)? This changes the export table and column names significantly.

## Utility: Why CSV Portal Export (not PDF, not API)

**Chose:** CSV download from utility portal (MSEDCL, Tata Power, BESCOM style)

**Why:** PDF parsing requires OCR or layout-aware extraction — fragile, breaks on any format 
change. Utility APIs exist (Green Button in the US, some Indian utilities have APIs) but require 
OAuth registration with each utility, which is a business relationship problem not a technical one.

The facilities team at most companies logs into the utility portal once a month and downloads a CSV.
This is the realistic workflow. Our parser handles the billing period misalignment (e.g., bill runs 
18th to 17th, not 1st to 31st) by storing actual period start/end rather than assuming calendar months.

**Emission factor choice:** India CEA grid emission factor 0.82 kg CO₂e/kWh (2023 value). 
A client with facilities in multiple states ideally gets state-level factors (Tamil Nadu vs UP vary 
significantly). We use national average for simplicity.

**What I'd ask the PM:** Are all facilities in India, or are there international sites? UK/EU 
have lower grid factors and different reporting requirements.

## Travel: Why Concur/Navan CSV Export (not API)

**Chose:** Concur/Navan expense report CSV export

**Why:** Both Concur and Navan have REST APIs, but accessing them requires OAuth client credentials 
registered with the client's corporate travel admin. That's a 2-week procurement/IT process. 
The CSV export ("Download Report as CSV") is available to any admin immediately.

**Airport code distance lookup:** Concur exports often don't include distance — just origin/destination
airport codes. We have a lookup table for common Indian routes and major international routes. 
For production, this would call an aviation distance API (Great Circle Mapper, OAG).

**Category classification:** We map expense categories to emission factors: flight → ICAO factors 
by distance, hotel → HCMI standard, taxi/cab/Uber → road vehicle factor.

**What I'd ask the PM:** Does the client use Concur, Navan, or another platform? Column names 
differ across platforms. Also — do they want employee-level reporting or just aggregate?

## Status Machine: pending → approved/rejected

Records are born as `pending` (or `suspicious` if auto-flagged). An analyst can approve or reject.
Once approved records are locked for audit, they cannot be changed. This is a one-way gate — 
intentional, because audit trails need to be immutable.

## Suspicious Flagging Rules

Auto-flagged if:
- Value is zero or negative (almost always a data error)
- SAP fuel > 50,000 L in a month (plausible for large plant but worth verifying)
- Utility reading > 1,000,000 kWh (possible meter multiplier error — a common utility billing mistake)
- Flight distance > 20,000 km (longer than any commercial route — likely data error)

These thresholds are conservative by design — better to flag too much than miss real errors.
