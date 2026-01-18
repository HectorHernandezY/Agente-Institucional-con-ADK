"""Motor de búsqueda RAG para documentos UTEM."""
from __future__ import annotations
import os
import re
import numpy as np
from typing import Any, Optional, List, Dict
import traceback
import logging

from google.cloud import firestore
from vertexai.language_models import TextEmbeddingModel
from google.adk.tools import FunctionTool
from google.auth import default
import vertexai


PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "muruna-utem-project")
VERTEX_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
COLLECTION_NAME = "rag_vectores2"

DEFAULT_TOP_K = 35
DEFAULT_SIMILARITY_THRESHOLD = 0.45

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_db = None
_embedding_model = None
_initialized = False

EMBEDDING_MODELS = ["text-multilingual-embedding-002"]


def _initialize_clients():
    """Inicializa los clientes de GCP."""
    global _db, _embedding_model, _initialized
    
    if _initialized:
        return
    
    try:
        # Inicializar credenciales
        credentials, _ = default(quota_project_id=PROJECT_ID)
        
        # Inicializar Firestore
        _db = firestore.Client(
            project=PROJECT_ID, 
            database=DATABASE_ID, 
            credentials=credentials
        )
        
        vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION, credentials=credentials)
        
        for model_name in EMBEDDING_MODELS:
            try:
                _embedding_model = TextEmbeddingModel.from_pretrained(model_name)
                logger.info(f"✓ Modelo de embeddings cargado: {model_name}")
                break
            except Exception as e:
                logger.warning(f"No se pudo cargar {model_name}: {e}")
                continue
        
        if _embedding_model is None:
            raise RuntimeError("No se pudo cargar ningún modelo de embeddings")
        
        _initialized = True
        logger.info("✓ Clientes GCP inicializados correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando clientes GCP: {e}")
        raise


def get_db():
    """Obtiene el cliente de Firestore (inicializa si es necesario)."""
    _initialize_clients()
    return _db


def get_embedding_model():
    """Obtiene el modelo de embeddings (inicializa si es necesario)."""
    _initialize_clients()
    return _embedding_model



def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcula similitud coseno entre dos vectores usando numpy optimizado."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:  # Evitar división por cero
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))



