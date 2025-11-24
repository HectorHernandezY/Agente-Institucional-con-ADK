from google.adk.agents import LlmAgent
from adk_file_search_agent.tools.file_search_tool import create_store_tool, upload_file_tool, query_store_tool

# Define the ADK Agent
file_search_agent = LlmAgent(
    name="FileSearchAgent",
    model="gemini-1.5-flash",
    description="Un agente capaz de indexar y buscar información en archivos PDF utilizando Gemini File Search.",
    instruction="""
    Eres un asistente inteligente con acceso a una herramienta de búsqueda de archivos (File Search).
    
    Tu flujo de trabajo ideal es:
    1. Si el usuario te pide preparar la base de conocimientos o subir un archivo, usa 'create_store' (si no existe) y luego 'upload_file'.
    2. Si el usuario hace una pregunta sobre el documento, usa 'query_store' para obtener fragmentos relevantes.
    3. Usa la información devuelta por 'query_store' para responder la pregunta del usuario. Cita las fuentes si es posible.
    
    El archivo objetivo predeterminado es: /mnt/data/Informe Avance 2025 PDC Ing civil Biomédica.pdf
    """,
    tools=[
        create_store_tool,
        upload_file_tool,
        query_store_tool
    ]
)

# Optional: If you want to run this agent directly with ADK runner
if __name__ == "__main__":
    from google.adk.runners import ConsoleRunner
    runner = ConsoleRunner(agent=file_search_agent)
    runner.run()
