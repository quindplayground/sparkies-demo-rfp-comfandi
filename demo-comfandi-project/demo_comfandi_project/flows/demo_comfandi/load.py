"""Load module for demo_comfandi data flow."""

from pyspark.sql import DataFrame, SparkSession
from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)

@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
) -> None:
    # 1. Obtenemos configuración
    output_config = vars_instance.vars.output
    target_table_id = output_config.get("table_id")
    target_path = output_config.get("path") # <--- Nueva variable inyectada dinámicamente
    
    num_partitions = vars_instance.vars.num_partitions.min_global

    destination = target_path if target_path else target_table_id

    logger.info(
        f"Loading data to: {destination}",
        extra={
            "attributes": {
                "job_id": job_id,
                "destination": destination,
                "type": "file" if target_path else "table"
            }
        },
    )

    data_to_load = transformed_data
    
    # Coalesce(1) es vital para que salga UN solo archivo CSV descargable
    if target_path:
        data_to_load = data_to_load.coalesce(1)
    elif num_partitions:
        data_to_load = data_to_load.repartition(num_partitions)

    # --- LÓGICA DE GUARDADO ---
    writer = data_to_load.write.mode("overwrite")

    if target_path:
        # MODO ARCHIVO (Para la Web App)
        writer.option("header", "true").csv(target_path)
    elif target_table_id:
        # MODO TABLA (Legacy)
        writer.option("overwriteSchema", "true").saveAsTable(target_table_id)
    else:
        logger.warning("No output destination defined (neither path nor table_id)")

    logger.info("Data load completed")
