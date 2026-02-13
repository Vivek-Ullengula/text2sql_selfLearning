from sqlalchemy import create_engine, text

# Hardcoded DB URL
DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("--- Commission Detail Schema ---")
        try:
            result = conn.execute(text("DESCRIBE commissiondetail"))
            for row in result:
                # Access by index for safety
                print(f"{row[0]} | {row[1]}")
        except Exception as e:
             # Fallback to SELECT * LIMIT 1 if DESCRIBE fails (though it shouldn't on MySQL)
             print(f"DESCRIBE failed: {e}. Trying SELECT...")
             res = conn.execute(text("SELECT * FROM commissiondetail LIMIT 1"))
             print("Columns:", res.keys())

except Exception as e:
    print(f"Connection Error: {e}")
