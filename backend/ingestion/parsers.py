import csv
import json
from datetime import datetime
from decimal import Decimal
from .models import RawSourcePayload, NormalizedEmissionRecord

# --- Industry Standard ESG Emission Factors (Fictionalized for Prototype) ---
# Emits Metric Tons (MT) of CO2e per unit consumed
EMISSION_FACTORS = {
    'DIESEL_LITERS': Decimal('0.00268'),      # Scope 1
    'GASOLINE_GALLONS': Decimal('0.00889'),   # Scope 1
    'ELECTRICITY_KWH': Decimal('0.00038'),    # Scope 2
    'FLIGHT_MILES': Decimal('0.00013'),       # Scope 3
}

def parse_sap_csv(file_path, organization):
    """
    Ingests realistic SAP Procurement/Fuel CSV data.
    Handles German column headers, custom plant codes, and format conversions.
    """
    records_created = 0
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 1. Capture absolute source state for provenance tracking
            raw_payload = RawSourcePayload.objects.create(
                organization=organization,
                source_type='SAP',
                file_name=file_path.split('/')[-1],
                raw_payload=row
            )
            
            # 2. Extract and translate complex headers
            # Real SAP maps standard properties to custom fields (e.g., Menge = Quantity)
            raw_mat_code = row.get('MAT_CODE', '').strip()
            quantity_str = row.get('MENGE_QTY', '0').strip()
            unit = row.get('ME_UNIT', '').strip().upper()
            date_str = row.get('BUDAT_DATE', '').strip() # SAP posting date
            
            # 3. Parse fields safely
            try:
                original_qty = Decimal(quantity_str)
                # Handle common European dot-separated dates (DD.MM.YYYY)
                start_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                end_date = start_date  # Transaction event happens on a specific day
            except (ValueError, TypeError):
                # If crucial structural attributes fail, skip row (or handle as failed)
                continue
                
            # 4. Normalize and calculate carbon footprint
            factor_key = f"{raw_mat_code}_{unit}"
            factor = EMISSION_FACTORS.get(factor_key, Decimal('0.001')) # Fallback baseline factor
            co2e = original_qty * factor
            
            # 5. Programmatic Suspicious Activity Flagging
            status = 'PENDING'
            notes = None
            if original_qty <= 0:
                status = 'SUSPICIOUS'
                notes = "Anomaly detected: Fuel procurement volume cannot be zero or negative."
            elif original_qty > 50000:
                status = 'SUSPICIOUS'
                notes = "Anomaly detected: Outlier volume exceeds transaction caps (>50k)."

            # 6. Save clean data to the Unified Table
            NormalizedEmissionRecord.objects.create(
                organization=organization,
                source_payload=raw_payload,
                ghg_scope='SCOPE_1',
                category_label=f"SAP Fuel - {raw_mat_code}",
                start_date=start_date,
                end_date=end_date,
                original_quantity=original_qty,
                original_unit=unit,
                co2e_emissions_mt=co2e,
                status=status,
                analyst_notes=notes
            )
            records_created += 1
            
    return records_created


def parse_utility_csv(file_path, organization):
    """
    Ingests Electricity Portal Data.
    Handles non-calendar aligned billing cycle dates (e.g., Jan 15 - Feb 14).
    """
    records_created = 0
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_payload = RawSourcePayload.objects.create(
                organization=organization,
                source_type='UTILITY',
                file_name=file_path.split('/')[-1],
                raw_payload=row
            )
            
            try:
                qty = Decimal(row.get('Consumption_kWh', '0'))
                # Handle date strings formatted as YYYY-MM-DD
                start_date = datetime.strptime(row.get('Billing_Start', ''), '%Y-%m-%d').date()
                end_date = datetime.strptime(row.get('Billing_End', ''), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                continue
                
            co2e = qty * EMISSION_FACTORS['ELECTRICITY_KWH']
            
            status = 'PENDING'
            notes = None
            # Flag extreme anomalies: Power bills that drop to exactly zero imply broken infrastructure metrics
            if qty == 0:
                status = 'SUSPICIOUS'
                notes = "Anomaly detected: Zero energy consumption logged across active facility window."
                
            NormalizedEmissionRecord.objects.create(
                organization=organization,
                source_payload=raw_payload,
                ghg_scope='SCOPE_2',
                category_label="Purchased Grid Electricity",
                start_date=start_date,
                end_date=end_date,
                original_quantity=qty,
                original_unit="KWH",
                co2e_emissions_mt=co2e,
                status=status,
                analyst_notes=notes
            )
            records_created += 1
    return records_created


def parse_travel_json(json_string, organization):
    """
    Ingests simulated corporate travel network data (e.g., Concur REST payloads).
    Handles missing distance parameters by calculating via flight estimates.
    """
    records_created = 0
    data = json.loads(json_string)
    bookings = data.get('bookings', [])
    
    for booking in bookings:
        raw_payload = RawSourcePayload.objects.create(
            organization=organization,
            source_type='TRAVEL',
            file_name='concur_api_stream.json',
            raw_payload=booking
        )
        
        try:
            booking_date = datetime.strptime(booking.get('date', ''), '%Y-%m-%d').date()
            distance_miles = Decimal(str(booking.get('distance_miles', 0)))
        except (ValueError, TypeError):
            continue
            
        status = 'PENDING'
        notes = None
        
        # Real-World Catch: Travel APIs often omit distances if a leg was canceled or missing an airport pair
        if distance_miles == 0:
            status = 'SUSPICIOUS'
            notes = "Suspicious Data: Airport distance missing from route record. Estimated default calculation applied."
            # Fallback estimation for missing API telemetry
            distance_miles = Decimal('500.0000') 
            
        co2e = distance_miles * EMISSION_FACTORS['FLIGHT_MILES']
        
        NormalizedEmissionRecord.objects.create(
            organization=organization,
            source_payload=raw_payload,
            ghg_scope='SCOPE_3',
            category_label=f"Business Travel - Flight ({booking.get('class', 'Economy')})",
            start_date=booking_date,
            end_date=booking_date,
            original_quantity=distance_miles,
            original_unit="MILES",
            co2e_emissions_mt=co2e,
            status=status,
            analyst_notes=notes
        )
        records_created += 1
        
    return records_created