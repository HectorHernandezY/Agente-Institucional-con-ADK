#from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from .prompts import PROMPT_AGENT_UTEM

from .tools.query_rag import search_rag_tool, list_documents_tool
from .tools.generate_chart import generate_chart_tool

root_agent = LlmAgent(
    name="Agente_UTEM",
    model="gemini-2.5-flash",
    description="Agente especializado en el análisis de informes de avance de Proyectos de Desarrollo de Carrera (PDC) de la UTEM.",
    instruction=PROMPT_AGENT_UTEM,
    tools=[
        search_rag_tool, 
        list_documents_tool,
        generate_chart_tool
    ]
)
