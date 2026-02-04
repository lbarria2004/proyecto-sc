import streamlit as st
import pandas as pd
import re
import io
import os

# Importar Módulos Refactorizados
from config.settings import DEFAULT_PGU_AMOUNT
from services.pdf_parser import extract_text_from_pdf
from services.gemini_api import analyze_scomp_with_gemini
from services.calculations import process_data_vejez, process_data_sobrevivencia
from services.report_gen import PDFReportVejez, PDFReportSobrevivencia, create_formatted_excel_report
from utils.helpers import clean_number, get_sort_key_vejez, get_sort_key_sobrevivencia

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Generador SCOMP Pro", page_icon="🚀")

# --- CARGAR CSS ---
def load_css():
    css_path = os.path.join("assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- BARRA LATERAL ---
st.sidebar.title("🛠️ Configuración")

# API Key
api_key_sidebar = st.sidebar.text_input(
    "Google AI API Key", 
    type="password",
    key="api_key_from_user",
    help="Tu clave API de Google Gemini."
)
st.sidebar.markdown("[Obtener API Key](https://aistudio.google.com/app/apikey)")
st.sidebar.divider()

# Opciones Generales
st.sidebar.subheader("Parámetros (Vejez/Invalidez)")
include_pgu = st.sidebar.checkbox("Incluir PGU", value=True)
include_bono = st.sidebar.checkbox("Incluir Bono Adicional", value=True)
bono_uf = st.sidebar.number_input(
    "Monto Bono (en UF)", 
    min_value=0.0, 
    max_value=5.0, 
    value=2.5, 
    step=0.1, 
    disabled=not include_bono
)

# --- HEADER PRINCIPAL ---
st.title("🚀 Generador de Reporte Previsional")
st.markdown("### Transforma tu SCOMP en un reporte profesional en segundos.")

uploaded_file = st.file_uploader("Sube el archivo PDF del SCOMP", type=["pdf"])

# --- LÓGICA PRINCIPAL ---
if uploaded_file is not None:
    
    # Gestión de API Key
    try:
        api_key_secrets = st.secrets["api_key"]
    except Exception:
        api_key_secrets = None
    
    final_api_key = api_key_secrets if api_key_secrets else st.session_state.get("api_key_from_user", "")
    
    if not final_api_key:
        st.error("⚠️ Por favor, introduce tu API Key para continuar.")
        st.stop()

    # Estado de la sesión para guardar datos procesados
    if "scomp_data" not in st.session_state or st.session_state.get("current_file") != uploaded_file.name:
        st.session_state.scomp_data = None
        st.session_state.current_file = uploaded_file.name

    raw_data = st.session_state.scomp_data

    # --- FASE 1: ANÁLISIS ---
    if raw_data is None:
        with st.status("🔍 Analizando documento...", expanded=True) as status:
            st.write("Extrayendo texto del PDF...")
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            if not pdf_text:
                status.update(label="Error en lectura de PDF", state="error")
                st.stop()
            
            st.write("Consultando a la Inteligencia Artificial (Gemini)...")
            try:
                raw_data = analyze_scomp_with_gemini(pdf_text, final_api_key)
                st.session_state.scomp_data = raw_data # Guardar en cache de sesión
                status.update(label="¡Análisis completado!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Error en el análisis", state="error")
                st.error(f"Ocurrió un error: {e}")
                st.stop()
    
    # --- FASE 2: PROCESAMIENTO Y VISUALIZACIÓN ---
    if raw_data:
        header_data = raw_data.get("header", {})
        tipo_pension = header_data.get("tipo_pension", "").upper()
        
        # Tarjetas de Resumen del Cliente
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Afiliado", header_data.get("nombre", "N/A"))
        col2.metric("RUT", header_data.get("rut", "N/A"))
        col3.metric("Saldo Acumulado", f"{header_data.get('saldo_uf', '0')} UF")
        col4.metric("Tipo Pensión", tipo_pension)

        # === SOBREVIVENCIA ===
        if "SOBREVIVENCIA" in tipo_pension:
            processed_tables, beneficiarios, warnings = process_data_sobrevivencia(raw_data, header_data)
            
            if warnings:
                for w in warnings: st.warning(w)

            st.subheader("👥 Beneficiarios")
            if beneficiarios:
                cols = st.columns(len(beneficiarios)) if len(beneficiarios) < 4 else st.columns(3)
                for i, b in enumerate(beneficiarios):
                    with cols[i % 3]:
                        st.info(f"**{b['nombre']}**\n\n{b['parentesco']}")
            
            processed_tables.sort(key=get_sort_key_sobrevivencia)
            
            st.subheader("📊 Tabla de Ofertas")
            for item in processed_tables:
                with st.expander(f"{item['titulo']}", expanded=True):
                    st.dataframe(item['tabla'], use_container_width=True, hide_index=True)
            
            # Botones de descarga
            st.divider()
            st.subheader("📥 Descargas")
            
            pdf = PDFReportSobrevivencia(orientation='L', unit='mm', format='A4')
            pdf.set_header_data(header_data, beneficiarios)
            pdf.add_page()
            pdf.print_header_data_sobrevivencia()
            for item in processed_tables:
                 if not item['tabla'].empty:
                    pdf.print_table_sobrevivencia(item['titulo'], item['tabla'], item['tipo'])
            
            pdf_output = pdf.output()
            pdf_bytes = bytes(pdf_output)
            excel_bytes = create_formatted_excel_report(header_data, processed_tables, beneficiarios)
            
            c1, c2 = st.columns(2)
            c1.download_button("📄 Descargar PDF Pro", pdf_bytes, "Resultado_SCOMP_Sobrevivencia.pdf", "application/pdf", use_container_width=True)
            c2.download_button("📊 Descargar Excel", excel_bytes, "Resultado_SCOMP_Sobrevivencia.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        # === VEJEZ / INVALIDEZ ===
        else:
            processed_tables = process_data_vejez(raw_data, header_data, include_pgu, 224004, include_bono, bono_uf)
            
            # Ordenar lógica
            parent_sort_keys = {}
            for item in processed_tables:
                if 'linked_to_title' not in item:
                    key = get_sort_key_vejez(item) + (0,) 
                    item['sort_key'] = key
                    parent_sort_keys[item['titulo']] = key
            for item in processed_tables:
                if 'linked_to_title' in item:
                    parent_key = parent_sort_keys.get(item['linked_to_title'])
                    item['sort_key'] = (parent_key[0], parent_key[1], parent_key[2], 1) if parent_key else (99,0,0,0)
            processed_tables.sort(key=lambda x: x.get('sort_key', (100, 0, 0, 0)))

            # Filtros
            st.sidebar.subheader("Filtros de Modalidad")
            all_titles = [item['titulo'] for item in processed_tables if 'linked_to_title' not in item]
            
            if 'selected_titles' not in st.session_state:
                st.session_state.selected_titles = all_titles
            
            with st.sidebar.form("filter_form"):
                 st.write("Selecciona modalidades:")
                 new_selection = []
                 for t in all_titles:
                     if st.checkbox(t, value=(t in st.session_state.selected_titles)):
                         new_selection.append(t)
                 if st.form_submit_button("Aplicar Filtros"):
                     st.session_state.selected_titles = new_selection
                     st.rerun()

            filtered_tables = [
                item for item in processed_tables 
                if ('linked_to_title' not in item and item['titulo'] in st.session_state.selected_titles) or 
                   ('linked_to_title' in item and item['linked_to_title'] in st.session_state.selected_titles)
            ]

            # Visualización
            st.subheader("📈 Análisis de Ofertas")
            
            # Gráfico de Resumen (Top Ofertas)
            top_offers = []
            for item in filtered_tables:
                if not item['tabla'].empty:
                    col_pension = item['col_title_display']
                    max_val = item['tabla'][col_pension].max()
                    top_offers.append({"Modalidad": item['titulo'], "Monto": max_val})
            
            if top_offers:
                df_chart = pd.DataFrame(top_offers)
                st.bar_chart(df_chart, x="Modalidad", y="Monto", use_container_width=True)

            # Tablas Detalladas
            for item in filtered_tables:
                with st.expander(f"📌 {item['titulo']}", expanded=True):
                    # Preparar dataframe para display (quitar columnas internas)
                    df_display = item['tabla'].copy()
                    if 'Comision_Pct' in df_display.columns: 
                        df_display = df_display.drop(columns=['Comision_Pct'])
                    
                    # Renombrar columna dinámica
                    df_display = df_display.rename(columns={item['col_title_pdf']: item['col_title_display']})
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Info ELD
                    eld = item.get('eld_info')
                    if eld and eld.get("monto_pesos", 0) > 0:
                        st.info(f"💰 Se detectó una oferta de Excedente de Libre Disposición (ELD): **${eld.get('monto_pesos', 0):,.0f}**")

            # Botones de Descarga
            st.divider()
            st.subheader("📥 Descargas")
            
            pdf = PDFReportVejez(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.print_header_data(header_data)
            for item in filtered_tables:
                 if not item['tabla'].empty: 
                    pdf.print_table(item['titulo'], item['tabla'], item['tipo'], item['col_title_pdf'], item.get('eld_info'), header_data.get('valor_uf_float', 0.0))
            
            pdf_output = pdf.output()
            pdf_bytes = bytes(pdf_output)
            excel_bytes = create_formatted_excel_report(header_data, filtered_tables)

            c1, c2 = st.columns(2)
            c1.download_button("📄 Descargar PDF Pro", pdf_bytes, "Resultado_SCOMP_Vejez_Invalidez.pdf", "application/pdf", use_container_width=True)
            c2.download_button("📊 Descargar Excel", excel_bytes, "Resultado_SCOMP_Vejez_Invalidez.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)