def normalize_doc_name(name: str) -> str:
    """Normaliza nombre de documento para búsqueda."""
    name = re.sub(r'\.(docx|pdf|txt|md|csv)$', '', name, flags=re.IGNORECASE)
    name = name.lower()
    name = re.sub(r'[_\-\(\)\[\]]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


_docs_cache: Dict[str, Any] = {}
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 300


def get_documents_metadata(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Obtiene metadata de todos los documentos con cache."""
    import time
    global _docs_cache, _cache_timestamp
    
    current_time = time.time()
    if not force_refresh and _docs_cache and (current_time - _cache_timestamp) < CACHE_TTL_SECONDS:
        return list(_docs_cache.values())
    
    try:
        db = get_db()
        docs_ref = db.collection(COLLECTION_NAME)
        all_docs = list(docs_ref.stream())
        
        _docs_cache = {}
        for doc in all_docs:
            doc_data = doc.to_dict()
            doc_data['_firestore_id'] = doc.id
            _docs_cache[doc.id] = doc_data
        
        _cache_timestamp = current_time
        logger.info(f"Cache de documentos actualizado: {len(_docs_cache)} docs")
        return list(_docs_cache.values())
    except Exception as e:
        logger.error(f"Error obteniendo documentos: {e}")
        return list(_docs_cache.values()) if _docs_cache else []



def search_documents(
    query: str,
    document_name: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> Dict[str, Any]:
    """
    Busca información en documentos indexados usando búsqueda vectorial simple.
    
    Args:
        query: Consulta del usuario en lenguaje natural
        document_name: (Opcional) Filtrar por nombre de documento específico
        top_k: Número de resultados a retornar
        similarity_threshold: Umbral mínimo de similitud coseno
    
    Returns:
        Dict con status, contextos encontrados y texto formateado
    """
    try:
        logger.info(f"🔎 Búsqueda RAG: '{query}' | doc_filter: '{document_name}'")


        try:
            model = get_embedding_model()
            query_embeddings = model.get_embeddings([query])
            query_vector = query_embeddings[0].values
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return {"ok": False, "status": "Error", "message": f"Error en embedding: {e}"}
        

        all_docs = get_documents_metadata()
        
        if not all_docs:
            return {"ok": False, "status": "No hay documentos", "message": "La colección está vacía"}
        
        target_doc_ids = []
        
        if document_name:
            norm_search = normalize_doc_name(document_name)
            search_tokens = set(norm_search.split())
            
            for doc_data in all_docs:
                d_name = doc_data.get("doc_name", "")
                norm_doc = normalize_doc_name(d_name)
                
                if norm_search in norm_doc or norm_doc in norm_search:
                    target_doc_ids.append(doc_data['_firestore_id'])
                    continue
                    
                doc_tokens = set(norm_doc.split())
                common_tokens = search_tokens.intersection(doc_tokens)
                if common_tokens and (len(common_tokens) / len(search_tokens) >= 0.5):
                    target_doc_ids.append(doc_data['_firestore_id'])

            if not target_doc_ids:
                available_docs = [d.get('doc_name', 'Unknown') for d in all_docs]
                return {
                    "ok": False, 
                    "status": f"Documento no encontrado: '{document_name}'",
                    "message": f"Documentos disponibles: {available_docs}"
                }
        else:
            target_doc_ids = [d['_firestore_id'] for d in all_docs]
        
        logger.info(f"   Buscando en {len(target_doc_ids)} documento(s)")
        

        candidates: List[Dict[str, Any]] = []
        db = get_db()
        
        for doc_id in target_doc_ids:
            doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
            doc_metadata = doc_ref.get().to_dict()
            
            if not doc_metadata:
                continue
                
            chunks = list(doc_ref.collection("chunks").stream())
            
            for chunk_doc in chunks:
                chunk_data = chunk_doc.to_dict()
                if "embedding" not in chunk_data or "text" not in chunk_data:
                    continue
                
                chunk_text = chunk_data.get("text", "")
                chunk_embedding = chunk_data["embedding"]
                similarity = cosine_similarity(query_vector, chunk_embedding)
                
                if similarity >= similarity_threshold:
                    candidates.append({
                        "doc_id": doc_id,
                        "doc_name": doc_metadata.get("doc_name", "Unknown"),
                        "chunk_id": chunk_data.get("chunk_id", chunk_doc.id),
                        "chunk_index": chunk_data.get("chunk_index", 0),
                        "text": chunk_text,
                        "similarity_score": similarity,
                        "gcs_uri": doc_metadata.get("gcs_uri"),
                        "file_type": doc_metadata.get("file_type", "?"),
                        "firestore_path": f"{COLLECTION_NAME}/{doc_id}/chunks/{chunk_doc.id}"
                    })
        
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        final_results = candidates[:top_k]
        
        logger.info(f"   Resultados encontrados: {len(final_results)}")
        
        if not final_results:
            return {
                "ok": True,
                "status": "Sin coincidencias",
                "message": "No se encontraron fragmentos relevantes para la consulta.",
                "contexts": [],
                "contexts_text": ""
            }


        try:
            db = get_db()
            batch = db.batch()
            for result in final_results[:10]:  # Limitar batch
                chunk_ref = db.collection(COLLECTION_NAME).document(
                    result["doc_id"]
                ).collection("chunks").document(result["chunk_id"])
                batch.update(chunk_ref, {
                    "access_count": firestore.Increment(1),
                    "last_accessed": firestore.SERVER_TIMESTAMP
                })
            batch.commit()
        except Exception as e:
            logger.warning(f"Error actualizando métricas: {e}")
        

        contexts_text = "\n\n---\n\n".join([
            f"📄 [{r['doc_name']}] (Chunk {r['chunk_index']}, Score: {r['similarity_score']:.3f})\n{r['text']}"
            for r in final_results
        ])
        
        return {
            "ok": True,
            "status": f"Se encontraron {len(final_results)} contextos relevantes",
            "query": query,
            "documents_searched": len(target_doc_ids),
            "candidates_found": len(candidates),
            "contexts": final_results,
            "contexts_text": contexts_text
        }

    except Exception as e:
        logger.error(f"Error en búsqueda RAG: {e}")
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error en búsqueda: {str(e)}",
            "traceback": traceback.format_exc()
        }


def list_available_documents() -> Dict[str, Any]:
    """Lista todos los documentos indexados con su metadata."""
    try:
        docs = get_documents_metadata(force_refresh=False)
        documents = []
        for d in docs:
            documents.append({
                "doc_name": d.get("doc_name", "Unknown"),
                "doc_id": d.get("doc_id", d.get("_firestore_id", "?")),
                "type": d.get("file_type", "?"),
                "created_at": str(d.get("created_at", "?"))
            })
        
        return {
            "ok": True, 
            "total_documents": len(documents),
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listando documentos: {e}")
        return {"ok": False, "error": str(e)}


def get_document_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas agregadas de la base de conocimiento.
    """
    try:
        docs = get_documents_metadata(force_refresh=True)
        
        total_docs = len(docs)
        total_chunks = sum(d.get("total_chunks", 0) for d in docs)
        total_chars = sum(d.get("total_characters", 0) for d in docs)
        
        by_type = {}
        for d in docs:
            ftype = d.get("file_type", "OTHER")
            by_type[ftype] = by_type.get(ftype, 0) + 1
        
        return {
            "ok": True,
            "stats": {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "total_characters": total_chars,
                "estimated_words": total_chars // 5,  # Aproximación
                "documents_by_type": by_type
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {"ok": False, "error": str(e)}



search_rag_tool = FunctionTool(search_documents)
list_documents_tool = FunctionTool(list_available_documents)
stats_tool = FunctionTool(get_document_stats)