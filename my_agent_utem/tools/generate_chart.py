import os
import tempfile
import matplotlib.pyplot as plt
import io
import base64
from google.adk.tools import FunctionTool


def generate_progress_chart(project_name: str, total_progress: float, completed: int, not_completed: int, not_applicable: int) -> str:
    """
    Genera un gráfico de avance del proyecto.
    
    Args:
        project_name: Nombre del proyecto
        total_progress: Porcentaje total de avance
        completed: Número de actividades logradas
        not_completed: Número de actividades no logradas
        not_applicable: Número de actividades que no aplican
    
    Returns:
        Descripción del gráfico generado
    """
    # Crear figura con dos subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Gráfico de torta para el avance total
    ax1.pie([total_progress, 100-total_progress], 
            labels=[f'Completado\n{total_progress}%', f'Pendiente\n{100-total_progress:.2f}%'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#4CAF50', '#e0e0e0'])
    ax1.set_title(f'Avance Total del Proyecto\n{project_name}')
    
    # Gráfico de barras para actividades
    categories = ['Logradas', 'No Logradas', 'No Aplica']
    values = [completed, not_completed, not_applicable]
    colors = ['#4CAF50', '#F44336', '#9E9E9E']
    
    ax2.bar(categories, values, color=colors)
    ax2.set_ylabel('Número de Actividades')
    ax2.set_title('Distribución de Actividades')
    ax2.set_ylim(0, max(values) + 2)
    
    # Agregar valores sobre las barras
    for i, v in enumerate(values):
        ax2.text(i, v + 0.1, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Guardar el gráfico (compatible con Windows)
    img_filename = f'progress_chart_{project_name.replace(" ", "_")}.png'
    img_path = os.path.join(tempfile.gettempdir(), img_filename)
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return f"Gráfico generado exitosamente y guardado en: {img_path}"


generate_chart_tool = FunctionTool(generate_progress_chart)