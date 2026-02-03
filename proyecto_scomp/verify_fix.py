import sys
import os

print("Verifying critical imports...")
try:
    # Mimic the imports in app.py
    from services.calculations import process_data_vejez, process_data_sobrevivencia
    from utils.helpers import clean_number, get_sort_key_vejez, get_sort_key_sobrevivencia
    print("✅ Imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ An error occurred: {e}")
    sys.exit(1)
