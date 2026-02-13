from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://root:password@localhost:3306/custlight"

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("--- Commission Detail Columns ---")
        sql = """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA='custlight' AND TABLE_NAME='commissiondetail'
        ORDER BY ORDINAL_POSITION
        """
        result = conn.execute(text(sql))
        for row in result:
            print(f"{row[0]} ({row[1]})")
            
except Exception as e:
    print(f"Error: {e}")
