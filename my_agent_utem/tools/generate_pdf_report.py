import os
import unicodedata
from fpdf import FPDF
from datetime import datetime
from google.adk.tools import FunctionTool 


def limpiar_texto(texto: str) -> str:
    """Limpia y normaliza texto para el PDF."""
    if not texto:
        return ""
    
    texto = str(texto)
    
    reemplazos = {
        '\u2013': '-',
        '\u2014': '-',
        '\u2015': '-',
        '\u2212': '-',
        
        '\u201c': '"',
        '\u201d': '"',
        '\u2018': "'",
        '\u2019': "'",
        '\u201a': ',',
        '\u201e': '"',
        '\u00ab': '"',
        '\u00bb': '"',
        
        '\u2026': '...',
        '\u2022': '*',
        '\u2023': '>',
        '\u2043': '-',
        
        '\u00a0': ' ',
        '\u2002': ' ',
        '\u2003': ' ',
        '\u2009': ' ',
        '\u200a': ' ',
        '\u200b': '',
        '\u202f': ' ',
        '\u205f': ' ',
        '\u3000': ' ',
        
        '\u00b0': 'o',
        '\u00b7': '*',
        '\u2033': '"',
        '\u2032': "'",
        '\u00d7': 'x',
        '\u00f7': '/',
        '\u2192': '->',
        '\u2190': '<-',
        '\u2194': '<->',
        '\u25cf': '*',
        '\u25cb': 'o',
        '\u25a0': '#',
        '\u25a1': '[]',
        '\u2713': '[x]',
        '\u2717': '[X]',
        '\u00ae': '(R)',
        '\u00a9': '(C)',
        '\u2122': '(TM)',
    }
    
    for char_unicode, char_ascii in reemplazos.items():
        texto = texto.replace(char_unicode, char_ascii)
    
    texto = unicodedata.normalize('NFC', texto)
    
    resultado = []
    for char in texto:
        try:
            char.encode('latin-1')
            resultado.append(char)
        except UnicodeEncodeError:
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


AZUL_UTEM_OSCURO = (26, 82, 118)
AZUL_UTEM_CLARO = (212, 230, 241)
AZUL_UTEM_MEDIO = (41, 128, 185)


