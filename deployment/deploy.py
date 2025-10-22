import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.adk.sessions import VertexAiSessionService, BaseSessionService
from google.adk.sessions import InMemorySessionService


# Configuración
PROJECT_ID = "muruna-utem-project"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://db_agent_utem"
ENGINE_DISPLAY_NAME = 'agent_utem'
REQUIREMENTS_PATH = os.path.join(current_dir, "requirements.txt")
EXTRA_PACKAGES = ["./my_agent_utem"]

def build_session_service() -> BaseSessionService:
    return VertexAiSessionService()

# INIT PRIMERO
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

print("Iniciando actualización del agente...")

# IMPORTAR EL AGENTE DESPUÉS DEL INIT
from my_agent_utem.agent import root_agent

app = AdkApp(
    agent=root_agent,
    session_service_builder=build_session_service,
    enable_tracing=True,
)

env_vars = {
    "FIRESTORE_PROJECT_ID": "muruna-utem-project",
    "DATABASE_ID": "(default)",
    "GCS_RAG_BUCKET": "db_agent_utem",
}

# CREAR NUEVO AGENTE (sin resource_name)
remote_app = agent_engines.update(
    resource_name="projects/muruna-utem-project/locations/us-central1/reasoningEngines/4532120958995005440",
    agent_engine=app,
    display_name=ENGINE_DISPLAY_NAME,
    gcs_dir_name='db_agent_utem',
    requirements=REQUIREMENTS_PATH,
    extra_packages=EXTRA_PACKAGES,
    env_vars=env_vars,
    service_account="433491555173-compute@developer.gserviceaccount.com", 
)

print(f"Agente actualizado '{ENGINE_DISPLAY_NAME}' exitosamente.")
print(f"Recurso: {remote_app.resource_name}")


