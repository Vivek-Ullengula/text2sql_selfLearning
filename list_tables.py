import os
import sys
from sqlalchemy import create_engine, text

# Hardcoded DB URL from text2sql.py
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

try:
    engine = create_engine(DB_URL)
except Exception as e:
    print(f"Connection setup failed: {e}")
    sys.exit(1)

print("\n--- Listing Tables & Row Counts ---")
try:
    with engine.connect() as conn:
        tables = conn.execute(text("SHOW TABLES")).fetchall()
        print(f"Total Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            # Count rows
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                print(f"- {table_name}: {count} rows")
            except Exception as e:
                print(f"- {table_name}: Error counting ({e})")
except Exception as e:
    print(f"Error connecting: {e}")