class ReportePDF(FPDF):
    """Clase personalizada para generar reportes UTEM con formato institucional."""
    
    def __init__(self):
        super().__init__()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(current_dir, '..', 'templates', 'UTEM-LOGO.jpg')
    
    def header(self):
        """Encabezado del PDF."""
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 30)
        
        self.set_xy(45, 12)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 6, 'VRAC', 0, 1, 'L')
        
        self.set_xy(45, 19)
        self.set_font('Arial', '', 10)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 5, 'Vicerrectoria Academica', 0, 1, 'L')
        
        self.set_draw_color(*AZUL_UTEM_OSCURO)
        self.set_line_width(0.5)
        self.line(10, 38, 200, 38)
        
        self.set_text_color(0, 0, 0)
        self.ln(25)
    
    def footer(self):
        """Pie de página del PDF."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.set_text_color(0, 0, 0)
    
    def seccion_titulo(self, numero, titulo):
        """Genera un título de sección."""
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 7, f'{numero}. {titulo}', 0, 1, 'L')
        self.set_text_color(0, 0, 0)
    
    def dimension_titulo(self, titulo):
        """Genera un título de dimensión."""
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*AZUL_UTEM_CLARO)
        self.set_text_color(*AZUL_UTEM_OSCURO)
        self.cell(0, 6, titulo, 1, 1, 'L', True)
        self.set_text_color(0, 0, 0)


def generar_tabla_dimension(pdf, acciones):
    """Genera una tabla de dimensión."""
    if not acciones:
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 5, 'No hay acciones registradas para esta dimension.', 1, 1, 'L')
        return
    
    col_widths = {
        'accion': 65,
        'fecha': 20,
        'estado': 18,
        'medios': 60,
        'plan': 27
    }
    line_height = 4
    min_row_height = 8
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
    
    for accion in acciones:
        texto = limpiar_texto(str(accion.get('texto', 'N/A'))[:500])
        fecha = limpiar_texto(str(accion.get('fecha', 'N/A'))[:30])
        estado = limpiar_texto(str(accion.get('estado', 'N/A'))[:15])
        medios_list = accion.get('medios', ['N/A'])
        medios = ', '.join(medios_list) if isinstance(medios_list, list) else str(medios_list)
        medios = limpiar_texto(medios[:200])
        plan_mejora = limpiar_texto(str(accion.get('plan_mejora', 'N/A'))[:25])
        
        x_calc = pdf.get_x()
        y_calc = pdf.get_y()
        
        pdf.set_xy(x_calc, y_calc)
        lines_accion = pdf.multi_cell(col_widths['accion'] - 2, line_height, texto, border=0, split_only=True)
        height_accion = len(lines_accion) * line_height

        lines_medios = pdf.multi_cell(col_widths['medios'] - 2, line_height, medios, border=0, split_only=True)
        height_medios = len(lines_medios) * line_height

        lines_plan = pdf.multi_cell(col_widths['plan'] - 2, line_height, plan_mejora, border=0, split_only=True)
        height_plan = len(lines_plan) * line_height

        real_height = max(height_accion, height_medios, height_plan, min_row_height)

        if pdf.get_y() + real_height > 270:
            pdf.add_page()
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

        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        pdf.rect(x_start, y_start, col_widths['accion'], real_height)
        pdf.rect(x_start + col_widths['accion'], y_start, col_widths['fecha'], real_height)
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'], y_start, col_widths['estado'], real_height)
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'], y_start, col_widths['medios'], real_height)
        pdf.rect(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + col_widths['medios'], y_start, col_widths['plan'], real_height)
        
        padding = 1
        pdf.set_xy(x_start + padding, y_start + padding)
        pdf.multi_cell(col_widths['accion'] - (padding * 2), line_height, texto, border=0, align='L')
        
        pdf.set_xy(x_start + col_widths['accion'] + padding, y_start + (real_height - line_height) / 2)
        pdf.cell(col_widths['fecha'] - (padding * 2), line_height, fecha, 0, 0, 'C')
        
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + padding, y_start + (real_height - line_height) / 2)
        pdf.cell(col_widths['estado'] - (padding * 2), line_height, estado, 0, 0, 'C')
        
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + padding, y_start + padding)
        pdf.multi_cell(col_widths['medios'] - (padding * 2), line_height, medios, border=0, align='L')
        
        pdf.set_xy(x_start + col_widths['accion'] + col_widths['fecha'] + col_widths['estado'] + col_widths['medios'] + padding, y_start + padding)
        pdf.multi_cell(col_widths['plan'] - (padding * 2), line_height, plan_mejora, border=0, align='L')

        pdf.set_xy(x_start, y_start + real_height)


def generate_pdf_report(content_data: dict, report_title: str = "Reporte_Generado") -> dict:
    """Genera un reporte PDF y lo guarda localmente.
    
    Args:
        content_data: Diccionario con datos estructurados.
        report_title: Nombre del archivo PDF (sin extensión).
    Returns:    
        dict: Diccionario con el resultado:
            - ok: bool indicando si fue exitoso
            - file_path: Ruta absoluta del PDF generado (si ok=True)
            - filename: Nombre del archivo (si ok=True)
            - error: Mensaje de error (si ok=False)
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        reportes_dir = os.path.join(current_dir, '..', 'reportes')
        os.makedirs(reportes_dir, exist_ok=True)
        
        safe_filename = f"{report_title.replace(' ', '_')}.pdf"
        output_path = os.path.join(reportes_dir, safe_filename)
        output_path_abs = os.path.abspath(output_path)
        
        pdf = ReportePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(*AZUL_UTEM_OSCURO)
        pdf.cell(0, 8, 'PROYECTOS DE DESARROLLO 2022 - 2025', 0, 1, 'C')
        pdf.set_font('Arial', 'B', 12)
        anio = content_data.get('anio_informe', '2025')
        pdf.cell(0, 6, f'INFORME DE AVANCE - Ano {anio}', 0, 1, 'C')
        pdf.cell(0, 6, 'DIRECCION DE ASEGURAMIENTO DE CALIDAD DE PRE Y POSTGRADO', 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)  # Resetear a negro
        pdf.ln(5)
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

        pdf.add_page()
        pdf.seccion_titulo('3', 'DESCRIPCION DEL ESTADO DE AVANCE')
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, 'Nota: L (Logrado), NL (No Logrado), NA (No Aplica).', 0, 1, 'L')
        pdf.ln(3)
        
        dimensiones = content_data.get('dimensiones', {})
        dimensiones_info = [
            ('dim1', 'Dimensión N°I: Docencia y resultados del proceso de formación'),
            ('dim2', 'Dimensión N°II: Gestión estratégica y recursos institucionales'),
            ('dim3', 'Dimensión N°III: Aseguramiento interno de la calidad'),
            ('dim4', 'Dimensión N°IV: Vinculación con el Medio'),
            ('dim5', 'Dimensión N°V: Investigación, creación y/o innovación'),
        ]
        
        for dim_key, dim_titulo in dimensiones_info:
            pdf.dimension_titulo(dim_titulo)
            
            dim_data = dimensiones.get(dim_key, {})
            acciones = dim_data.get('acciones', [])
            
            generar_tabla_dimension(pdf, acciones)
            pdf.ln(3)
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

        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        fecha_gen = content_data.get('fecha_generacion', datetime.now().strftime('%Y-%m-%d %H:%M'))
        pdf.cell(0, 5, f'Documento generado automáticamente por Agente Institucional UTEM - {fecha_gen}', 0, 1, 'R')

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
generate_pdf_report_tool = FunctionTool(generate_pdf_report)