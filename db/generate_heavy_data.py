import os
import sys
import random
import datetime
from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

try:
    engine = create_engine(DB_URL)
except Exception as e:
    print(f"Connection setup failed: {e}")
    sys.exit(1)

# Helper Data
STATES = ['CA', 'TX', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'WA', 'AZ']
CITIES = ['CityA', 'CityB', 'CityC', 'Springfield', 'Metropolis', 'Gotham', 'Smallville']
STATUSES = ['Active', 'Active', 'Active', 'Cancelled', 'Pending', 'Expired'] # Weighted
POLICY_TYPES = ['Personal Auto', 'Homeowners', 'Commercial General Liability', 'Workers Comp']
TRANS_CODES = ['New Business', 'Renewal', 'Endorsement', 'Cancellation']

FIRST_NAMES = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

PROVIDERS = ['Alpha Insurance', 'Beta Agency', 'Gamma Brokers', 'Delta Risk', 'Epsilon Coverage']

def get_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def get_random_date(start_year=2023, end_year=2026):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def run_sql(conn, sql, params=None):
    conn.execute(text(sql), params or {})

def generate_data():
    print("Starting Heavy Data Generation...")
    
    with engine.connect() as conn:
        # 1. Create Providers
        provider_ids = []
        print("Creating Providers...")
        for name in PROVIDERS:
            # Create main entity with dummy XML
            result = conn.execute(text("INSERT INTO provider (SystemId, XmlContent) VALUES (NULL, :xml)"), 
                {"xml": f"<Provider IndexName='{name}' />"})
            p_id = result.lastrowid
            provider_ids.append(p_id)
            
            # Add Lookup Attributes
            attrs = {
                'IndexName': name,
                'ProviderType': 'Agency',
                'StatusCd': 'Active',
                'StateProvCd': random.choice(STATES),
                'City': random.choice(CITIES)
            }
            for key, val in attrs.items():
                conn.execute(text("""
                    INSERT INTO providerlookup (SystemId, LookupKey, LookupValue)
                    VALUES (:id, :key, :val)
                """), {"id": p_id, "key": key, "val": val})

        # 2. Create Customers
        customer_ids = []
        print("Creating 100 Customers...")
        for _ in range(100):
            # Create entity with dummy XML
            name = get_random_name()
            result = conn.execute(text("INSERT INTO customer (SystemId, XmlContent) VALUES (NULL, :xml)"),
                {"xml": f"<Customer IndexName='{name}' />"})
            c_id = result.lastrowid
            customer_ids.append(c_id)
            
            p_ref = random.choice(provider_ids)
            state = random.choice(STATES)
            
            attrs = {
                'IndexName': name,
                'Status': random.choice(STATUSES),
                'BillState': state,
                'BillCity': random.choice(CITIES),
                'ProviderRef': str(p_ref),
                'EmailAddr': f"{name.replace(' ', '.').lower()}@example.com",
                'CustomerNumber': f"CUST-{c_id:05d}"
            }
            for key, val in attrs.items():
                conn.execute(text("""
                    INSERT INTO customerlookup (SystemId, LookupKey, LookupValue)
                    VALUES (:id, :key, :val)
                """), {"id": c_id, "key": key, "val": val})

        # 3. Create Policies
        print("Creating 200 Policies...")
        for _ in range(200):
            # Create entity with dummy XML
            result = conn.execute(text("INSERT INTO policy (SystemId, XmlContent) VALUES (NULL, :xml)"),
                 {"xml": "<Policy />"})
            pol_id = result.lastrowid
            
            c_ref = random.choice(customer_ids)
            # Find provider of this customer? Or just any? We'll pick random from list to simplify
            p_ref = random.choice(provider_ids) 
            
            status = random.choice(STATUSES)
            exp_date = get_random_date()
            
            attrs = {
                'PolicyNumber': f"POL-{pol_id:08d}",
                'Status': status,
                'CustomerRef': str(c_ref),
                'ProviderRef': str(p_ref),
                'ExpirationDt': str(exp_date),
                'StateProvCd': random.choice(STATES),
                'TransactionCd': random.choice(TRANS_CODES),
                'IndexName': f"{random.choice(POLICY_TYPES)} Policy"
            }
            for key, val in attrs.items():
                conn.execute(text("""
                    INSERT INTO policylookup (SystemId, LookupKey, LookupValue)
                    VALUES (:id, :key, :val)
                """), {"id": pol_id, "key": key, "val": val})
        
        conn.commit()
    
    print("Success! Created 5 Providers, 100 Customers, 200 Policies.")

if __name__ == "__main__":
    generate_data()
