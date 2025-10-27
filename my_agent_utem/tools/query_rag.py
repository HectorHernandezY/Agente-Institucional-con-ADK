from __future__ import annotations
import os
import re
import numpy as np
from typing import Any, Optional
import traceback

from google.cloud import firestore
from vertexai.language_models import TextEmbeddingModel
from google.adk.tools import FunctionTool
from google.auth import default
import vertexai

# Configuración
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "muruna-utem-project")
VERTEX_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Configurar credenciales
credentials, _ = default(quota_project_id=PROJECT_ID)
db = firestore.Client(project=PROJECT_ID, credentials=credentials)
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
    
    Nueva estructura:
    rag_vectores2/
      └── {doc_id}/
          ├── metadata
          └── chunks/
              ├── chunk_0
              └── ...
    
    Args:
        query: Pregunta o consulta del usuario
        document_name: (Opcional) Nombre del documento específico para filtrar
        top_k: Número máximo de resultados
        similarity_threshold: Umbral mínimo de similitud (0-1)
    
    Returns:
        Contextos relevantes encontrados
    """
    try:
        # 1. Generar embedding de la query
        query_embeddings = embedding_model.get_embeddings([query])
        query_vector = query_embeddings[0].values
        
        # 2. Obtener todos los documentos de la colección principal
        docs_ref = db.collection("rag_vectores2")
        all_docs = list(docs_ref.stream())
        
        if not all_docs:
            return {
                "ok": False,
                "status": "No hay documentos indexados",
                "message": "La colección rag_vectores2 está vacía"
            }
        
        # 3. Filtrar por nombre de documento si se especifica
        if document_name:
            normalized_search = normalize_doc_name(document_name)
            filtered_doc_ids = []
            
            for doc in all_docs:
                doc_data = doc.to_dict()
                doc_name = doc_data.get("doc_name", "")
                normalized_doc = normalize_doc_name(doc_name)
                
                # Búsqueda parcial
                if normalized_search in normalized_doc or normalized_doc in normalized_search:
                    filtered_doc_ids.append(doc.id)
            
            if not filtered_doc_ids:
                return {
                    "ok": False,
                    "status": f"No se encontró documento: '{document_name}'",
                    "message": "Verifica el nombre del documento"
                }
            
            target_doc_ids = filtered_doc_ids
        else:
            target_doc_ids = [doc.id for doc in all_docs]
        
        # 4. Buscar en los chunks de cada documento
        results = []
        
        for doc_id in target_doc_ids:
            # Obtener metadata del documento
            doc_ref = db.collection("rag_vectores2").document(doc_id)
            doc_metadata = doc_ref.get().to_dict()
            
            # Acceder a la subcolección de chunks
            chunks_ref = doc_ref.collection("chunks")
            chunks = list(chunks_ref.stream())
            
            for chunk_doc in chunks:
                chunk_data = chunk_doc.to_dict()
                
                if "embedding" not in chunk_data or "text" not in chunk_data:
                    continue
                
                # Calcular similitud
                similarity = cosine_similarity(query_vector, chunk_data["embedding"])
                
                if similarity >= similarity_threshold:
                    results.append({
                        "doc_id": doc_id,
                        "doc_name": doc_metadata.get("doc_name", "Unknown"),
                        "chunk_id": chunk_data.get("chunk_id"),
                        "chunk_index": chunk_data.get("chunk_index"),
                        "text": chunk_data.get("text"),
                        "similarity_score": similarity,
                        "gcs_uri": doc_metadata.get("gcs_uri"),
                        "firestore_path": f"rag_vectores2/{doc_id}/chunks/{chunk_doc.id}"
                    })
        
        # 5. Ordenar por similitud y limitar
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_results = results[:top_k]
        
        # 6. Actualizar contadores de acceso
        if top_results:
            batch = db.batch()
            for result in top_results:
                doc_id = result["doc_id"]
                chunk_id = result["chunk_id"]
                chunk_ref = db.collection("rag_vectores2").document(doc_id).collection("chunks").document(chunk_id)
                
                batch.update(chunk_ref, {
                    "access_count": firestore.Increment(1),
                    "last_accessed": firestore.SERVER_TIMESTAMP
                })
            batch.commit()
        
        search_scope = f"documento '{document_name}'" if document_name else "todos los documentos"
        
        # 7. Formatear respuesta
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
            "contexts_text": contexts_text,
            "total_found": len(results)
        }
        
    except Exception as e:
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error en consulta RAG: {str(e)}",
            "traceback": traceback.format_exc()
        }


def list_available_documents() -> dict[str, Any]:
    """
    Lista todos los documentos disponibles en el sistema RAG.
    
    Nueva estructura: lee de rag_vectores2/ (documentos principales)
    
    Returns:
        Lista de documentos con metadata
    """
    try:
        docs_ref = db.collection("rag_vectores2")
        docs = docs_ref.stream()
        
        documents = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            documents.append({
                "doc_id": doc.id,
                "doc_name": doc_data.get("doc_name", "Unknown"),
                "total_chunks": doc_data.get("total_chunks", 0),
                "file_type": doc_data.get("file_type", "Unknown"),
                "gcs_uri": doc_data.get("gcs_uri"),
                "created_at": doc_data.get("created_at"),
                "firestore_path": f"rag_vectores2/{doc.id}"
            })
        
        # Formatear lista legible
        docs_list = "\n".join([
            f"- {doc['doc_name']} ({doc['file_type']}, {doc['total_chunks']} chunks)"
            for doc in documents
        ])
        
        return {
            "ok": True,
            "status": f"Se encontraron {len(documents)} documentos",
            "documents": documents,
            "documents_list": docs_list,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error listando documentos: {str(e)}",
            "traceback": traceback.format_exc()
        }


# Exportar como tools
search_rag_tool = FunctionTool(search_documents)
list_documents_tool = FunctionTool(list_available_documents)