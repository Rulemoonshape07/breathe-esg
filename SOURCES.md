# Sources Research — Three Data Sources

## 1. SAP — Fuel & Procurement Data

**Format researched:** SAP SE16 flat file export (table browser) and ME2M (purchase orders by material)

**What I learned:**
- SAP has multiple export paths: IDoc (EDI), OData (REST-like), BAPI (RFC function calls), 
  and flat file (the most common for ad-hoc exports)
- German column headers are real: MENGE (quantity), EINHEIT (unit), BUCHUNGSDATUM (posting date), 
  WERK (plant code), BEZEICHNUNG (description)
- Plant codes like "1001" or "JAMSHEDPUR" are internal identifiers that mean nothing without the 
  plant master data table (T001W). In a real deployment you'd join with this table
- Units from SAP: L (litre), KG, M3, TO (tonne), ST (each/piece), GAL — inconsistent across clients
- Date format is DD.MM.YYYY by default in German SAP, MM/DD/YYYY in US SAP

**Why my sample data looks the way it does:**
- Two plants: JAMSHEDPUR and KALINGANAGAR — realistic for a steel manufacturer (Tata Steel's actual plants)
- Materials: DIESEL001, PETROL002 — SAP material numbers are alphanumeric codes
- One row with 85,000 m³ natural gas — intentionally suspicious to demonstrate flagging
- Document numbers starting with 5000xxxxxx — real SAP FI document number format
- Mix of January/February/March dates — realistic quarterly batch

**What would break in a real deployment:**
- Plant codes without the T001W lookup table are meaningless
- Material numbers need a material master mapping to know what category they are
- Some SAP exports use semicolon delimiter, not comma
- Character encoding issues with German umlauts (ü, ö, ä) — need UTF-8 handling

## 2. Utility — Electricity Data

**Format researched:** MSEDCL (Maharashtra State Electricity Distribution), Tata Power, 
BESCOM (Bangalore) portal CSV exports; also reviewed Green Button standard (US)

**What I learned:**
- Indian utility portals all have "Download Consumption Data" or "Download Bill" as CSV
- Billing periods do NOT align with calendar months — MSEDCL bills from 18th to 17th, 
  Tata Power from 15th to 14th depending on your meter reading cycle
- Meter IDs and account numbers are separate (meter is physical, account is billing)
- Tariff categories matter for reporting: HT-Commercial, LT-Industrial, EHT rates 
  imply different consumption patterns
- Some industrial meters have a multiplier factor (CT ratio) — a reading of 1000 kWh with 
  multiplier 100 is actually 100,000 kWh. This is the source of the 1,000,000 kWh flag

**Why my sample data looks the way it does:**
- Meter IDs like MH-JMS-001 — realistic format (state code + site + number)
- MSEDCL/24/001234 bill numbers — format matches actual MSEDCL invoices
- Billing period 18th Jan to 17th Feb — realistic non-calendar alignment
- One row with 1,250,000 kWh flagged — a smelter consumes this but it should be verified

**What would break in a real deployment:**
- CT ratio / multiplier not captured in the CSV — need to handle this separately
- Some utility portals export in MWh, some in kWh — need unit detection
- PDF bills are common alongside CSV — PDF path not handled
- International sites would have different grid emission factors

## 3. Corporate Travel — Concur/Navan

**Format researched:** Concur Travel & Expense report CSV export; Navan CSV export format;
SAP Concur API documentation (v4); ICAO carbon calculator methodology

**What I learned:**
- Concur's standard expense report export includes: expense type, transaction date, 
  vendor name, amount, currency — but NOT always origin/destination or distance
- Navan (formerly TripActions) exports trip data separately from expense data
- Flights: distance is often not in the export — you get airport codes (IATA 3-letter). 
  Distance must be computed via Great Circle distance
- Hotels: room nights are the unit, not a distance. Emission factor is per room-night (HCMI standard)
- Ground transport: often just "taxi" or "Uber" with an amount, no distance. Distance is estimated
  from the expense amount divided by typical per-km rate
- Scope 3 Category 6 (Business Travel) and Category 7 (Employee Commuting) are separate 
  categories in the GHG Protocol

**Why my sample data looks the way it does:**
- Employee IDs like EMP-10023 — realistic corporate HR format
- DEL→BOM flight using known IATA codes — 1,148 km is the correct great-circle distance
- DEL→LHR flight (6,700 km) — long-haul, uses different emission factor
- One row with DEL→SYD at 25,000 km — intentionally suspicious (Sydney is ~10,400 km from Delhi)
- Hotel with 3 nights — realistic for an international business trip

**What would break in a real deployment:**
- Airport codes outside our lookup table would default to 1,000 km — a rough estimate
- Concur column names vary by company configuration (each org customizes field names)
- Currency conversion needed if expenses are in multiple currencies
- Employee home office location needed to separate Scope 3 Cat 6 vs Cat 7
