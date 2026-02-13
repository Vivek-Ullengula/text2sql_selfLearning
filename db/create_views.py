"""
Create MySQL VIEWs that pivot the EAV lookup tables into normal relational columns.
This eliminates the need for the SQL agent to understand EAV patterns.
"""
from sqlalchemy import create_engine, text

mysql_url = "mysql+pymysql://root:password@localhost:3306/custlight"
engine = create_engine(mysql_url)

views = {
    "v_customers": """
        CREATE OR REPLACE VIEW v_customers AS
        SELECT
            SystemId AS customer_id,
            MAX(CASE WHEN LookupKey = 'IndexName' THEN LookupValue END) AS customer_name,
            MAX(CASE WHEN LookupKey = 'Status' THEN LookupValue END) AS status,
            MAX(CASE WHEN LookupKey = 'CustomerNumber' THEN LookupValue END) AS customer_number,
            MAX(CASE WHEN LookupKey = 'EmailAddr' THEN LookupValue END) AS email,
            MAX(CASE WHEN LookupKey = 'PhoneNumberPrimary' THEN LookupValue END) AS phone,
            MAX(CASE WHEN LookupKey = 'BillCity' THEN LookupValue END) AS city,
            MAX(CASE WHEN LookupKey = 'BillState' THEN LookupValue END) AS state,
            MAX(CASE WHEN LookupKey = 'BillZip' THEN LookupValue END) AS zip_code,
            MAX(CASE WHEN LookupKey = 'LookupAddress' THEN LookupValue END) AS address,
            MAX(CASE WHEN LookupKey = 'TaxId' THEN LookupValue END) AS tax_id,
            MAX(CASE WHEN LookupKey = 'ProviderRef' THEN LookupValue END) AS provider_ref,
            MAX(CASE WHEN LookupKey = 'AddDt' THEN LookupValue END) AS add_date,
            MAX(CASE WHEN LookupKey = 'AddUser' THEN LookupValue END) AS add_user
        FROM customerlookup
        GROUP BY SystemId
    """,
    "v_policies": """
        CREATE OR REPLACE VIEW v_policies AS
        SELECT
            SystemId AS policy_id,
            MAX(CASE WHEN LookupKey = 'PolicyNumber' THEN LookupValue END) AS policy_number,
            MAX(CASE WHEN LookupKey = 'PolicyDisplayNumber' THEN LookupValue END) AS policy_display_number,
            MAX(CASE WHEN LookupKey = 'Status' THEN LookupValue END) AS status,
            MAX(CASE WHEN LookupKey = 'StatusCd' THEN LookupValue END) AS status_code,
            MAX(CASE WHEN LookupKey = 'CustomerRef' THEN LookupValue END) AS customer_ref,
            MAX(CASE WHEN LookupKey = 'ProviderRef' THEN LookupValue END) AS provider_ref,
            MAX(CASE WHEN LookupKey = 'ExpirationDt' THEN LookupValue END) AS expiration_date,
            MAX(CASE WHEN LookupKey = 'IndexName' THEN LookupValue END) AS index_name,
            MAX(CASE WHEN LookupKey = 'QuoteNumber' THEN LookupValue END) AS quote_number,
            MAX(CASE WHEN LookupKey = 'TransactionCd' THEN LookupValue END) AS transaction_code,
            MAX(CASE WHEN LookupKey = 'City' THEN LookupValue END) AS city,
            MAX(CASE WHEN LookupKey = 'StateProvCd' THEN LookupValue END) AS state,
            MAX(CASE WHEN LookupKey = 'PostalCode' THEN LookupValue END) AS postal_code,
            MAX(CASE WHEN LookupKey = 'EmailAddr' THEN LookupValue END) AS email,
            MAX(CASE WHEN LookupKey = 'ContactNumber' THEN LookupValue END) AS contact_number,
            MAX(CASE WHEN LookupKey = 'TaxId' THEN LookupValue END) AS tax_id
        FROM policylookup
        GROUP BY SystemId
    """,
    "v_providers": """
        CREATE OR REPLACE VIEW v_providers AS
        SELECT
            SystemId AS provider_id,
            MAX(CASE WHEN LookupKey = 'IndexName' THEN LookupValue END) AS provider_name,
            MAX(CASE WHEN LookupKey = 'ProviderType' THEN LookupValue END) AS provider_type,
            MAX(CASE WHEN LookupKey = 'ProviderNumber' THEN LookupValue END) AS provider_number,
            MAX(CASE WHEN LookupKey = 'BusinessName' THEN LookupValue END) AS business_name,
            MAX(CASE WHEN LookupKey = 'PersonalName' THEN LookupValue END) AS personal_name,
            MAX(CASE WHEN LookupKey = 'StatusCd' THEN LookupValue END) AS status_code,
            MAX(CASE WHEN LookupKey = 'City' THEN LookupValue END) AS city,
            MAX(CASE WHEN LookupKey = 'StateProvCd' THEN LookupValue END) AS state,
            MAX(CASE WHEN LookupKey = 'PostalCode' THEN LookupValue END) AS postal_code,
            MAX(CASE WHEN LookupKey = 'StreetAddr' THEN LookupValue END) AS street_address,
            MAX(CASE WHEN LookupKey = 'PhoneNumber' THEN LookupValue END) AS phone,
            MAX(CASE WHEN LookupKey = 'TaxID' THEN LookupValue END) AS tax_id,
            MAX(CASE WHEN LookupKey = 'ProducerAgency' THEN LookupValue END) AS producer_agency,
            MAX(CASE WHEN LookupKey = 'ProducerGroup' THEN LookupValue END) AS producer_group
        FROM providerlookup
        GROUP BY SystemId
    """,
    "v_commissions": """
        CREATE OR REPLACE VIEW v_commissions AS
        SELECT
            SystemId AS commission_id,
            CommissionAmt AS commission_amount,
            WrittenPremiumAmt AS premium_amount,
            TransactionEffectiveDt AS transaction_date,
            ProviderRef AS provider_ref,
            SourceRef AS policy_ref,
            SourceNumber AS policy_number,
            Type AS commission_type,
            CarrierCd AS carrier_code,
            ChargedAmt AS charged_amount
        FROM commissiondetail
    """,
}

with engine.connect() as conn:
    for view_name, sql in views.items():
        print(f"Creating view: {view_name}...")
        conn.execute(text(sql))
        # Verify
        result = conn.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
        count = result.scalar()
        print(f"  ✓ {view_name}: {count} rows")
    conn.commit()

# Quick test: the cross-table join that keeps failing
print("\n=== Test: Customers with their Providers ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT c.customer_name, p.provider_name
        FROM v_customers c
        JOIN v_providers p ON p.provider_id = CAST(c.provider_ref AS UNSIGNED)
    """))
    for row in result:
        print(f"  {row[0]} → {row[1]}")

    print("\n=== Test: Policies with Customer Names ===")
    result = conn.execute(text("""
        SELECT pol.policy_number, pol.status, c.customer_name
        FROM v_policies pol
        JOIN v_customers c ON c.customer_id = CAST(pol.customer_ref AS UNSIGNED)
    """))
    for row in result:
        print(f"  {row[0]} ({row[1]}) → {row[2]}")

print("\nAll views created and tested successfully!")
