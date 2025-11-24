import os
import jinja2
from xhtml2pdf import pisa
from google.adk.tools import FunctionTool

def generate_pdf_report(content_data: dict, report_title: str = "Reporte_Generado", template_type: str = "archivo_test") -> str:
    """
    Genera un reporte PDF basado en un template y datos proporcionados.
    
    Args:
        content_data: Un diccionario con toda la data estructurada (identificacion, resumen, dimensiones, etc.).
        report_title: El nombre que tendrá el archivo PDF final (sin extensión).
        template_type: El nombre del archivo HTML en la carpeta templates (sin extensión .html).
        
    Returns:    
        str: La ruta local del archivo generado o un mensaje de error.
    """
    try:
        # 1. Calcular la ruta absoluta a la carpeta 'templates'
        # Obtenemos la ruta donde está ESTE archivo .py (tools/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Subimos un nivel y entramos a templates
        template_dir = os.path.join(current_dir, '..', 'templates')

        # 2. Configurar el entorno de Jinja2
        template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
        template_env = jinja2.Environment(loader=template_loader)
        
        # 3. Cargar el template
        # Añadimos .html automáticamente si no viene en el string
        if not template_type.endswith('.html'):
            template_type += '.html'
            
        template = template_env.get_template(template_type)
        
        # 4. Renderizar el HTML con los datos
        # Usamos **content_data para "desempaquetar" el diccionario
        # Así en el HTML usas {{ identificacion }} en vez de {{ data.identificacion }}
        output_text = template.render(**content_data)
        
        # 5. Convertir a PDF usando xhtml2pdf
        # Crear carpeta 'reportes' al mismo nivel que 'agents' y 'tools'
        reportes_dir = os.path.join(current_dir, '..', 'reportes')
        os.makedirs(reportes_dir, exist_ok=True)
        
        # Limpiamos el nombre del archivo de espacios para evitar errores en Windows
        safe_filename = f"{report_title.replace(' ', '_')}.pdf"
        output_path = os.path.join(reportes_dir, safe_filename)
        
        # Convertir la ruta a absoluta para mostrarla correctamente
        output_path_abs = os.path.abspath(output_path)
        
        # xhtml2pdf genera el PDF desde el HTML renderizado
        with open(output_path_abs, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(output_text, dest=pdf_file)
            
        if pisa_status.err:
            return f"Error al generar el PDF: {pisa_status.err}"
        
        return f"Reporte generado exitosamente en: {output_path_abs}"

    except jinja2.exceptions.TemplateNotFound:
        return f"Error: No se encontró el template '{template_type}' en la ruta: {template_dir}"
    except Exception as e:
        return f"Error al generar el reporte: {str(e)}"

# Exportar como FunctionTool
generate_pdf_report_tool = FunctionTool(generate_pdf_report)