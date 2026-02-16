import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

PAYMENT_TYPES = ["Premium", "Installment", "Fee", "Reinstatement"]
NOTE_AUTHORS = ["System", "Underwriter: Sarah", "Agent: Mike", "Billing Dept"]
NOTE_TEXTS = [
    "Customer requested policy change.",
    "Payment received late but accepted.",
    "Policy review completed.",
    "Claim first notice of loss received via phone.",
    "Underwriting approval granted.",
    "Pending cancellation notice sent."
]

def generate_data():
    print("--- Generating Payments and Notes ---")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        # 1. Fetch References
        print("Fetching Policies and Claims...")
        policies = [row[0] for row in conn.execute(text("SELECT SystemId FROM policy")).fetchall()]
        claims = [row[0] for row in conn.execute(text("SELECT SystemId FROM claim")).fetchall()] # Assuming claim table uses SystemId?
        # Check if claim uses SystemId. inspect_claims.py showed SystemId.
        
        print(f"Found {len(policies)} Policies, {len(claims)} Claims.")

        if not policies:
            print("No policies found! Cannot generate payments.")
            return

        # 2. Generate Payments (Linked to Policies)
        print("Generating Payments...")
        for policy_id in policies:
            # Generate 0-3 payments per policy
            num_payments = random.randint(0, 3)
            for _ in range(num_payments):
                amount = round(random.uniform(50.0, 5000.0), 2)
                pay_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
                pay_type = random.choice(PAYMENT_TYPES)
                
                # Insert Payment
                xml = f"<Payment><Amount>{amount}</Amount><Date>{pay_date}</Date><Type>{pay_type}</Type></Payment>"
                res = conn.execute(text("INSERT INTO payment (XmlContent, UpdateUser, UpdateTimestamp) VALUES (:xml, 'GENERATOR', NOW())"), {"xml": xml})
                payment_id = res.lastrowid
                
                # Insert Lookups
                # Key: PolicyRef -> PolicyId
                conn.execute(text("INSERT INTO paymentlookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'PolicyRef', :val)"), {"id": payment_id, "val": str(policy_id)})
                # Key: Amount
                conn.execute(text("INSERT INTO paymentlookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'PaymentAmount', :val)"), {"id": payment_id, "val": str(amount)})
                # Key: PaymentDate
                conn.execute(text("INSERT INTO paymentlookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'PaymentDate', :val)"), {"id": payment_id, "val": pay_date})
                 # Key: PaymentType
                conn.execute(text("INSERT INTO paymentlookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'PaymentType', :val)"), {"id": payment_id, "val": pay_type})
        
        print("Payments Generated.")

        # 3. Generate Notes (Linked to Policies OR Claims)
        print("Generating Notes...")
        # Mix of policy notes and claim notes
        targets = []
        for p in policies: targets.append(('Policy', p))
        for c in claims: targets.append(('Claim', c))
        
        # Pick random 50% of targets to have notes
        targets = random.sample(targets, k=int(len(targets) * 0.5))
        
        for target_type, target_id in targets:
            text_content = random.choice(NOTE_TEXTS)
            author = random.choice(NOTE_AUTHORS)
            date_str = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d")
            
            # Insert Note
            xml = f"<Note><Text>{text_content}</Text><Author>{author}</Author><Date>{date_str}</Date></Note>"
            res = conn.execute(text("INSERT INTO note (XmlContent, UpdateUser, UpdateTimestamp) VALUES (:xml, 'GENERATOR', NOW())"), {"xml": xml})
            note_id = res.lastrowid
            
            # Insert Lookups
            # Generic ParentRef pattern? Or PolicyRef/ClaimRef?
            # Let's use specific refs for clarity in Views
            if target_type == 'Policy':
                conn.execute(text("INSERT INTO notelookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'PolicyRef', :val)"), {"id": note_id, "val": str(target_id)})
            else:
                conn.execute(text("INSERT INTO notelookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'ClaimRef', :val)"), {"id": note_id, "val": str(target_id)})
            
            conn.execute(text("INSERT INTO notelookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'Author', :val)"), {"id": note_id, "val": author})
            conn.execute(text("INSERT INTO notelookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'NoteDate', :val)"), {"id": note_id, "val": date_str})
             # Note Text snippet (first 50 chars)
            conn.execute(text("INSERT INTO notelookup (SystemId, LookupKey, LookupValue) VALUES (:id, 'NoteText', :val)"), {"id": note_id, "val": text_content[:50]})

        conn.commit()
        print("Notes Generated.")

if __name__ == "__main__":
    generate_data()
