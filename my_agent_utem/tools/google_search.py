from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools import AgentTool

search_agent = LlmAgent(
    name="Agente_busqueda_Google",
    model="gemini-2.5-flash",
    description="Agente especializado en la búsqueda de información relevante utilizando Google Search.",
    instruction="""
    Eres un agente especializado en realizar búsquedas en Google para encontrar información relevante y actualizada. Utiliza la herramienta de búsqueda de Google para responder a las consultas de los usuarios de manera precisa y eficiente.

    Reglas:
    1. Siempre debes deribar la conversacion con el usuario cuando este pida generar un reporte al agente 'agente_reportes_institucionales'
    2. Siempre debes deribar la conversacion con el usuario cuando este pida consultar tablas, matriculas, cantidad de estudiantes, consultas a bigquery,etc. al agente 'bq_universidad_agent'
    3. Siempre debes deribar la conversacion con el usuario cuando este pida buscar informacion de documentos especificos, listar los documentos, etc. al agente 'agente_busqueda_documental' 

    """,
    tools=[
        google_search,
    ]
)

google_search_tool = AgentTool(search_agent)