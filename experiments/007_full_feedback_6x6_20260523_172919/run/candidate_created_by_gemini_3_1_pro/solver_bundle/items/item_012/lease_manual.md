# Commercial Lease CAM Reconciliation Manual

## 1. Operating Expenses (OpEx) Pool
The Annual OpEx Pool is the sum of all allowable operating expenses incurred during the year 2025 (Day 1 to Day 365).
Allowable expenses include:
- Routine maintenance, cleaning, landscaping, and security.
- Minor repairs (any repair costing strictly less than 500,000 cents).
- Utility bills for common areas.

Excluded expenses (DO NOT add to the OpEx Pool):
- Capital Expenses (CapEx), defined as any improvement, replacement, or repair costing 500,000 cents or more.
- Landlord's late fees, penalties, or legal fees.
- Direct Charges (expenses explicitly attributed to a specific tenant's negligence or direct request in the communications).

## 2. Property Management Fee
After summing the allowable expenses to find the Base OpEx Pool, a Property Management Fee is added.
The fee is exactly 5% (0.05) of the Base OpEx Pool.
USE INTEGER MATH ONLY. Do not use floats.
Property Management Fee = (Base OpEx Pool * 5) // 100
Total OpEx Pool = Base OpEx Pool + Property Management Fee

## 3. Tenant Pro-Rata Share
A tenant's share of the Total OpEx Pool is based on their "Occupancy Fraction".
Occupancy Fraction = (Tenant's Total Square-Foot-Days) / (Total Building SqFt * 365)

Total Building SqFt is defined in property_data.json.
A tenant's Total Square-Foot-Days is the sum of (SqFt occupied * number of days occupied at that SqFt).
Day counting is inclusive. Occupying a suite from Day 10 to Day 20 means 11 days of occupancy (20 - 10 + 1).
If a tenant expands into another suite, their Total Square-Foot-Days is the sum of the Square-Foot-Days for all their suites.
Building SqFt-Days = Total Building SqFt * 365.

Base CAM Charge = (Total OpEx Pool * Tenant's Total Square-Foot-Days) // Building SqFt-Days

## 4. Direct Charges
If a tenant has any Direct Charges identified in the communications, add the full amount of those Direct Charges to their Base CAM Charge.

## 5. CAM Caps
Some tenants may have a negotiated CAM Cap, expressed in cents per square foot per year.
The CAM Cap applies to the tenant's entire occupancy. Calculate the Max Base Charge as:
Max Base Charge = (Cap * Tenant's Total Square-Foot-Days) // 365
If the calculated Base CAM Charge exceeds the Max Base Charge, reduce the Base CAM Charge to the Max Base Charge.
Direct Charges are NOT subject to the CAM Cap and are added AFTER applying the cap.

Final CAM Charge = (Capped Base CAM Charge) + Direct Charges

**Final Output Instructions**: Return the exact integer amount in cents for each tenant listed in the initial rent roll.
