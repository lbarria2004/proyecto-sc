from fpdf import FPDF
import sys

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Welcome to Python!", ln=1, align="C")
    
    print("Attempting pdf.output(dest='S')...")
    output = pdf.output(dest='S')
    print(f"Output type: {type(output)}")
    
    print("Attempting bytes(output)...")
    result = bytes(output)
    print("Success! Result length:", len(result))

except Exception as e:
    print(f"CRASHED: {e}")
    # Print traceback for details
    import traceback
    traceback.print_exc()
