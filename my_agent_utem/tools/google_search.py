from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools import AgentTool

search_agent = LlmAgent(
    name="Agente_busqueda_Google",
    model="gemini-2.5-flash",
    description="Agente especializado en la búsqueda de información relevante utilizando Google Search.",
    instruction="""
    Eres un agente especializado en realizar búsquedas en Google para encontrar información relevante y actualizada. Utiliza la herramienta de búsqueda de Google para responder a las consultas de los usuarios de manera precisa y eficiente.

    """,
    tools=[
        google_search,
    ]
)

google_search_tool = AgentTool(search_agent)