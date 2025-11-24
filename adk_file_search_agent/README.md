# ADK File Search Agent

This is a standard ADK Agent that integrates Gemini API File Search (Semantic Retriever).

## Structure

-   `agent.py`: Defines the `file_search_agent` using `LlmAgent`.
-   `tools/file_search_tool.py`: Implements the Gemini Corpus API logic and exposes ADK `FunctionTool`s.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file:
    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

## Running the Agent

You can run the agent using the ADK runner or the included snippet in `agent.py`:

```bash
python agent.py
```

Or if you have the ADK CLI installed and configured:

```bash
adk run agent:file_search_agent
```

## Capabilities

The agent has tools to:
1.  `create_store(name)`: Create a Gemini Corpus.
2.  `upload_file(path)`: Upload a PDF/Text file to the Corpus (automatically chunked and indexed).
3.  `query_store(query)`: Search the Corpus for relevant passages.

The agent is instructed to use these tools to answer questions based on the `/mnt/data/Informe Avance 2025 PDC Ing civil Biomédica.pdf` file (or other files you upload).
