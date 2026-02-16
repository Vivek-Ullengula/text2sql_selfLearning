import os
from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

def create_views():
    print("--- Creating v_payments and v_notes Views ---")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        # v_payments
        print("Creating v_payments View...")
        conn.execute(text("""
        CREATE OR REPLACE VIEW v_payments AS
        SELECT
            p.SystemId AS payment_id,
            MAX(CASE WHEN pl.LookupKey = 'PolicyRef' THEN pl.LookupValue END) AS policy_ref,
            CAST(MAX(CASE WHEN pl.LookupKey = 'PaymentAmount' THEN pl.LookupValue END) AS DECIMAL(10,2)) AS amount,
            MAX(CASE WHEN pl.LookupKey = 'PaymentDate' THEN pl.LookupValue END) AS payment_date,
            MAX(CASE WHEN pl.LookupKey = 'PaymentType' THEN pl.LookupValue END) AS payment_type
        FROM payment p
        LEFT JOIN paymentlookup pl ON p.SystemId = pl.SystemId
        GROUP BY p.SystemId;
        """))
        
        # v_notes
        print("Creating v_notes View...")
        conn.execute(text("""
        CREATE OR REPLACE VIEW v_notes AS
        SELECT
            n.SystemId AS note_id,
            MAX(CASE WHEN nl.LookupKey = 'PolicyRef' THEN nl.LookupValue END) AS policy_ref,
            MAX(CASE WHEN nl.LookupKey = 'ClaimRef' THEN nl.LookupValue END) AS claim_ref,
            MAX(CASE WHEN nl.LookupKey = 'Author' THEN nl.LookupValue END) AS author,
            MAX(CASE WHEN nl.LookupKey = 'NoteDate' THEN nl.LookupValue END) AS note_date,
            MAX(CASE WHEN nl.LookupKey = 'NoteText' THEN nl.LookupValue END) AS note_text
        FROM note n
        LEFT JOIN notelookup nl ON n.SystemId = nl.SystemId
        GROUP BY n.SystemId;
        """))
        
        # Verification
        print("Verifying Views...")
        p_count = conn.execute(text("SELECT COUNT(*) FROM v_payments")).scalar()
        n_count = conn.execute(text("SELECT COUNT(*) FROM v_notes")).scalar()
        print(f"Success! v_payments: {p_count} rows, v_notes: {n_count} rows.")

if __name__ == "__main__":
    create_views()
