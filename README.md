# Agente Institucional UTEM

Sistema de análisis de documentos académicos de la Universidad Tecnológica Metropolitana usando inteligencia artificial.

## ¿Qué hace?

Este proyecto permite:
- **Consultar documentos** - Buscar información en informes PDC (Proyectos de Desarrollo de Carrera)
- **Generar reportes PDF** - Crear informes formales con formato institucional
- **Consultar datos de matrículas** - Obtener estadísticas de estudiantes desde BigQuery
- **Búsqueda web** - Encontrar información pública sobre la universidad

## Requisitos

- Python 3.12
- Cuenta de Google Cloud con acceso a:
  - Firestore (base de datos vectorial)
  - Vertex AI (modelo de lenguaje)
  - BigQuery (datos de matrículas)
  - Cloud Storage (almacenamiento de archivos)

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd agent-utem
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install poetry
   poetry install
   ```

4. **Configurar credenciales**
   ```bash
   gcloud auth application-default login
   ```

5. **Configurar variables de entorno**

   Crear archivo `.env`:
   ```
   FIRESTORE_PROJECT_ID=tu-proyecto
   FIRESTORE_DATABASE_ID=(default)
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

## Uso

### Ejecutar localmente

```bash
adk run my_agent_utem
```

### Desplegar en Cloud Run

```bash
cd deployment
python deploy.py
```

## Estructura del Proyecto

```
agent-utem/
├── my_agent_utem/
│   ├── agent.py          # Agente principal
│   ├── prompts.py        # Instrucciones de los agentes
│   ├── agents/           # Sub-agentes especializados
│   │   ├── bq_agent.py       # Consultas BigQuery
│   │   ├── rag_agent.py      # Búsqueda en documentos
│   │   └── reportes_agent.py # Generación de PDF
│   └── tools/            # Herramientas
│       ├── query_rag.py          # Búsqueda vectorial
│       ├── generate_pdf_report.py # Generador de PDF
│       └── upload_to_storage.py  # Subida a GCS
├── deployment/           # Scripts de despliegue
└── pyproject.toml        # Dependencias
```

## Ejemplos de uso

Una vez ejecutando el agente, puedes hacer consultas como:

- "¿Cuántos estudiantes hay matriculados en Ingeniería Civil?"
- "Lista los documentos disponibles"
- "¿Cuáles son las actividades logradas de Ciencia de Datos?"
- "Genera un reporte PDF del informe de Ingeniería Industrial"

## Licencia

Proyecto interno de la Universidad Tecnológica Metropolitana.
