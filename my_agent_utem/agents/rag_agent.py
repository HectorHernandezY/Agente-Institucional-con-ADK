from google.adk.agents import LlmAgent
from ..tools.query_rag import search_rag_tool, list_documents_tool
from ..prompts import PROMPT_RAG_AGENT

# Crear el agente RAG especializado
agente_busqueda_documental = LlmAgent(
    name="agente_busqueda_documental",
    model="gemini-2.5-flash",
    description="""Agente especializado en búsqueda vectorial RAG. 
    Úsalo cuando necesites:
    - Buscar información en documentos PDF/DOCX indexados
    - Listar documentos disponibles en la base de conocimiento
    - Extraer contexto relevante sobre informes PDC, carreras, actividades, etc.
    
    Este agente NO analiza ni interpreta datos, solo los recupera.""",
    instruction=PROMPT_RAG_AGENT,
    tools=[search_rag_tool, list_documents_tool]
)
