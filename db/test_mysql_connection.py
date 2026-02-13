"""Quick test: verify MySQL connection and EAV query pattern."""
from sqlalchemy import create_engine, text

mysql_url = "mysql+pymysql://root:password@localhost:3306/custlight"
engine = create_engine(mysql_url)

with engine.connect() as conn:
    # Test 1: Count entities
    print("=== Entity Counts ===")
    for table in ["customerlookup", "policylookup", "providerlookup", "commissiondetail"]:
        r = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        print(f"  {table}: {r.scalar()} rows")

    # Test 2: EAV pivot query (customer details)
    print("\n=== Customer Details (EAV pivot) ===")
    r = conn.execute(text("""
        SELECT SystemId,
            MAX(CASE WHEN LookupKey = 'IndexName' THEN LookupValue END) AS name,
            MAX(CASE WHEN LookupKey = 'Status' THEN LookupValue END) AS status,
            MAX(CASE WHEN LookupKey = 'EmailAddr' THEN LookupValue END) AS email,
            MAX(CASE WHEN LookupKey = 'BillCity' THEN LookupValue END) AS city,
            MAX(CASE WHEN LookupKey = 'BillState' THEN LookupValue END) AS state
        FROM customerlookup
        GROUP BY SystemId
        LIMIT 5
    """))
    for row in r:
        print(f"  ID={row[0]}, Name={row[1]}, Status={row[2]}, Email={row[3]}, City={row[4]}, State={row[5]}")

    # Test 3: Policy lookup
    print("\n=== Policy Details (EAV pivot) ===")
    r = conn.execute(text("""
        SELECT SystemId,
            MAX(CASE WHEN LookupKey = 'PolicyNumber' THEN LookupValue END) AS policy_number,
            MAX(CASE WHEN LookupKey = 'Status' THEN LookupValue END) AS status,
            MAX(CASE WHEN LookupKey = 'CustomerRef' THEN LookupValue END) AS customer_ref
        FROM policylookup
        GROUP BY SystemId
        LIMIT 5
    """))
    for row in r:
        print(f"  PolicyID={row[0]}, Number={row[1]}, Status={row[2]}, CustomerRef={row[3]}")

    # Test 4: Commission detail (relational)
    print("\n=== Commission Details (relational) ===")
    r = conn.execute(text("SELECT SystemId, CommissionAmt, CommissionPct, PremiumAmt, ProviderRef FROM commissiondetail LIMIT 5"))
    for row in r:
        print(f"  ID={row[0]}, Commission=${row[1]}, Pct={row[2]}, Premium=${row[3]}, Provider={row[4]}")

print("\nAll tests passed!")
