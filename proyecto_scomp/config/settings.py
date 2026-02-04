
# === PROMPT UNIVERSAL ===
PROMPT_EXTRACCION = """
Eres un analista previsional experto en leer SCOMPs chilenos. Tu trabajo es leer el texto
extraído de un SCOMP y devolver un objeto JSON estructurado.

REGLAS IMPORTANTES:
1. Responde SÓLO con el objeto JSON. NADA MÁS.
2. Si un dato no se encuentra, usa `null` (para string) o `0` (para números).
3. Los valores en pesos deben ser NÚMEROS (ej: 1775219), no strings.

INSTRUCCIONES DE EXTRACCIÓN:

1.  **HEADER**: Extrae siempre estos datos.
    * `nombre`: El "Datos del afiliado" o "Datos del Consultante".
    * `rut`: El RUT del afiliado o consultante.
    * `tipo_pension`: El tipo de pensión en la portada (ej. "PENSIÓN DE VEJEZ", "PENSIÓN DE SOBREVIVENCIA").
    * `n_scomp`: El "Código consulta".
    * `saldo_uf`: El valor que sigue a "EL SALDO DESTINADO A PENSIÓN ES:".
    * `valor_uf_str`: El valor en pesos de "Valor UF a fecha emisión:".
    * `valor_uf_float`: El valor numérico de la UF.
    * `afp_origen`: El nombre de la AFP del afiliado/causante.

2.  **BENEFICIARIOS (SÓLO SI ES SOBREVIVENCIA)**:
    * Si `tipo_pension` es "PENSIÓN DE SOBREVIVENCIA", busca "Información Beneficiarios".
    * Extrae una lista de beneficiarios con `nombre`, `rut` y `parentesco`.
    * Ej: `[{ "nombre": "SOTO ISLA DORILA", "rut": "11.090.315-4", "parentesco": "Cónyuge con hijos con derecho a pensión"}, ...]`
    * Si no es Sobrevivencia, devuelve `[]`.

3.  **PENSION_REFERENCIA**:
    * Busca "PENSIÓN DE REFERENCIA GARANTIZADA POR LEY:".
    * **Si es Vejez/Invalidez**: Extrae la tabla simple (Compañía, UF, $). Ej: `[["CONSORCIO VIDA", "42,09", 1579348]]`.
    * **Si es Sobrevivencia**: La tabla es diferente. Extrae `Compania` y una lista de pensiones por beneficiario.
    * Ej: `[{ "compania": "CONSORCIO VIDA", "ofertas_beneficiarios": [["13,82", 503970], ["4,15", 151337]]}, ...]`
    * Si no existe, devuelve `[]`.

4.  **RETIRO_PROGRAMADO**:
    * Busca "MONTO DE PENSIÓN MENSUAL DURANTE EL PRIMER AÑO".
    * Encuentra la columna de la AFP de origen (`header.afp_origen`).
    * Busca la nota (a) para extraer el `comision_pct`.
    * **Si es Vejez/Invalidez**:
        * Busca la fila "Pensión mensual (UF) (a)" para `pension_uf`.
        * Busca la fila "Pensión mensual ($)" para `pension_bruta`.
        * Busca "EXCEDENTE DE LIBRE DISPOSICIÓN" y extrae `eld_oferta` (con monto_uf, monto_pesos, pension_resultante_uf, pension_resultante_pesos).
    * **Si es Sobrevivencia**:
        * Busca la fila "Pensión mensual total" (UF y $) y guárdala como `pension_total_uf` y `pension_total_pesos`.
        * Extrae CADA fila de beneficiario (Nombre, UF, $) de la columna de la AFP de origen. Guárdalo en `pensiones_beneficiarios`.
        * Ej: `{"pension_total_uf": "21,06", "pension_total_pesos": 767988, "comision_pct": 1.25, "pensiones_beneficiarios": [["SOTO ISLA DORILA", "16,20", 590760], ... ]}`
    * Si no existe, devuelve un objeto vacío {}.

5.  **RENTAS_VITALICIAS (INMEDIATAS)**:
    * Busca títulos que comiencen con "PENSIÓN MENSUAL EN RENTA VITALICIA INMEDIATA..." que sean "SIN RETIRO DE EXCEDENTE".
    * Para CADA modalidad (Simple, Aumento, Garantizada):
        * Extrae `titulo` (el título largo original), `porcentaje_aumento`, `meses_aumento`, `meses_garantizados`.
    * **Si es Vejez/Invalidez**:
        * Extrae la tabla de ofertas (Compañía, Pensión UF, Pensión $ como número).
        * Busca la tabla "CON RETIRO DE EXCEDENTE MÁXIMO" asociada y extrae la mejor oferta en `eld_info`.
    * **Si es Sobrevivencia**:
        * Extrae la tabla `Compania de Seguros` y las pensiones por `BENEF. 1 UF`, `BENEF. 1 $`, `BENEF. 2 UF`, `BENEF. 2 $`, ... y `Pensión mensual total $`.
        * Estructura: `[{ "compania": "CN LIFE", "ofertas_beneficiarios": [["13,96", 509075], ["4,19", 152795]], "pension_total_pesos": 661870}, ...]`
    * Devuelve una lista de objetos, uno por cada modalidad.

6.  **RENTA_TEMPORAL_RV_DIFERIDA**:
    * Busca "RENTA TEMPORAL CON RENTA VITALICIA DIFERIDA".
    * Extrae `titulo` (el título largo original), `periodo_diferido_meses` y `factor_renta_temporal`.
    * Busca la tabla "PENSIÓN MENSUAL EN RENTA VITALICIA DIFERIDA..." (SIN RETIRO DE EXCEDENTE).
    * Extrae `meses_garantizados`.
    * **Si es Vejez/Invalidez**: Extrae la tabla (Compañía, Pensión UF, Pensión $) en `ofertas_rvd`.
    * **Si es Sobrevivencia**: Extrae la tabla por beneficiarios (BENEF. 1, etc.) en `ofertas_rvd` (misma estructura que RENTAS_VITALICIAS Sobrevivencia).
    * Extrae `eld_info` si existe.
    * Devuelve una lista de objetos, uno por cada modalidad.

TEXTO DEL SCOMP:
{TEXTO_PDF}

FORMATO JSON DE SALIDA (EJEMPLO):
{
  "header": { "nombre": "JUAN PEREZ", "rut": "12.345.678-9" },
  "beneficiarios": [
    { "nombre": "SOTO ISLA DORILA", "parentesco": "Cónyuge con hijos con derecho a pensión" }
  ],
  "pension_referencia": [ 
    { "compania": "CONSORCIO VIDA", "ofertas_beneficiarios": [["13,82", 503970], ["4,15", 151337]] }
  ],
  "retiro_programado": {
    "pension_total_uf": "21,06", 
    "pension_total_pesos": 767988, 
    "comision_pct": 1.25, 
    "pensiones_beneficiarios": [["SOTO ISLA DORILA", "16,20", 590760]]
  },
  "rentas_vitalicias": [
    {
      "titulo": "Renta Vitalicia Inmediata Simple",
      "porcentaje_aumento": 0,
      "meses_aumento": 0,
      "meses_garantizados": 0,
      "ofertas": [ 
        { "compania": "CN LIFE", "ofertas_beneficiarios": [["13,96", 509075], ["4,19", 152795]], "pension_total_pesos": 661870 }
      ],
      "eld_info": null
    }
  ],
  "renta_temporal_rv_diferida": []
}
"""

# === Diccionario de porcentajes ===
PORCENTAJES_SOBREVIVENCIA = {
    "Cónyuge con hijos con derecho a pensión": 0.50,
    "Cónyuge sin hijos con derecho a pensión": 0.60,
    "Hijo de cónyuge con derecho a pensión": 0.15,
    "Hijo": 0.15,
    "Madre o Padre de hijos de filiación no matrimonial": 0.30, 
}

# Configuración de PGU y Bonos por defecto
DEFAULT_PGU_AMOUNT = 231732
