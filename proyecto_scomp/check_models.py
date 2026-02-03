import google.generativeai as genai
import os

# Pide la clave de API en el terminal
api_key = input("Pega tu Google AI API Key aquí y presiona Enter: ")

try:
    genai.configure(api_key=api_key)
    
    print("\n--- Buscando modelos disponibles... ---")
    
    model_names = []
    for m in genai.list_models():
        # Queremos los modelos que pueden "generateContent"
        if 'generateContent' in m.supported_generation_methods:
            model_names.append(m.name)
    
    if not model_names:
        print("No se encontraron modelos compatibles con 'generateContent'.")
        print("Asegúrate de que la clave sea correcta y la facturación esté activa.")
    else:
        print("\n¡Éxito! Copia UNO de los siguientes nombres (exactamente como aparece)")
        print("y pégalo en la línea 167 de tu app.py:\n")
        
        # Extrae el nombre limpio, ej. 'gemini-1.0-pro' de 'models/gemini-1.0-pro'
        for name in model_names:
            clean_name = name.replace("models/", "")
            print(f"'{clean_name}'") # Imprime 'gemini-1.0-pro'

except Exception as e:
    print(f"\nError al conectar con la API: {e}")