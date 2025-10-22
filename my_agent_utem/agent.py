#from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from .prompts import PROMPT_AGENT_UTEM
from my_agent_utem.tools.index_documents import index_document_tool
from my_agent_utem.tools.query_rag import search_rag_tool, list_documents_tool

root_agent = LlmAgent(

    name="Agente_UTEM",
    model="gemini-2.5-flash",
    instruction=PROMPT_AGENT_UTEM,
    tools=[
        index_document_tool,
        search_rag_tool,
        list_documents_tool,
    ]
)