import pandas as pd
from utils.helpers import clean_number
from config.settings import PORCENTAJES_SOBREVIVENCIA

def process_data_vejez(raw_data, header_data, include_pgu=True, pgu_amount=0, include_bono=True, bono_uf=0):
    """
    Procesa los datos para SCOMP de Vejez/Invalidez.
    Retorna una lista de tablas procesadas.
    """
    tables_data = []
    
    # Adaptar Retiro Programado
    rp = raw_data.get("retiro_programado", {})
    if rp and rp.get("pension_bruta") is not None:
        afp_origen = header_data.get('afp_origen', 'AFP No Encontrada')
        
        rp_df_final = pd.DataFrame({
            'Modalidad': [afp_origen],
            'Pension_UF': [rp.get("pension_uf", "0,00")],
            'Pension_Bruta': [clean_number(rp.get("pension_bruta", 0))], 
            'Comision_Pct': [rp.get("comision_pct", 0) / 100.0] 
        })
        rp_titulo = f"Retiro Programado ({afp_origen})"
        rp_eld_offer = rp.get("eld_oferta") 
        tables_data.append({
            'titulo': rp_titulo, 
            'tipo': 'RP', 
            'tabla': rp_df_final,
            'eld_info': rp_eld_offer 
        })

    # Adaptar Pensión de Referencia
    ref_list = raw_data.get("pension_referencia", [])
    if ref_list and isinstance(ref_list[0], list): 
        df_ref = pd.DataFrame(ref_list, columns=['Compania', 'Pension_UF', 'Pension_Bruta_str']) 
        if not df_ref.empty:
            df_ref['Pension_Bruta'] = df_ref['Pension_Bruta_str'].apply(clean_number)
            df_ref = df_ref.drop(columns=['Pension_Bruta_str'])
            tables_data.append({
                'titulo': "Pensión de Referencia (Garantizada por Ley)", 
                'tipo': 'REF', 
                'tabla': df_ref,
                'eld_info': None
            })

    # Adaptar Rentas Vitalicias
    rv_list = raw_data.get("rentas_vitalicias", [])
    for modalidad in rv_list:
        ofertas = modalidad.get("ofertas", [])
        if ofertas and isinstance(ofertas[0], list):
            df = pd.DataFrame(ofertas, columns=['Compania', 'Pension_UF', 'Pension_Bruta_str'])
            if not df.empty:
                df['Pension_Bruta'] = df['Pension_Bruta_str'].apply(clean_number)
                df = df.drop(columns=['Pension_Bruta_str'])
                
                # === LÓGICA DE TÍTULO RESUMIDO ===
                base_title = "Renta Vitalicia Inmediata"
                parts = [base_title]
                aumento_pct = modalidad.get("porcentaje_aumento", 0)
                aumento_meses = modalidad.get("meses_aumento", 0)
                garant_meses = modalidad.get("meses_garantizados", 0)

                if aumento_pct > 0 and aumento_meses > 0:
                    parts.append(f"Aumento {aumento_pct}% {aumento_meses}m")
                if garant_meses > 0:
                    parts.append(f"Garantizado {garant_meses}m")
                if len(parts) == 1:
                    parts.append("Simple")
                
                new_title = " / ".join(parts)
                # === FIN LÓGICA TÍTULO ===

                tables_data.append({
                    'titulo': new_title, 
                    'tipo': 'RV', 
                    'tabla': df,
                    'porcentaje_aumento': aumento_pct,
                    'meses_aumento': aumento_meses,
                    'meses_garantizados': garant_meses,
                    'eld_info': modalidad.get("eld_info") 
                })
    
    # Adaptar Renta Temporal / RVD
    rtrvd_list = raw_data.get("renta_temporal_rv_diferida", [])
    for modalidad in rtrvd_list:
        ofertas_rvd = modalidad.get("ofertas_rvd", [])
        if ofertas_rvd and isinstance(ofertas_rvd[0], list):
            df = pd.DataFrame(ofertas_rvd, columns=['Compania', 'Pension_UF', 'Pension_Bruta_str'])
            if not df.empty:
                df['Pension_Bruta'] = df['Pension_Bruta_str'].apply(clean_number)
                df = df.drop(columns=['Pension_Bruta_str'])
                
                # === LÓGICA DE TÍTULO RESUMIDO ===
                base_title = "Renta Temporal"
                parts = [base_title]
                diferido_meses = modalidad.get("periodo_diferido_meses", 0)
                garant_meses = modalidad.get("meses_garantizados", 0)

                parts.append("RVD") 
                
                if garant_meses > 0:
                    parts.append(f"Garantizado {garant_meses}m")
                else:
                    parts.append("Simple")
                
                if diferido_meses > 0:
                    parts.append(f"({diferido_meses}m)")
                
                new_title = " / ".join(parts)
                # === FIN LÓGICA TÍTULO ===
                
                tables_data.append({
                    'titulo': new_title,
                    'tipo': 'RT_RVD',
                    'tabla': df,
                    'periodo_diferido_meses': diferido_meses,
                    'factor_renta_temporal': modalidad.get("factor_renta_temporal", 1.0),
                    'meses_garantizados': garant_meses,
                    'eld_info': modalidad.get("eld_info") 
                })

    # --- INICIO LÓGICA DE PROCESAMIENTO (VEJEZ) ---
    valor_pgu = pgu_amount if include_pgu else 0
    valor_bono = (bono_uf * header_data.get('valor_uf_float', 0)) if include_bono else 0
    
    col_title_parts = ["Pensión"]
    if include_pgu: col_title_parts.append("PGU")
    if include_bono: col_title_parts.append("Bono")
    col_title = " + ".join(col_title_parts)
    col_title_pdf = "Pensión + Bono" 

    afp_commission_pct = 0.0
    rp_item = next((item for item in tables_data if item.get('tipo') == 'RP'), None)
    if rp_item and not rp_item['tabla'].empty:
        if 'Comision_Pct' in rp_item['tabla'].columns:
            afp_commission_pct = rp_item['tabla']['Comision_Pct'].iloc[0]

    processed_tables = []
    
    for item in tables_data:
        df = item['tabla'].copy()
        
        if df.empty or 'Pension_Bruta' not in df.columns:
            continue
            
        if item['tipo'] == 'RV' or item['tipo'] == 'REF' or item['tipo'] == 'RT_RVD':
             df = df.sort_values(by="Pension_Bruta", ascending=False).head(4)
        
        porcentaje_aumento = item.get('porcentaje_aumento', 0)
        
        if item['tipo'] == 'RT_RVD':
            meses = item.get('periodo_diferido_meses', 0)
            factor = item.get('factor_renta_temporal', 1.0)
            
            df_base = df.copy()
            df_base["Descuento_Salud_7%"] = (df_base["Pension_Bruta"] * 0.07).round(0)
            df_base["Pension_Liquida"] = df_base["Pension_Bruta"] - df_base["Descuento_Salud_7%"]
            df_base[col_title_pdf] = (df_base["Pension_Bruta"] + valor_pgu + valor_bono).round(0)

            df_temporal = df.copy()
            df_temporal['Pension_UF_float'] = df_temporal['Pension_UF'].apply(clean_number)
            df_temporal["Pension_Bruta"] = (df_temporal["Pension_Bruta"] * factor).round(0)
            df_temporal["Pension_UF"] = (df_temporal["Pension_UF_float"] * factor).apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_temporal["Descuento_Salud_7%"] = (df_temporal["Pension_Bruta"] * 0.07).round(0)
            df_temporal["Comision_Pct"] = afp_commission_pct
            df_temporal["Descuento_Comision"] = (df_temporal["Pension_Bruta"] * df_temporal["Comision_Pct"]).round(0)
            df_temporal["Pension_Liquida"] = df_temporal["Pension_Bruta"] - df_temporal["Descuento_Salud_7%"] - df_temporal["Descuento_Comision"]
            df_temporal[col_title_pdf] = (df_temporal["Pension_Bruta"] + valor_pgu + valor_bono).round(0)
            
            afp_origen = header_data.get('afp_origen', 'AFP')
            titulo_temporal = f"{item['titulo']} - Renta Temporal (Mes 1-{meses}) / {afp_origen}"
            titulo_base = f"{item['titulo']} - Renta Vitalicia Diferida (desde mes {meses + 1})"
            
            processed_tables.append({
                'titulo': titulo_temporal, 
                'tipo': 'RT', 
                'tabla': df_temporal.drop(columns=['Pension_UF_float']),
                'col_title_display': col_title,
                'col_title_pdf': col_title_pdf,
                'periodo_diferido_meses': meses,
                'meses_garantizados': item.get('meses_garantizados', 0),
                'eld_info': item.get('eld_info')
            })

            processed_tables.append({
                'titulo': titulo_base, 
                'tipo': 'RVD', 
                'tabla': df_base, 
                'col_title_display': col_title,
                'col_title_pdf': col_title_pdf,
                'periodo_diferido_meses': meses,
                'meses_garantizados': item.get('meses_garantizados', 0),
                'eld_info': None,
                'linked_to_title': titulo_temporal
            })

        elif item['tipo'] == 'RV' and porcentaje_aumento > 0:
            df_base = df.copy()
            df_base["Descuento_Salud_7%"] = (df_base["Pension_Bruta"] * 0.07).round(0)
            df_base["Pension_Liquida"] = df_base["Pension_Bruta"] - df_base["Descuento_Salud_7%"]
            df_base[col_title_pdf] = (df_base["Pension_Bruta"] + valor_pgu + valor_bono).round(0)
            
            df_aumentada = df.copy()
            factor_aumento = (1 + porcentaje_aumento / 100.0)
            df_aumentada['Pension_UF_float'] = df_aumentada['Pension_UF'].apply(clean_number)
            df_aumentada["Pension_Bruta"] = (df_aumentada["Pension_Bruta"] * factor_aumento).round(0)
            df_aumentada["Pension_UF"] = (df_aumentada["Pension_UF_float"] * factor_aumento).apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_aumentada["Descuento_Salud_7%"] = (df_aumentada["Pension_Bruta"] * 0.07).round(0)
            df_aumentada["Pension_Liquida"] = df_aumentada["Pension_Bruta"] - df_aumentada["Descuento_Salud_7%"]
            df_aumentada[col_title_pdf] = (df_aumentada["Pension_Bruta"] + valor_pgu + valor_bono).round(0)

            processed_tables.append({
                'titulo': item['titulo'], 
                'tipo': 'RV_Aumentada', 
                'tabla': df_aumentada.drop(columns=['Pension_UF_float']),
                'col_title_display': col_title,
                'col_title_pdf': col_title_pdf,
                'meses_aumento': item.get('meses_aumento', 0),
                'meses_garantizados': item.get('meses_garantizados', 0),
                'eld_info': item.get('eld_info') 
            })
            
            meses_aumento = item.get('meses_aumento', 0)
            titulo_base = f"Pensión Base (desde mes {meses_aumento + 1})"
            
            processed_tables.append({
                'titulo': titulo_base, 
                'tipo': 'RV_Base', 
                'tabla': df_base, 
                'col_title_display': col_title,
                'col_title_pdf': col_title_pdf,
                'meses_aumento': item.get('meses_aumento', 0),
                'meses_garantizados': item.get('meses_garantizados', 0),
                'eld_info': None,
                'linked_to_title': item['titulo'] 
            })

        else:
            df["Descuento_Salud_7%"] = (df["Pension_Bruta"] * 0.07).round(0)
            
            if item['tipo'] == 'RP':
                df["Comision_Pct"] = afp_commission_pct
                df["Descuento_Comision"] = (df["Pension_Bruta"] * df["Comision_Pct"]).round(0)
                df["Pension_Liquida"] = df["Pension_Bruta"] - df["Descuento_Salud_7%"] - df["Descuento_Comision"]
            else: 
                df["Pension_Liquida"] = df["Pension_Bruta"] - df["Descuento_Salud_7%"]


            df[col_title_pdf] = (df["Pension_Bruta"] + valor_pgu + valor_bono).round(0)
            
            processed_tables.append({
                'titulo': item['titulo'], 
                'tipo': item['tipo'], 
                'tabla': df, 
                'col_title_display': col_title,
                'col_title_pdf': col_title_pdf,
                'meses_garantizados': item.get('meses_garantizados', 0), 
                'eld_info': item.get('eld_info') 
            })

    return processed_tables

