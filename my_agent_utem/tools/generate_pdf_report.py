import os
import unicodedata
from fpdf import FPDF
from datetime import datetime
from google.adk.tools import FunctionTool 


def limpiar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto para evitar problemas con caracteres especiales en el PDF.
    Reemplaza caracteres Unicode problemáticos por sus equivalentes ASCII.
    
    Args:
        texto: El texto a limpiar.
        
    Returns:
        str: Texto limpio compatible con la fuente Arial del PDF.
    """
    if not texto:
        return ""
    
    texto = str(texto)
    
    # Diccionario de reemplazos para caracteres problemáticos
    reemplazos = {
        # Guiones y rayas
        '\u2013': '-',  # en dash (–)
        '\u2014': '-',  # em dash (—)
        '\u2015': '-',  # horizontal bar (―)
        '\u2212': '-',  # minus sign (−)
        
        # Comillas tipográficas
        '\u201c': '"',  # left double quotation mark (")
        '\u201d': '"',  # right double quotation mark (")
        '\u2018': "'",  # left single quotation mark (')
        '\u2019': "'",  # right single quotation mark (')
        '\u201a': ',',  # single low-9 quotation mark (‚)
        '\u201e': '"',  # double low-9 quotation mark („)
        '\u00ab': '"',  # left-pointing double angle quotation mark («)
        '\u00bb': '"',  # right-pointing double angle quotation mark (»)
        
        # Puntos suspensivos y otros
        '\u2026': '...',  # horizontal ellipsis (…)
        '\u2022': '*',    # bullet (•)
        '\u2023': '>',    # triangular bullet (‣)
        '\u2043': '-',    # hyphen bullet (⁃)
        
        # Espacios especiales
        '\u00a0': ' ',    # non-breaking space
        '\u2002': ' ',    # en space
        '\u2003': ' ',    # em space
        '\u2009': ' ',    # thin space
        '\u200a': ' ',    # hair space
        '\u200b': '',     # zero-width space
        '\u202f': ' ',    # narrow no-break space
        '\u205f': ' ',    # medium mathematical space
        '\u3000': ' ',    # ideographic space
        
        # Otros caracteres especiales
        '\u00b0': 'o',    # degree sign (°)
        '\u00b7': '*',    # middle dot (·)
        '\u2033': '"',    # double prime (″)
        '\u2032': "'",    # prime (′)
        '\u00d7': 'x',    # multiplication sign (×)
        '\u00f7': '/',    # division sign (÷)
        '\u2192': '->',   # rightwards arrow (→)
        '\u2190': '<-',   # leftwards arrow (←)
        '\u2194': '<->',  # left right arrow (↔)
        '\u25cf': '*',    # black circle (●)
        '\u25cb': 'o',    # white circle (○)
        '\u25a0': '#',    # black square (■)
        '\u25a1': '[]',   # white square (□)
        '\u2713': '[x]',  # check mark (✓)
        '\u2717': '[X]',  # ballot x (✗)
        '\u00ae': '(R)',  # registered sign (®)
        '\u00a9': '(C)',  # copyright sign (©)
        '\u2122': '(TM)', # trade mark sign (™)
    }
    
    # Aplicar reemplazos
    for char_unicode, char_ascii in reemplazos.items():
        texto = texto.replace(char_unicode, char_ascii)
    
    # Normalizar caracteres acentuados (mantener los del español)
    # Solo normalizamos a NFC para combinar caracteres
    texto = unicodedata.normalize('NFC', texto)
    
    # Reemplazar cualquier otro caracter no-ascii problemático
    resultado = []
    for char in texto:
        try:
            # Intentamos codificar en latin-1 (que es lo que soporta Arial)
            char.encode('latin-1')
            resultado.append(char)
        except UnicodeEncodeError:
            # Si no se puede, intentamos descomponer y tomar solo la parte base
            decomposed = unicodedata.normalize('NFD', char)
            base_char = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
            if base_char:
                try:
                    base_char.encode('latin-1')
                    resultado.append(base_char)
                except UnicodeEncodeError:
                    resultado.append('?')
            else:
                resultado.append('?')
    
    return ''.join(resultado)


# ──────────────────────────────────────────────────────────────────────────────
# Colores institucionales UTEM
# ──────────────────────────────────────────────────────────────────────────────
# Azul oscuro para títulos (similar al de la imagen)
AZUL_UTEM_OSCURO = (26, 82, 118)  # #1a5276
# Azul claro para fondos de encabezados de tabla
AZUL_UTEM_CLARO = (212, 230, 241)  # #d4e6f1
# Azul medio para algunos elementos
AZUL_UTEM_MEDIO = (41, 128, 185)  # #2980b9


class ReportePDF(FPDF):
    """Clase personalizada para generar reportes UTEM con formato institucional."""
    
    def __init__(self):
        super().__init__()
        # Obtener la ruta del logo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(current_dir, '..', 'templates', 'UTEM-LOGO.jpg')
    
    def header(self):
        """Encabezado del PDF con logo UTEM y colores institucionales."""
        # Verificar si existe el logo
        if os.path.exists(self.logo_path):
            # Logo UTEM a la izquierda (más grande y mejor posicionado)
            self.image(self.logo_path, 10, 8, 30)  # x, y, ancho (aumentado a 30mm)
        
        # Texto VRAC a la derecha del logo
        self.set_xy(45, 12)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*AZUL_UTEM_OSCURO)  # Azul institucional
        self.cell(0, 6, 'VRAC', 0, 1, 'L')
        
        self.set_xy(45, 19)
        self.set_font('Arial', '', 10)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 5, 'Vicerrectoria Academica', 0, 1, 'L')
        
        # Línea separadora azul (movida más abajo para no cortar el logo)
        self.set_draw_color(*AZUL_UTEM_OSCURO)
        self.set_line_width(0.5)
        self.line(10, 38, 200, 38)  # Línea en y=38 (debajo del logo)
        
        # Resetear color de texto a negro para el contenido
        self.set_text_color(0, 0, 0)
        self.ln(25)  # Más espacio después del header
    
    def footer(self):
        """Pie de página del PDF con estilo institucional."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)  # Gris
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.set_text_color(0, 0, 0)  # Resetear a negro
    
    def seccion_titulo(self, numero, titulo):
        """Genera un título de sección con estilo UTEM."""
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 7, f'{numero}. {titulo}', 0, 1, 'L')
        self.set_text_color(0, 0, 0)
    
    def dimension_titulo(self, titulo):
        """Genera un título de dimensión con fondo azul claro."""
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*AZUL_UTEM_CLARO)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 6, titulo, 1, 1, 'L', True)
        self.set_text_color(0, 0, 0)


