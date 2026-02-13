import os
import sys
import random
import datetime
from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

def get_random_date(start_year=2023, end_year=2026):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def generate_commissions():
    print("Starting Commission Data Generation...")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Fetch existing Policies to link against
            # We need SystemId (SourceRef), PolicyNumber (SourceNumber), ProviderRef
            # Use v_policies view for easier access if available, else querying policylookup is hard.
            # But v_policies exists!
            print("Fetching existing policies...")
            sql = """
            SELECT policy_id, policy_number, provider_ref, status 
            FROM v_policies 
            WHERE status != 'Cancelled'
            LIMIT 200
            """
            result = conn.execute(text(sql))
            policies = list(result)
            
            if not policies:
                print("No policies found! Run generate_heavy_data.py first.")
                return

            print(f"Found {len(policies)} policies. Generating commissions...")
            
            count = 0
            for pol in policies:
                # pol: (policy_id, policy_number, provider_ref, status)
                policy_id = pol[0]
                policy_num = pol[1]
                provider_ref = pol[2]
                
                if not provider_ref: 
                    continue
                
                # Generate 1-3 commission transactions per policy
                for _ in range(random.randint(1, 3)):
                    premium = random.randint(1000, 5000)
                    comm_rate = random.uniform(0.10, 0.20)
                    comm_amt = round(premium * comm_rate, 2)
                    
                    eff_date = get_random_date()
                    
                    insert_sql = """
                    INSERT INTO commissiondetail (
                        SystemId, 
                        SourceRef, 
                        SourceNumber, 
                        ProviderRef, 
                        PayToRef, 
                        WrittenPremiumAmt, 
                        CommissionableAmt, 
                        CommissionAmt, 
                        ChargedAmt,
                        TransactionEffectiveDt,
                        TransactionEntryDt,
                        TransactionTypeCd,
                        Type,
                        CarrierCd
                    ) VALUES (
                        NULL, 
                        :source_ref, 
                        :source_num, 
                        :provider_ref, 
                        :pay_to_ref, 
                        :premium, 
                        :premium, 
                        :comm_amt, 
                        :comm_amt,
                        :eff_date,
                        :eff_date,
                        'New Business',
                        'Commission',
                        'CarrierX'
                    )
                    """
                    
                    params = {
                        "source_ref": str(policy_id),
                        "source_num": policy_num,
                        "provider_ref": provider_ref,
                        "pay_to_ref": provider_ref,
                        "premium": premium,
                        "comm_amt": comm_amt,
                        "eff_date": eff_date
                    }
                    
                    conn.execute(text(insert_sql), params)
                    count += 1
            
            conn.commit()
            print(f"Success! Generated {count} commission records.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_commissions()
