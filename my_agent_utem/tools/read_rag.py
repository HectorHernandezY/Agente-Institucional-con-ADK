from __future__ import annotations
import os
from typing import Any, Optional

from google.adk.tools import FunctionTool

# Vertex AI RAG
try:
    from vertexai.preview import rag
    from vertexai.preview.rag.utils.resources import RagResource
    from vertexai import init as vertex_init
    from google.api_core import exceptions as api_exceptions
except Exception as e:
    rag = None
    RagResource = None
    vertex_init = None
    api_exceptions = None
    _import_error = e
else:
    _import_error = None

# Config por defecto
PROJECT_ID = os.getenv("PROJECT_ID", "muruna-utem-project")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")


def _ensure_vertex_initialized(project_id: str, location: str) -> None:
    if _import_error is not None:
        raise ImportError(f"No se pudo importar Vertex AI SDK: {_import_error}")
    if vertex_init is None:
        raise RuntimeError("Vertex AI SDK no está disponible.")
    vertex_init(project=project_id, location=location)


def _find_corpus_name_by_id(
    initiative_id: str, project_id: str, location: str
) -> Optional[str]:
    """Busca el nombre completo de un corpus RAG por su display_name."""
    _ensure_vertex_initialized(project_id, location)
    for corpus in rag.list_corpora():
        if corpus.display_name == initiative_id:
            return corpus.name
    return None


def query_initiative_rag(
    initiative_id: str,
    query: str,
    project_id: Optional[str] = None,
    location: Optional[str] = None,
) -> dict[str, Any]:
    """
    Realiza una consulta de recuperación en el corpus RAG de una iniciativa específica.

    Args:
        initiative_id: El ID de la iniciativa, usado para encontrar el corpus RAG.
        query: La pregunta o término de búsqueda para consultar en el RAG.
        project_id: (Opcional) ID del proyecto de Google Cloud.
        location: (Opcional) Ubicación del proyecto de Google Cloud.

    Returns:
        Un diccionario con las respuestas encontradas o un mensaje de error.
    """
    if not initiative_id or not query:
        raise ValueError("Los parámetros 'initiative_id' y 'query' son obligatorios.")

    p_id = project_id or PROJECT_ID
    loc = location or VERTEX_LOCATION

    try:
        corpus_name = _find_corpus_name_by_id(initiative_id, p_id, loc)
        if not corpus_name:
            return {
                "ok": False,
                "status": "Not Found",
                "message": f"No se encontró un corpus RAG para la iniciativa con ID: {initiative_id}",
            }

        # Realizar la consulta de recuperación
        response = rag.retrieval_query(
            rag_resources=[RagResource(rag_corpus=corpus_name)],
            text=query,
            similarity_top_k=5,
            vector_distance_threshold=0.5,
        )

        return {
            "ok": True,
            "status": "Consulta completada.",
            "results": [
                {"source": context.source_uri, "text": context.text}
                for context in response.contexts.contexts
            ],
        }
    except api_exceptions.GoogleAPICallError as e:
        raise RuntimeError(f"Error de API al consultar Vertex RAG: {e}")
    except Exception as e:
        raise RuntimeError(f"Ocurrió un error inesperado al consultar el RAG: {e}")


# Exponer la función como una herramienta para el agente
read_rag_tool = FunctionTool(query_initiative_rag)