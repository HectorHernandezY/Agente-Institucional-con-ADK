from google.adk.agents import LlmAgent
from my_agent_utem.tools.generate_pdf_report import generate_pdf_report_tool
from my_agent_utem.tools.upload_to_storage import upload_pdf_to_storage_tool
from my_agent_utem.tools.query_rag import search_rag_tool, list_documents_tool
from my_agent_utem.prompts import PROMPT_AGENT_REPORTES


agente_reportes_institucionales = LlmAgent(
    name="agente_reportes_institucionales",
    model="gemini-2.5-flash",  # Usar un modelo capaz de manejar contextos largos
    description="""Agente especializado en la generacion de informes academicos para la UTEM.
    Puede recibir datos directamente del usuario O buscar informacion en documentos indexados.
    Usalo cuando el usuario quiera generar un reporte PDF, ya sea con datos proporcionados
    o basandose en un documento especifico del sistema RAG.
    
    Capacidades:
    - Recibir texto extraido de documentos adjuntos (el frontend hace la extraccion)
    - Buscar en documentos indexados con search_rag_tool
    - Generar reportes PDF con generate_pdf_report_tool
    - Subir a Cloud Storage con upload_pdf_to_storage_tool
    """,
    tools=[
        generate_pdf_report_tool,      # Generador de PDF (local)
        upload_pdf_to_storage_tool,    # Subir PDF a Cloud Storage
        search_rag_tool,               # Busqueda en documentos
        list_documents_tool            # Listar documentos disponibles
    ],
    instruction=PROMPT_AGENT_REPORTES
)