def process_data_sobrevivencia(raw_data, header_data):
    """
    Procesa los datos para SCOMP de Sobrevivencia.
    Retorna (processed_tables, beneficiarios_ordenados, warnings).
    """
    processed_tables = []
    warnings = []
    
    beneficiarios_raw = raw_data.get("beneficiarios", [])
    if not beneficiarios_raw:
        warnings.append("No se encontraron beneficiarios en el SCOMP.")
        return [], [], warnings

    # --- 1. Ordenar beneficiarios ---
    beneficiarios_ordenados = []
    benef_hijos = []
    
    for b in beneficiarios_raw:
        parentesco = b.get("parentesco", "").lower()
        if "cónyuge" in parentesco or "conviviente" in parentesco or "madre" in parentesco or "padre" in parentesco:
            beneficiarios_ordenados.append(b) 
        else:
            benef_hijos.append(b) 
    
    beneficiarios_ordenados.extend(benef_hijos) 
    header_data["beneficiarios_ordenados"] = beneficiarios_ordenados 
    
    # --- 2. Calcular Pensión Base 100% ---
    pension_base_100_uf = 0.0
    rp_data = raw_data.get("retiro_programado", {})
    afp_commission_pct = rp_data.get("comision_pct", 0) / 100.0
    
    if rp_data and "pensiones_beneficiarios" in rp_data:
        for benef_rp in rp_data["pensiones_beneficiarios"]:
            nombre_rp = benef_rp[0]
            uf_rp = clean_number(benef_rp[1])
            parentesco = ""
            for b in beneficiarios_ordenados:
                if nombre_rp.strip().upper() in b["nombre"].strip().upper():
                    parentesco = b["parentesco"]
                    break
            
            porcentaje = PORCENTAJES_SOBREVIVENCIA.get(parentesco, 0)
            if porcentaje > 0:
                pension_base_100_uf = uf_rp / porcentaje
                header_data["Pension_Base_100_UF"] = pension_base_100_uf
                break
    
    if pension_base_100_uf == 0:
        warnings.append("No se pudo calcular la Pensión Base 100% desde Retiro Programado.")

    # --- 3. Procesar Tabla de Retiro Programado ---
    if rp_data and "pensiones_beneficiarios" in rp_data:
        rp_rows = []
        for benef_rp in rp_data["pensiones_beneficiarios"]:
            nombre = benef_rp[0]
            uf = clean_number(benef_rp[1])
            bruta = clean_number(benef_rp[2])
            
            salud = round(bruta * 0.07)
            comision = round(bruta * afp_commission_pct)
            
            liquida = bruta - salud - comision
            rp_rows.append([nombre, f"{uf:,.2f}", bruta, salud, comision, liquida])

        df_rp = pd.DataFrame(rp_rows, columns=["Beneficiario", "Pension_UF", "Pension_Bruta", "Dscto_Salud_7%", "Dscto_Comision", "Pension_Liquida"])
        
        total_bruto = df_rp["Pension_Bruta"].sum()
        total_salud = df_rp["Dscto_Salud_7%"].sum()
        total_comision = df_rp["Dscto_Comision"].sum()
        total_liquido = df_rp["Pension_Liquida"].sum()
        total_uf = clean_number(rp_data.get("pension_total_uf", 0))
        
        df_rp.loc['Total'] = ["Pensión mensual total", f"{total_uf:,.2f}", total_bruto, total_salud, total_comision, total_liquido]
        
        processed_tables.append({
            'titulo': f"Retiro Programado ({header_data.get('afp_origen', 'AFP')})",
            'tipo': 'RP_SOBREVIVENCIA',
            'tabla': df_rp,
            'meses_garantizados': 0
        })

    # --- 4. Generar nombres de columna para RV ---
    cols_base = ["Compañía"]
    for i in range(len(beneficiarios_ordenados)):
        cols_base.extend([f"Benef. {i+1} UF", f"Benef. {i+1} $"])
    cols_rv = cols_base + ["Total Bruto", "Total Líquido"]
    
    # --- 5. Procesar Tablas de Renta Vitalicia ---
    rv_list = raw_data.get("rentas_vitalicias", [])
    for modalidad in rv_list:
        ofertas = modalidad.get("ofertas", [])
        if not ofertas or not isinstance(ofertas[0], dict):
            continue 

        # === LÓGICA DE TÍTULO RESUMIDO (Sobrevivencia) ===
        base_title = "Renta Vitalicia Inmediata"
        parts = [base_title]
        garant_meses = modalidad.get("meses_garantizados", 0)
        
        if garant_meses > 0:
            parts.append(f"Garantizado {garant_meses}m")
        else:
            parts.append("Simple")
        
        new_title = " / ".join(parts)
        # === FIN LÓGICA TÍTULO ===

        rv_rows = []
        for oferta in ofertas:
            row = [oferta["compania"]]
            total_bruto = clean_number(oferta.get("pension_total_pesos", 0))
            
            for benef_oferta in oferta.get("ofertas_beneficiarios", []):
                row.append(benef_oferta[0]) # UF (string)
                row.append(clean_number(benef_oferta[1])) # Pesos (num)
            
            num_esperado = len(cols_rv)
            num_actual = len(row) + 2 # +2 for Total Bruto/Liquido
            
            if num_actual > num_esperado:
                row = row[:num_esperado-2]
            elif num_actual < num_esperado:
                row.extend([None] * (num_esperado - num_actual))
            
            row.append(total_bruto)
            row.append(round(total_bruto * 0.93)) # Total Líquido (Bruto - 7% Salud)
            rv_rows.append(row)
        
        if rv_rows:
            df_rv = pd.DataFrame(rv_rows, columns=cols_rv).head(4) 
            processed_tables.append({
                'titulo': new_title, 
                'tipo': 'RV_SOBREVIVENCIA',
                'tabla': df_rv,
                'meses_garantizados': garant_meses
            })

    return processed_tables, beneficiarios_ordenados, warnings
