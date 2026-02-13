"""Load all CustLight SQL dump files into MySQL."""
import subprocess
import sys
from pathlib import Path

MYSQL_BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
MYSQL_USER = "root"
MYSQL_PASS = "password"
DATABASE = "custlight"
DUMP_DIR = Path(__file__).resolve().parent.parent / "data" / "sql_dump" / "Dump20260211"


def load_dump():
    sql_files = sorted(DUMP_DIR.glob("*.sql"))
    print(f"Found {len(sql_files)} SQL files in {DUMP_DIR}")

    success = 0
    failed = []

    for sql_file in sql_files:
        print(f"  Loading {sql_file.name}...", end=" ")
        try:
            result = subprocess.run(
                [MYSQL_BIN, "-u", MYSQL_USER, f"-p{MYSQL_PASS}", DATABASE],
                stdin=open(sql_file, "r", encoding="utf-8"),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print("OK")
                success += 1
            else:
                err = result.stderr.strip().split("\n")[-1] if result.stderr else "Unknown error"
                print(f"FAILED: {err}")
                failed.append((sql_file.name, err))
        except Exception as e:
            print(f"ERROR: {e}")
            failed.append((sql_file.name, str(e)))

    print(f"\n{'='*50}")
    print(f"Loaded: {success}/{len(sql_files)}")
    if failed:
        print(f"Failed: {len(failed)}")
        for name, err in failed:
            print(f"  - {name}: {err}")


if __name__ == "__main__":
    load_dump()
