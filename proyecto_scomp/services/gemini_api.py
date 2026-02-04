import google.generativeai as genai
import json
from config.settings import PROMPT_EXTRACCION

def analyze_scomp_with_gemini(text, api_key):
    """
    Envía el texto extraído del SCOMP a la API de Google Gemini para obtener un JSON estructurado.
    """
    if not api_key:
        raise ValueError("API Key no proporcionada.")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro-latest') # O el modelo más reciente/estable
        
        prompt_completo = PROMPT_EXTRACCION.replace("{TEXTO_PDF}", text)
        
        generation_config = {
            "temperature": 0.0,
            "response_mime_type": "application/json",
        }
        
        request_options = {"timeout": 300}
        
        response = model.generate_content(
            prompt_completo, 
            generation_config=generation_config,
            request_options=request_options
        )
        
        try:
            json_response = json.loads(response.text)
            return json_response
        except json.JSONDecodeError:
            # En caso de error, podríamos retornar el texto crudo para debug o lanzar error
            raise ValueError(f"La IA no devolvió un JSON válido. Respuesta: {response.text[:200]}...")
            
    except Exception as e:
        raise e
