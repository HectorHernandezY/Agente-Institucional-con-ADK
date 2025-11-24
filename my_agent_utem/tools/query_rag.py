from __future__ import annotations
import os
import re
import numpy as np
from typing import Any, Optional
import traceback
import json

from google.cloud import firestore
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel, GenerationConfig
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

try:
    generative_model = GenerativeModel("gemini-2.0-flash-exp")
except:
    generative_model = GenerativeModel("gemini-1.5-flash")


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calcula similitud coseno entre dos vectores"""
    a = np.array(vec1)
    b = np.array(vec2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def normalize_doc_name(name: str) -> str:
    """Normaliza nombre de documento para búsqueda flexible"""
    name = re.sub(r'\.(docx|pdf|txt)$', '', name, flags=re.IGNORECASE)
    name = name.lower()
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def expand_query(query: str) -> list[str]:
    """Genera variaciones de la consulta para mejorar la recuperación."""
    try:
        prompt = f"""Genera 3 variaciones de búsqueda diferentes para la siguiente consulta de usuario. 
        El objetivo es encontrar información relevante en documentos corporativos o académicos.
        Solo devuelve las variaciones separadas por saltos de línea, sin numeración ni texto extra.
        
        Consulta: {query}"""
        
        response = generative_model.generate_content(prompt)
        variations = [line.strip() for line in response.text.split('\n') if line.strip()]
        return variations[:3]
    except Exception as e:
        print(f"Error en expansión de query: {e}")
        return [query]


def rerank_candidates(query: str, candidates: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
    """Re-ordena los candidatos usando el LLM para evaluar relevancia."""
    if not candidates:
        return []
    
    try:
        # Preparar contexto para el LLM
        candidates_text = ""
        for i, c in enumerate(candidates):
            candidates_text += f"ID: {i}\nTexto: {c['text'][:500]}...\n\n"
            
        prompt = f"""Evalúa la relevancia de los siguientes fragmentos de texto para responder a la consulta: "{query}".
        Asigna un puntaje de 0 a 10 a cada fragmento, donde 10 es altamente relevante y contiene la respuesta exacta, y 0 es irrelevante.
        
        Fragmentos:
        {candidates_text}
        
        Devuelve SOLO un objeto JSON válido con el formato:
        {{"scores": {{ "0": 8, "1": 3, ... }} }}
        """
        
        response = generative_model.generate_content(
            prompt, 
            generation_config=GenerationConfig(response_mime_type="application/json")
        )
        
        result = json.loads(response.text)
        scores = result.get("scores", {})
        
        reranked = []
        for i, c in enumerate(candidates):
            score = scores.get(str(i), 0)
            c["rerank_score"] = score
            # Combinar score vectorial original con score del LLM (peso alto al LLM)
            c["final_score"] = (c["similarity_score"] * 0.3) + (score / 10 * 0.5)
            if score > 1: # Filtrar irrelevantes (más permisivo)
                reranked.append(c)
                
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked[:top_n]
    except Exception as e:
        print(f"Error en re-ranking: {e}")
        return candidates[:top_n] # Fallback a los top_n iniciales si hay error


def search_documents(
    query: str,
    document_name: Optional[str] = None,
    top_k: int = 15, # Aumentado para traer más candidatos al re-ranker
    similarity_threshold: float = 0.45
) -> dict[str, Any]:
    """
    Busca información en los documentos indexados usando Hybrid Search y Re-ranking.
    """
    try:
        # 1. Expansión de Query (Opcional, para keyword search o vector avg)
        # Por ahora usamos la query original para vector search principal para rapidez,
        # pero podríamos usar variaciones si la precisión es baja.
        
        # 2. Generar embedding de la query
        query_embeddings = embedding_model.get_embeddings([query])
        query_vector = query_embeddings[0].values
        
        # 3. Obtener documentos
        docs_ref = db.collection("rag_vectores2")
        all_docs = list(docs_ref.stream())
        
        if not all_docs:
            return {"ok": False, "status": "No hay documentos", "message": "Colección vacía"}
        
        # 4. Filtrar por documento
        target_doc_ids = []
        if document_name:
            normalized_search = normalize_doc_name(document_name)
            for doc in all_docs:
                doc_name = doc.to_dict().get("doc_name", "")
                if normalized_search in normalize_doc_name(doc_name):
                    target_doc_ids.append(doc.id)
            if not target_doc_ids:
                return {"ok": False, "status": f"No encontrado: {document_name}"}
        else:
            target_doc_ids = [doc.id for doc in all_docs]
        
        # 5. Recuperación Vectorial (Stage 1)
        candidates = []
        
        for doc_id in target_doc_ids:
            doc_ref = db.collection("rag_vectores2").document(doc_id)
            doc_metadata = doc_ref.get().to_dict()
            chunks = list(doc_ref.collection("chunks").stream())
            
            for chunk_doc in chunks:
                chunk_data = chunk_doc.to_dict()
                if "embedding" not in chunk_data or "text" not in chunk_data:
                    continue
                
                similarity = cosine_similarity(query_vector, chunk_data["embedding"])
                
                if similarity >= similarity_threshold:
                    candidates.append({
                        "doc_id": doc_id,
                        "doc_name": doc_metadata.get("doc_name", "Unknown"),
                        "chunk_id": chunk_data.get("chunk_id"),
                        "chunk_index": chunk_data.get("chunk_index"),
                        "text": chunk_data.get("text"),
                        "similarity_score": similarity,
                        "gcs_uri": doc_metadata.get("gcs_uri"),
                        "firestore_path": f"rag_vectores2/{doc_id}/chunks/{chunk_doc.id}"
                    })
        
        # Ordenar por similitud vectorial inicial
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Tomar top candidatos para re-ranking (ej. top 20)
        initial_candidates = candidates[:20]
        
        if not initial_candidates:
             return {
                "ok": True,
                "status": "No se encontraron coincidencias relevantes",
                "contexts": [],
                "contexts_text": ""
            }

        # 6. Re-ranking con LLM (Stage 2)
        # Solo aplicamos re-ranking si tenemos candidatos
        final_results = rerank_candidates(query, initial_candidates, top_n=5)
        
        # 7. Actualizar métricas (opcional, solo para los finales)
        if final_results:
            batch = db.batch()
            for result in final_results:
                chunk_ref = db.collection("rag_vectores2").document(result["doc_id"]).collection("chunks").document(result["chunk_id"])
                batch.update(chunk_ref, {
                    "access_count": firestore.Increment(1),
                    "last_accessed": firestore.SERVER_TIMESTAMP
                })
            batch.commit()
        
        # 8. Formatear
        contexts_text = "\n\n---\n\n".join([
            f"[{r['doc_name']} - Chunk {r['chunk_index']} (Score: {r.get('final_score', 0):.2f})]\n{r['text']}"
            for r in final_results
        ])
        
        return {
            "ok": True,
            "status": f"Se encontraron {len(final_results)} contextos altamente relevantes",
            "query": query,
            "contexts": final_results,
            "contexts_text": contexts_text
        }

    except Exception as e:
        return {
            "ok": False,
            "status": "Error",
            "message": f"Error RAG: {str(e)}",
            "traceback": traceback.format_exc()
        }


def list_available_documents() -> dict[str, Any]:
    """Lista documentos disponibles."""
    try:
        docs = db.collection("rag_vectores2").stream()
        documents = []
        for doc in docs:
            d = doc.to_dict()
            documents.append({
                "doc_name": d.get("doc_name", "Unknown"),
                "type": d.get("file_type", "?"),
                "chunks": d.get("total_chunks", 0)
            })
        return {"ok": True, "documents": documents}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Exportar tools
search_rag_tool = FunctionTool(search_documents)
list_documents_tool = FunctionTool(list_available_documents)
