import sys
import os

print("Verifying imports...")
try:
    import config.settings
    print("✅ config.settings imported")
    import utils.helpers
    print("✅ utils.helpers imported")
    import services.pdf_parser
    print("✅ services.pdf_parser imported")
    import services.gemini_api
    print("✅ services.gemini_api imported")
    import services.calculations
    print("✅ services.calculations imported")
    import services.report_gen
    print("✅ services.report_gen imported")
    print("All modules imported successfully.")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
