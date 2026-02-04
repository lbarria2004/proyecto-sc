import pandas as pd
from services.report_gen import PDFReportVejez, PDFReportSobrevivencia

def test_vejez_report():
    print("Testing PDFReportVejez...")
    try:
        # Mock Header Data
        header_data = {
            'nombre': 'JUAN PEREZ', 'rut': '12.345.678-9', 'saldo_uf': '1000', 
            'n_scomp': '12345', 'tipo_pension': 'VEJEZ', 'valor_uf_str': '35.000'
        }
        
        # Mock Table Data
        df = pd.DataFrame({
            'Compania': ['AFP MODELO'], 'Modalidad': ['Retiro Programado'], 
            'Pension_UF': ['10,00'], 'Pension_Bruta': [350000], 
            'Descuento_Salud_7%': [24500], 'Pension_Liquida': [325500], 
            'Pensión + Bono': [325500]
        })
        
        item = {
            'titulo': 'Retiro Programado', 'tipo': 'RP', 'tabla': df, 
            'col_title_pdf': 'Pensión + Bono', 'eld_info': None
        }
        
        pdf = PDFReportVejez(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.print_header_data(header_data)
        pdf.print_table(item['titulo'], item['tabla'], item['tipo'], item['col_title_pdf'], item.get('eld_info'))
        
        # This is the critical part - testing the output generation
        pdf_output = pdf.output()
        pdf_bytes = bytes(pdf_output)
        
        print(f"SUCCESS: Generated {len(pdf_bytes)} bytes for Vejez report.")
        
    except Exception as e:
        print(f"FAILED Vejez: {e}")
        import traceback
        traceback.print_exc()

def test_sobrevivencia_report():
    print("\nTesting PDFReportSobrevivencia...")
    try:
        # Mock Header Data
        header_data = {
            'nombre': 'MARIA GONZALEZ', 'rut': '9.876.543-2', 'saldo_uf': '500', 
            'n_scomp': '54321', 'tipo_pension': 'SOBREVIVENCIA', 'valor_uf_str': '35.000'
        }
        beneficiarios = [{'nombre': 'PEDRO', 'rut': '1.1.1', 'parentesco': 'Hijo'}]
        
        # Mock Table Data for Sobrevivencia
        df = pd.DataFrame({
            'Beneficiario': ['PEDRO'], 'Pension_UF': ['5,00'], 'Pension_Bruta': [175000],
            'Dscto_Salud_7%': [12250], 'Dscto_Comision': [0], 'Pension_Liquida': [162750]
        })
        
        item = {
            'titulo': 'Retiro Programado', 'tipo': 'RP_SOBREVIVENCIA', 'tabla': df
        }
        
        pdf = PDFReportSobrevivencia(orientation='L', unit='mm', format='A4')
        pdf.set_header_data(header_data, beneficiarios)
        pdf.add_page()
        pdf.print_header_data_sobrevivencia()
        pdf.print_table_sobrevivencia(item['titulo'], item['tabla'], item['tipo'])
        
        # This is the critical part
        pdf_output = pdf.output()
        pdf_bytes = bytes(pdf_output)
        
        print(f"SUCCESS: Generated {len(pdf_bytes)} bytes for Sobrevivencia report.")

    except Exception as e:
        print(f"FAILED Sobrevivencia: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vejez_report()
    test_sobrevivencia_report()
