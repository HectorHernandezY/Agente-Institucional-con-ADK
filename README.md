# Agent UTEM

Asistente inteligente para análisis de documentos UTEM con RAG (Retrieval-Augmented Generation) usando Google Cloud Platform.

## 🎯 Características

- **Indexación automática** de documentos (DOCX, TXT, MD, CSV) desde Google Cloud Storage
- **Búsqueda semántica** con embeddings vectoriales en Firestore
- **Análisis cuantitativo** de métricas, avances de proyectos y presupuestos
- **Agente LLM** con Gemini 2.5 Flash + Google ADK

## 🏗️ Arquitectura

```
GCS Bucket → Indexador → Firestore (vectores) → Query RAG → LLM Agent
```

## 📁 Estructura

```
agent-utem/
├── my_agent_utem/          # Módulo principal
│   ├── agent.py           # Configuración del agente
│   ├── prompts.py         # Sistema de prompts
│   └── tools/             # Herramientas RAG
│       ├── index_documents.py
│       ├── query_rag.py
│       └── read_rag.py
├── deployment/            # Scripts de deploy
│   └── deploy.py
└── scripts/               # Utilidades
    └── index_all_documents.py
```

## 🛠️ Herramientas del Agente

| Herramienta | Descripción |
|------------|-------------|
| `search_documents(query, document_name)` | Busca información en documentos indexados |
| `list_available_documents()` | Lista todos los documentos disponibles |
| `index_document_from_gcs(file_path)` | Indexa un nuevo documento desde GCS |

## 🧠 Capacidades del Agente

- ✅ Análisis cuantitativo (porcentajes, montos, cantidades)
- ✅ Clasificación de actividades (logradas/no logradas/no aplica)
- ✅ Cálculo automático de % de avance
- ✅ Respuestas estructuradas con datos explícitos
- ✅ Búsqueda vectorial por similitud semántica

## 📊 Configuración de Firestore

**Colección:** `rag_vectores`

**Esquema:**
```javascript
{
  chunk_id: "abc123_chunk_0",
  doc_name: "Informe 2025.docx",
  text: "...",
  embedding: [768 dimensiones],
  similarity_score: 0.85
}
```

## 🔐 Requisitos GCP

- **Project ID:** `muruna-utem-project`
- **Bucket:** `db_agent_utem`
- **APIs habilitadas:** Vertex AI, Firestore, Cloud Storage
- **Service Account:** `433491555173-compute@developer.gserviceaccount.com`

## 🐛 Troubleshooting

```bash
# Error: python-docx no instalado
pip install python-docx

# Error: Insufficient permissions
gcloud projects add-iam-policy-binding muruna-utem-project \
  --member="serviceAccount:YOUR-SA@..." \
  --role="roles/aiplatform.user"
```

## 📦 Dependencias Principales

- `google-adk` - Framework de agentes
- `google-cloud-aiplatform` - Vertex AI SDK
- `google-cloud-firestore` - Base de datos vectorial
- `python-docx` - Procesamiento de documentos
