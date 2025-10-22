from __future__ import annotations
import os
from typing import  Any, Optional
import numpy as np
import re

from google.cloud import firestore
from vertexai.language_models import TextEmbeddingModel
from google.adk.tools import FunctionTool
from google.auth import default

# Configuración
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "muruna-utem-project")
VERTEX_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Configurar credenciales
credentials, _ = default(quota_project_id=PROJECT_ID)
db = firestore.Client(project=PROJECT_ID, credentials=credentials)

import vertexai
vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION, credentials=credentials)

try:
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
except Exception:
    embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calcula similitud coseno entre dos vectores"""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def normalize_doc_name(name: str) -> str:
    """Normaliza nombre de documento para búsqueda flexible"""
    # Quitar extensión
    name = re.sub(r'\.(docx|pdf|txt)$', '', name, flags=re.IGNORECASE)
    # Convertir a minúsculas
    name = name.lower()
    # Quitar espacios múltiples
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def search_documents(
    query: str,
    document_name: Optional[str] = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3
) -> dict[str, Any]:
    """
    Busca información en los documentos indexados.
    
    Args:
        query: Pregunta o consulta del usuario
        document_name: (Opcional) Nombre del documento específico para filtrar. 
                      Puede ser nombre parcial (ej: "Ing. Industrial" o "Industrial")
        top_k: Número máximo de resultados
        similarity_threshold: Umbral mínimo de similitud (0-1)
    
    Returns:
        Contextos relevantes encontrados
    """
    try:
        # 1. Generar embedding de la query
        query_embeddings = embedding_model.get_embeddings([query])
        query_vector = query_embeddings[0].values
        
        # 2. Buscar chunks en Firestore
        chunks_ref = db.collection("rag_vectores")
        chunks = list(chunks_ref.stream())
        
        # 3. Filtrar por documento si se especifica (búsqueda flexible)
        if document_name:
            normalized_search = normalize_doc_name(document_name)
            filtered_chunks = []
            
            for chunk_doc in chunks:
                chunk_data = chunk_doc.to_dict()
                doc_name = chunk_data.get("doc_name", "")
                normalized_doc = normalize_doc_name(doc_name)
                
                # Búsqueda parcial (contiene)
                if normalized_search in normalized_doc or normalized_doc in normalized_search:
                    filtered_chunks.append(chunk_data)
            
            chunks_data = filtered_chunks
        else:
            chunks_data = [chunk_doc.to_dict() for chunk_doc in chunks]
        
        # 4. Calcular similitudes
        results = []
        
        for chunk_data in chunks_data:
            if "embedding" not in chunk_data or "text" not in chunk_data:
                continue
            
            similarity = cosine_similarity(query_vector, chunk_data["embedding"])
            
            if similarity >= similarity_threshold:
                results.append({
                    "chunk_id": chunk_data.get("chunk_id"),
                    "text": chunk_data.get("text"),
                    "doc_name": chunk_data.get("doc_name"),
                    "gcs_uri": chunk_data.get("gcs_uri"),
                    "chunk_index": chunk_data.get("chunk_index", 0),
                    "similarity_score": round(similarity, 4)
                })
        
        # 5. Ordenar por similitud y limitar
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_results = results[:top_k]
        
        # 6. Actualizar contadores de acceso
        if top_results:
            batch = db.batch()
            for result in top_results:
                doc_ref = db.collection("rag_vectores").document(result["chunk_id"])
                batch.update(doc_ref, {
                    "access_count": firestore.Increment(1),
                    "last_accessed": firestore.SERVER_TIMESTAMP
                })
            batch.commit()
        
        search_scope = f"documento '{document_name}'" if document_name else "todos los documentos"
        
        # 7. Formatear respuesta con los textos completos
        contexts_text = "\n\n---\n\n".join([
            f"[{r['doc_name']} - Chunk {r['chunk_index']}]\n{r['text']}"
            for r in top_results
        ])
        
        return {
            "ok": True,
            "status": f"Se encontraron {len(top_results)} contextos relevantes en {search_scope}",
            "query": query,
            "document_filter": document_name,
            "contexts": top_results,
            "contexts_text": contexts_text,  # Texto formateado para el LLM
            "total_found": len(results)
        }
        
    except Exception as e:
        import traceback
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error en consulta RAG: {str(e)}",
            "traceback": traceback.format_exc()
        }


def list_available_documents() -> dict[str, Any]:
    """
    Lista todos los documentos disponibles en el sistema RAG.
    
    Returns:
        Lista de documentos únicos con metadata
    """
    try:
        chunks_ref = db.collection("rag_vectores")
        chunks = chunks_ref.stream()
        
        # Agrupar por doc_id para obtener documentos únicos
        docs_dict = {}
        
        for chunk_doc in chunks:
            chunk_data = chunk_doc.to_dict()
            doc_id = chunk_data.get("doc_id")
            
            if doc_id not in docs_dict:
                docs_dict[doc_id] = {
                    "doc_id": doc_id,
                    "doc_name": chunk_data.get("doc_name"),
                    "gcs_uri": chunk_data.get("gcs_uri"),
                    "total_chunks": chunk_data.get("total_chunks", 0),
                    "created_at": chunk_data.get("created_at")
                }
        
        documents = list(docs_dict.values())
        
        # Formatear lista legible
        docs_list = "\n".join([f"- {doc['doc_name']}" for doc in documents])
        
        return {
            "ok": True,
            "status": f"Se encontraron {len(documents)} documentos",
            "documents": documents,
            "documents_list": docs_list,  # Lista formateada para el LLM
            "total_documents": len(documents)
        }
        
    except Exception as e:
        import traceback
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error listando documentos: {str(e)}",
            "traceback": traceback.format_exc()
        }


# Exportar como tools
search_rag_tool = FunctionTool(search_documents)
list_documents_tool = FunctionTool(list_available_documents)