def generar_tabla_dimension(pdf, acciones):
    """Genera una tabla de dimensión con manejo correcto de texto largo."""
    if not acciones:
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 5, 'No hay acciones registradas para esta dimension.', 1, 1, 'L')
        return
    
    # Anchos de columnas (total = 190mm aprox)
    col_widths = {
        'accion': 65,      # Reducido un poco
        'fecha': 20,
        'estado': 18,
        'medios': 60,      # Aumentado para más espacio
        'plan': 27         # Aumentado para "Mantener seguimiento"
    }
    line_height = 4  # Altura por línea de texto
    min_row_height = 8  # Altura mínima de fila
    
    # Encabezados con colores institucionales UTEM
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(*AZUL_UTEM_CLARO)  # Fondo azul claro
    pdf.set_text_color(*AZUL_UTEM_OSCURO)  # Texto azul oscuro
    pdf.cell(col_widths['accion'], 6, 'Accion', 1, 0, 'C', True)
    pdf.cell(col_widths['fecha'], 6, 'Fecha', 1, 0, 'C', True)
    pdf.cell(col_widths['estado'], 6, 'Estado', 1, 0, 'C', True)
    pdf.cell(col_widths['medios'], 6, 'Medios Verificacion', 1, 0, 'C', True)
    pdf.cell(col_widths['plan'], 6, 'Plan Mej.', 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)  # Resetear a negro para datos
    
    # Datos
    pdf.set_font('Arial', '', 7)
    
    for accion in acciones:
        texto = limpiar_texto(str(accion.get('texto', 'N/A'))[:500])  # Limitar texto y limpiar
        fecha = limpiar_texto(str(accion.get('fecha', 'N/A'))[:30])
        estado = limpiar_texto(str(accion.get('estado', 'N/A'))[:15])
        medios_list = accion.get('medios', ['N/A'])
        medios = ', '.join(medios_list) if isinstance(medios_list, list) else str(medios_list)
        medios = limpiar_texto(medios[:200])  # Limitar medios y limpiar
        plan_mejora = limpiar_texto(str(accion.get('plan_mejora', 'N/A'))[:25])  # Aumentado límite
        
        # Guardar posición inicial para cálculos
        x_calc = pdf.get_x()
        y_calc = pdf.get_y()
        
        # Calcular altura REAL de cada columna de texto largo usando multi_cell
        # Para Acción
        pdf.set_xy(x_calc, y_calc)
        lines_accion = pdf.multi_cell(col_widths['accion'] - 2, line_height, texto, border=0, split_only=True)
        height_accion = len(lines_accion) * line_height
        
        # Para Medios
        lines_medios = pdf.multi_cell(col_widths['medios'] - 2, line_height, medios, border=0, split_only=True)
        height_medios = len(lines_medios) * line_height
        
        # Para Plan Mejora (puede ser largo también)
        lines_plan = pdf.multi_cell(col_widths['plan'] - 2, line_height, plan_mejora, border=0, split_only=True)
        height_plan = len(lines_plan) * line_height
        
        # La altura real es el máximo de todas las columnas
        real_height = max(height_accion, height_medios, height_plan, min_row_height)
        
        # Verificar si hay espacio en la página (margen inferior = 15mm)
        if pdf.get_y() + real_height > 270:
            pdf.add_page()
            # Repetir encabezados en nueva página con colores institucionales
            pdf.set_font('Arial', 'B', 7)
            pdf.set_fill_color(*AZUL_UTEM_CLARO)
            pdf.set_text_color(*AZUL_UTEM_OSCURO)
            pdf.cell(col_widths['accion'], 6, 'Accion', 1, 0, 'C', True)
            pdf.cell(col_widths['fecha'], 6, 'Fecha', 1, 0, 'C', True)
            pdf.cell(col_widths['estado'], 6, 'Estado', 1, 0, 'C', True)
            pdf.cell(col_widths['medios'], 6, 'Medios Verificacion', 1, 0, 'C', True)
            pdf.cell(col_widths['plan'], 6, 'Plan Mej.', 1, 1, 'C', True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 7)
        
        # Guardar posición inicial para dibujar
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # PRIMERO: Dibujar TODOS los rectángulos con la misma altura
        # Columna 1: Acción
        pdf.rect(x_start, y_start, col_widths['accion'], real_height)
        
        # Columna 2: Fecha
        pdf.rect(x_start + col_widths['accion'], y_start, col_widths['fecha'], real_height)
        
        # Columna 3: Estado
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'], y_start, col_widths['estado'], real_height)
        
        # Columna 4: Medios
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'], y_start, col_widths['medios'], real_height)
        
        # Columna 5: Plan Mejora
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + col_widths['medios'], y_start, col_widths['plan'], real_height)
        
        # SEGUNDO: Escribir el texto en cada celda (con padding)
        padding = 1  # Padding interno
        
        # Columna 1: Acción (texto largo, multi_cell)
        pdf.set_xy(x_start + padding, y_start + padding)
        pdf.multi_cell(col_widths['accion'] - (padding * 2), line_height, texto, border=0, align='L')
        
        # Columna 2: Fecha (texto centrado verticalmente)
        pdf.set_xy(x_start + col_widths['accion'] + padding, y_start + (real_height - line_height) / 2)
        pdf.cell(col_widths['fecha'] - (padding * 2), line_height, fecha, 0, 0, 'C')
        
        # Columna 3: Estado (texto centrado verticalmente)
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + padding, y_start + (real_height - line_height) / 2)
        pdf.cell(col_widths['estado'] - (padding * 2), line_height, estado, 0, 0, 'C')
        
        # Columna 4: Medios (texto largo, multi_cell)
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + padding, y_start + padding)
        pdf.multi_cell(col_widths['medios'] - (padding * 2), line_height, medios, border=0, align='L')
        
        # Columna 5: Plan Mejora (puede ser largo, usar multi_cell)
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + col_widths['medios'] + padding, y_start + padding)
        pdf.multi_cell(col_widths['plan'] - (padding * 2), line_height, plan_mejora, border=0, align='L')
        
        # Mover a siguiente fila
        pdf.set_xy(x_start, y_start + real_height)


