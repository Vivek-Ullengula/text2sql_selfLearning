import os
import sys
import random
import datetime
from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

# Constants
STATUSES = ['Open', 'Closed', 'Reopened', 'Litigation']
DESCRIPTIONS = [
    'Rear-end collision at traffic light',
    'Water damage from burst pipe',
    'Wind damage to roof',
    'Slip and fall in driveway',
    'Theft of personal property',
    'Engine fire while driving',
    'Tree fell on garage'
]
ADJUSTERS = ['Sarah Connor', 'John Rico', 'Ellen Ripley', 'Rick Deckard', 'Dana Scully']

def get_random_date(start_year=2024, end_year=2026):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def generate_claims():
    print("Starting Claim Data Generation...")
    
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Fetch valid Policy IDs (SystemId from policy table)
            print("Fetching Policy References...")
            result = conn.execute(text("SELECT SystemId FROM policy"))
            policy_ids = [row[0] for row in result]
            
            if not policy_ids:
                print("No policies found! Please run generate_heavy_data.py first.")
                return

            # 2. Generate Claims (let's make 50 claims)
            print(f"Generating 50 claims linked to {len(policy_ids)} policies...")
            
            claims_created = 0
            
            for _ in range(50):
                # Random Policy
                policy_id = random.choice(policy_ids)
                
                # Claim Data
                claim_num = f"CLM-{random.randint(10000, 99999)}"
                loss_date = get_random_date()
                reported_date = loss_date + datetime.timedelta(days=random.randint(0, 5))
                status = random.choice(STATUSES)
                incurred = round(random.uniform(500.00, 50000.00), 2)
                desc = random.choice(DESCRIPTIONS)
                adjuster = random.choice(ADJUSTERS)
                
                # Insert Entity
                result = conn.execute(text("INSERT INTO claim (SystemId, XmlContent) VALUES (NULL, :xml)"),
                    {"xml": f"<Claim ClaimNumber='{claim_num}' />"})
                claim_id = result.lastrowid
                
                # Insert Attributes
                attrs = {
                    'ClaimNumber': claim_num,
                    'PolicyRef': str(policy_id), # Linking to Policy SystemId
                    'LossDt': str(loss_date),
                    'ReportedDt': str(reported_date),
                    'Status': status,
                    'TotalIncurred': str(incurred),
                    'Description': desc,
                    'Adjuster': adjuster
                }
                
                for key, val in attrs.items():
                    conn.execute(text("""
                        INSERT INTO claimlookup (SystemId, LookupKey, LookupValue)
                        VALUES (:id, :key, :val)
                    """), {"id": claim_id, "key": key, "val": str(val)})
                
                claims_created += 1

            conn.commit()
            print(f"Success! Created {claims_created} claims.")

    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    generate_claims()
