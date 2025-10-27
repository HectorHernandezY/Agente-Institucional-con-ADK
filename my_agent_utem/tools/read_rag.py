from __future__ import annotations
import os
from typing import Any, Optional

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.adk.tools import FunctionTool

# Vertex AI RAG (solo para list_files)
try:
    from vertexai.preview import rag
    from vertexai import init as vertex_init
except Exception as e:
    rag = None
    vertex_init = None
    _import_error = e
else:
    _import_error = None

# Configuración
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "muruna-utem-project")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "europe-west4")

# Nombre del corpus RAG (fijo)
RAG_CORPUS_NAME = "projects/muruna-utem-project/locations/europe-west4/ragCorpora/6917529027641081856"

# ──────────────────────────────────────────────────────────────────────────────
# TOOL PRINCIPAL: Vertex AI RAG Retrieval (nativa de ADK)
# ──────────────────────────────────────────────────────────────────────────────
query_vertex_rag_tool = VertexAiRagRetrieval(
    name="query_vertex_rag",
    description="Busca información en el corpus RAG de documentos UTEM. Úsala para responder preguntas sobre proyectos de desarrollo, actividades logradas, presupuestos y avances.",
    rag_corpora=[RAG_CORPUS_NAME],
    similarity_top_k=30,
    vector_distance_threshold=0.8,
)


# ──────────────────────────────────────────────────────────────────────────────
# TOOL AUXILIAR: Listar archivos del corpus
# ──────────────────────────────────────────────────────────────────────────────
def list_rag_files(
    project_id: Optional[str] = None,
    location: Optional[str] = None,
) -> dict[str, Any]:
    """
    Lista todos los archivos indexados en el corpus RAG de documentos UTEM.

    Args:
        project_id: (Opcional) ID del proyecto GCP
        location: (Opcional) Región del corpus RAG

    Returns:
        Diccionario con la lista de archivos indexados
    """
    if _import_error is not None:
        return {
            "ok": False,
            "status": "Error",
            "message": f"No se pudo importar Vertex AI SDK: {_import_error}"
        }

    p_id = project_id or PROJECT_ID
    loc = location or VERTEX_LOCATION

    try:
        # Inicializar Vertex AI
        vertex_init(project=p_id, location=loc)

        # Listar archivos en el corpus
        files = rag.list_files(corpus_name=RAG_CORPUS_NAME)

        files_list = []
        for file in files:
            files_list.append({
                "name": getattr(file, 'name', 'Unknown'),
                "display_name": getattr(file, 'display_name', 'Unknown'),
                "size_bytes": getattr(file, 'size_bytes', 0),
                "create_time": str(getattr(file, 'create_time', '')),
            })

        # Formatear lista legible
        files_text = "\n".join([
            f"- {f['display_name']} ({f['size_bytes']} bytes)"
            for f in files_list
        ])

        return {
            "ok": True,
            "status": f"Se encontraron {len(files_list)} archivos",
            "files": files_list,
            "files_list": files_text,
            "total_files": len(files_list)
        }

    except Exception as e:
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error listando archivos: {str(e)}",
            "error_type": type(e).__name__
        }


# Exponer list_rag_files como FunctionTool
list_rag_files_tool = FunctionTool(list_rag_files)