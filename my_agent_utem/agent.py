#from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from .prompts import PROMPT_AGENT_UTEM
#from google.adk.tools import AgentTool
from .tools.google_search import google_search_tool
from .tools.query_rag import search_rag_tool, list_documents_tool

#from .tools.generate_chart import generate_chart_tool

from .agents.bq_agent import bq_universidad_agent
from .agents.reportes_agent import agente_reportes_institucionales

root_agent = LlmAgent(
    name="Agente_UTEM",
    model="gemini-2.5-flash",
    description="Agente especializado en el análisis de informes de avance de Proyectos de Desarrollo de Carrera (PDC) de la UTEM.",
    instruction=PROMPT_AGENT_UTEM,
    tools=[
        search_rag_tool, 
        list_documents_tool,
        google_search_tool,
        #generate_chart_tool
    ],
    sub_agents=[bq_universidad_agent, agente_reportes_institucionales]
)

