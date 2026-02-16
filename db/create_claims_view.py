import os
import sys
from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

def create_view():
    print("Creating v_claims View...")
    
    view_sql = """
    CREATE OR REPLACE VIEW v_claims AS
    SELECT
        c.SystemId AS claim_id,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'ClaimNumber' LIMIT 1) AS claim_number,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'Status' LIMIT 1) AS status,
        CAST((SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'TotalIncurred' LIMIT 1) AS DECIMAL(10,2)) AS total_incurred,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'LossDt' LIMIT 1) AS loss_date,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'ReportedDt' LIMIT 1) AS reported_date,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'Description' LIMIT 1) AS description,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'Adjuster' LIMIT 1) AS adjuster,
        (SELECT LookupValue FROM claimlookup WHERE SystemId = c.SystemId AND LookupKey = 'PolicyRef' LIMIT 1) AS policy_ref
    FROM claim c;
    """
    
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text(view_sql))
            print("Success! v_claims created.")
            
            # Text query
            result = conn.execute(text("SELECT * FROM v_claims LIMIT 5"))
            for row in result:
                print(row)

    except Exception as e:
        print(f"View creation failed: {e}")

if __name__ == "__main__":
    create_view()
