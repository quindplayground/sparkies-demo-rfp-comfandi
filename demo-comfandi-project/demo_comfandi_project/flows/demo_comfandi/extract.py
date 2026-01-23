"""Extract module for demo_comfandi data flow."""

from pyspark.sql import DataFrame, SparkSession
from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)

@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
) -> DataFrame:
    """Extract data from source table OR file path.
    """
    # 1. Intentamos leer la configuración de 'path' (ruta de archivo)
    # Usamos .get() por si la clave no existe en el archivo de config
    input_config = vars_instance.vars.input
    source_path = input_config.get("path") 
    source_table_id = input_config.get("table_id")

    # --- CASO A: LECTURA DE ARCHIVO (Dinámico desde Web) ---
    if source_path:
        logger.info(
            f"📂 Detectado modo Archivo. Leyendo desde: {source_path}",
            extra={"attributes": {"source_path": source_path}}
        )
        
        # Leemos CSV (puedes agregar lógica para parquet/excel aquí si quieres)
        extracted_data = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(source_path)

    # --- CASO B: LECTURA DE TABLA (Legacy / Default) ---
    elif source_table_id:
        logger.info(
            f"🏗️ Detectado modo Tabla. Leyendo tabla: {source_table_id}",
            extra={"attributes": {"source_table": source_table_id}}
        )
        extracted_data = spark.table(source_table_id)
        
    else:
        raise ValueError("❌ Error en Configuración: No se definió ni 'path' ni 'table_id' en input.")

    logger.info("Data extraction completed")
    return extracted_data
