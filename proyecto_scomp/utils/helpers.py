
def clean_number(s):
    """
    Convierte de forma robusta un string, int o float a un float.
    """
    if isinstance(s, (int, float)):
        return float(s)
    try:
        cleaned_s = str(s).replace('$', '').replace('.', '').replace(',', '.').strip()
        return float(cleaned_s)
    except (ValueError, AttributeError, TypeError):
        return 0.0

def get_sort_key_vejez(item):
    """
    Asigna una clave de ordenamiento para SCOMP de Vejez/Invalidez.
    """
    tipo = item.get('tipo')
    aumento = item.get('meses_aumento', 0)
    garantizado = item.get('meses_garantizados', 0)
    diferido = item.get('periodo_diferido_meses', 0)

    # 1. Retiro Programado
    if tipo == 'RP':
        return (1, 0, 0)
    # 2. Pensión de Referencia
    if tipo == 'REF':
        return (2, 0, 0)
    
    # RV Inmediata
    if tipo == 'RV':
        if garantizado > 0:
            # 4. RV Inmediata con Periodo Garantizado
            return (4, -garantizado, 0)
        else:
            # 3. RV Inmediata Simple
            return (3, 0, 0)
    
    # RV Inmediata con Aumento
    if tipo == 'RV_Aumentada':
        if garantizado > 0:
            # 6. RV Inmediata con Aumento y Garantizado
            return (6, -aumento, -garantizado)
        else:
            # 5. RV Inmediata con Aumento (Simple)
            return (5, -aumento, 0)

    # Renta Temporal
    if tipo == 'RT':
         if garantizado > 0:
            # 8. Renta Temporal con RV Diferida (Garantizado)
             return (8, -diferido, -garantizado)
         else:
            # 7. Renta Temporal con RV Diferida (Simple)
             return (7, -diferido, 0)
    
    return (100, 0, 0) # Fallback

def get_sort_key_sobrevivencia(item):
    """
    Asigna una clave de ordenamiento para SCOMP de Sobrevivencia.
    """
    tipo = item.get('tipo')
    garantizado = item.get('meses_garantizados', 0)
    
    if tipo == 'RP_SOBREVIVENCIA':
        return (1, 0)
    if tipo == 'REF_SOBREVIVENCIA':
        return (2, 0)
    if tipo == 'RV_SOBREVIVENCIA':
        if garantizado > 0:
            return (4, -garantizado) # Ordenar por garantizado descendente
        else:
            return (3, 0) # Simple
    if tipo == 'RT_SOBREVIVENCIA':
        # (Lógica similar si añadimos RT/RVD para sobrevivencia)
        return (5, 0)
    
    return (100, 0) # Fallback