def generate_pdf_report(content_data: dict, report_title: str = "Reporte_Generado") -> dict:
    """
    Genera un reporte PDF basado en datos proporcionados y lo guarda localmente.
    
    NOTA: Esta tool solo genera el PDF. Para subirlo a Cloud Storage,
    usa la tool 'upload_pdf_to_storage' con la ruta retornada.
    
    Args:
        content_data: Un diccionario con toda la data estructurada (identificacion, resumen, dimensiones, etc.).
        report_title: El nombre que tendra el archivo PDF final (sin extension).
        
    Returns:    
        dict: Diccionario con el resultado:
            - ok: bool indicando si fue exitoso
            - file_path: Ruta absoluta del PDF generado (si ok=True)
            - filename: Nombre del archivo (si ok=True)
            - error: Mensaje de error (si ok=False)
    """
    try:
        # Crear carpeta 'reportes' 
        current_dir = os.path.dirname(os.path.abspath(__file__))
        reportes_dir = os.path.join(current_dir, '..', 'reportes')
        os.makedirs(reportes_dir, exist_ok=True)
        
        # Limpiamos el nombre del archivo
        safe_filename = f"{report_title.replace(' ', '_')}.pdf"
        output_path = os.path.join(reportes_dir, safe_filename)
        output_path_abs = os.path.abspath(output_path)
        
        # Crear el PDF
        pdf = ReportePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título principal con colores institucionales
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(*AZUL_UTEM_OSCURO)
        pdf.cell(0, 8, 'PROYECTOS DE DESARROLLO 2022 - 2025', 0, 1, 'C')
        pdf.set_font('Arial', 'B', 12)
        anio = content_data.get('anio_informe', '2025')
        pdf.cell(0, 6, f'INFORME DE AVANCE - Ano {anio}', 0, 1, 'C')
        pdf.cell(0, 6, 'DIRECCION DE ASEGURAMIENTO DE CALIDAD DE PRE Y POSTGRADO', 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)  # Resetear a negro
        pdf.ln(5)
        
        # 1. IDENTIFICACION
        pdf.seccion_titulo('1', 'IDENTIFICACION')
        
        identificacion = content_data.get('identificacion', {})
        pdf.set_font('Arial', '', 10)
        
        items_identificacion = [
            ('Carrera', identificacion.get('carrera', 'N/A')),
            ('Decano', identificacion.get('decano', 'N/A')),
            ('Director de Escuela', identificacion.get('director', 'N/A')),
            ('Jefe de Carrera', identificacion.get('jefe_carrera', 'N/A')),
            ('Coordinador de Calidad', identificacion.get('coordinador', 'N/A')),
            ('Fecha inicio / término', identificacion.get('fechas', 'N/A')),
            ('Fecha presentación informe', identificacion.get('fecha_informe', 'N/A')),
        ]
        
        for label, value in items_identificacion:
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(*AZUL_UTEM_CLARO)
            pdf.set_text_color(*AZUL_UTEM_OSCURO)
            pdf.cell(60, 6, label, 1, 0, 'L', True)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, limpiar_texto(str(value)), 1, 1, 'L')
        
        pdf.ln(5)
        
        # 2. RESUMEN DEL PROYECTO
        pdf.add_page()
        pdf.seccion_titulo('2', 'RESUMEN DEL PROYECTO DE DESARROLLO')
        pdf.ln(3)
        pdf.ln(3)
        
        resumen = content_data.get('resumen', {})
        aspectos_resumen = [
            ('Avance general del proceso de implementación', resumen.get('avance_general', 'N/A')),
            ('Principales logros y resultados alcanzados a la fecha', resumen.get('logros', 'N/A')),
            ('Gestión y estrategias de articulación', resumen.get('gestion', 'N/A')),
            ('Dificultades y desafíos', resumen.get('dificultades', 'N/A')),
            ('Otra información relevante', resumen.get('otros', 'N/A')),
        ]
        
        for aspecto, descripcion in aspectos_resumen:
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(*AZUL_UTEM_CLARO)
            pdf.set_text_color(*AZUL_UTEM_OSCURO)
            pdf.cell(0, 6, aspecto, 1, 1, 'L', True)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, limpiar_texto(str(descripcion)), 1)
            pdf.ln(2)
        
        # 3. DESCRIPCION DEL ESTADO DE AVANCE
        pdf.add_page()
        pdf.seccion_titulo('3', 'DESCRIPCION DEL ESTADO DE AVANCE')
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, 'Nota: L (Logrado), NL (No Logrado), NA (No Aplica).', 0, 1, 'L')
        pdf.ln(3)
        
        dimensiones = content_data.get('dimensiones', {})
        
        # Dimensiones
        dimensiones_info = [
            ('dim1', 'Dimensión N°I: Docencia y resultados del proceso de formación'),
            ('dim2', 'Dimensión N°II: Gestión estratégica y recursos institucionales'),
            ('dim3', 'Dimensión N°III: Aseguramiento interno de la calidad'),
            ('dim4', 'Dimensión N°IV: Vinculación con el Medio'),
            ('dim5', 'Dimensión N°V: Investigación, creación y/o innovación'),
        ]
        
        for dim_key, dim_titulo in dimensiones_info:
            # Usar el método dimension_titulo para estilo consistente
            pdf.dimension_titulo(dim_titulo)
            
            dim_data = dimensiones.get(dim_key, {})
            acciones = dim_data.get('acciones', [])
            
            generar_tabla_dimension(pdf, acciones)
            pdf.ln(3)
        
        # 4. ANEXOS
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(*AZUL_UTEM_CLARO)
        pdf.set_text_color(*AZUL_UTEM_OSCURO)
        pdf.cell(0, 6, '4. ANEXOS', 1, 1, 'L', True)
        pdf.set_text_color(0, 0, 0)
        
        anexos = content_data.get('anexos', [])
        pdf.set_font('Arial', '', 9)
        if anexos:
            for anexo in anexos:
                numero = limpiar_texto(str(anexo.get('numero', '')))
                descripcion = limpiar_texto(str(anexo.get('descripcion', '')))
                pdf.cell(0, 5, f"{numero}: {descripcion}", 0, 1, 'L')
        else:
            pdf.cell(0, 5, 'No se adjuntan anexos.', 0, 1, 'L')
        
        # Footer final
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        fecha_gen = content_data.get('fecha_generacion', datetime.now().strftime('%Y-%m-%d %H:%M'))
        pdf.cell(0, 5, f'Documento generado automáticamente por Agente Institucional UTEM - {fecha_gen}', 0, 1, 'R')
        
        # Guardar el PDF
        pdf.output(output_path_abs)
        
        return {
            "ok": True,
            "file_path": output_path_abs,
            "filename": safe_filename,
            "message": f"PDF generado exitosamente: {safe_filename}"
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"Error al generar el reporte: {str(e)}"
        }


# Exportar como FunctionTool
generate_pdf_report_tool = FunctionTool(generate_pdf_report)