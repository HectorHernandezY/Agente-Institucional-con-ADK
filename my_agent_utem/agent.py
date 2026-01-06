from google.adk.agents import LlmAgent
from .prompts import PROMPT_AGENT_UTEM_ORCHESTRATOR
from .tools.google_search import google_search_tool

# Sub-agentes especializados
from .agents.bq_agent import bq_universidad_agent
from .agents.reportes_agent import agente_reportes_institucionales
from .agents.rag_agent import agente_busqueda_documental

root_agent = LlmAgent(
    name="Agente_UTEM",
    model="gemini-2.5-flash",
    description="Agente orquestador principal de UTEM. Coordina sub-agentes especializados para análisis de informes PDC, consultas de matrículas y generación de reportes.",
    instruction=PROMPT_AGENT_UTEM_ORCHESTRATOR,
    tools=[
        google_search_tool,  # Solo herramienta directa: búsqueda web
    ],
    sub_agents=[
        agente_busqueda_documental,              # Búsqueda en documentos RAG
        bq_universidad_agent,          # Consultas BigQuery matrículas
        agente_reportes_institucionales # Generación de reportes PDF
    ]
)

