import pdfplumber
import io

def extract_text_from_pdf(pdf_file):
    """
    Extrae el texto completo de un archivo PDF usando pdfplumber.
    Concatenas las páginas con un separador.
    """
    full_text = ""
    try:
        # Asegurarse de leer desde el principio si es un objeto BytesIO reutilizado
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
            
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2)
                if text:
                    full_text += f"\n\n--- PÁGINA {page.page_number} ---\n\n{text}"
        return full_text
    except Exception as e:
        print(f"Error al leer PDF: {e}")
        return None
