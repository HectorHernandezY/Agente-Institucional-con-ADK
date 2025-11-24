from google.adk.agents import LlmAgent
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

bq_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

bq_universidad_agent = LlmAgent(
    name="bq_universidad_agent",
    description="Consultas Universidad (BigQuery). Tabla autorizada: muruna-utem-project.datos_simulados_utem.datos_utem_test",
    model="gemini-2.5-flash",
    tools=[
        BigQueryToolset(
            bigquery_tool_config=bq_config
        )
    ]
)
