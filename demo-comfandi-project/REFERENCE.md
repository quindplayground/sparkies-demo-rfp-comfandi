# Template Project

Plantilla de proyecto para procesamiento de datos utilizando PySpark y tecnologías de AWS. Este template proporciona una base sólida para construir proyectos de procesamiento de datos con patrones establecidos, manejo de errores robusto, y arquitectura escalable.

[[_TOC_]]

## Instalación

### Requisitos Previos

Este proyecto utiliza PySpark, por lo que requiere Java 17 para su funcionamiento. Asegúrate de tener instalado el SDK de Java 17 antes de proceder con la instalación del paquete.

#### Instalación de Java 17

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install openjdk-17-jdk
```

**macOS (con Homebrew):**
```bash
brew install openjdk@17
```

#### Configuración de JAVA_HOME

**Ubuntu/Debian:**
```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

**macOS:**
```bash
echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

### Instalación del Paquete

1. **Crear un entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate 
```

2. **Instalar el paquete en modo desarrollo:**
```bash
pip install -e demo-comfandi-project
```

3. **Verificar la instalación:**
```bash
python -c "import demo_comfandi_project; print(template_project.__version__)"
```

## Estructura del Proyecto

```
demo-comfandi-project/
├── demo_comfandi_project/                    # Paquete principal
│   ├── libs/                       # Librerías core del proyecto
│   │   ├── aws/                    # Utilidades para AWS (S3, DynamoDB)
│   │   ├── error_handler/          # Manejo de errores y logging
│   │   ├── iceberg/                # Utilidades para Apache Iceberg
│   │   ├── logging/                # Sistema de logging estandarizado
│   │   ├── resources/              # Gestión de recursos Spark
│   │   ├── runner/                 # Ejecutores de trabajos
│   │   └── validator_utils/        # Utilidades para crear validadores de parámetros
│   └── flows/                      # Flujos de procesamiento de datos
│       └── _template_flow/         # Template para crear nuevos flujos
│           ├── job.py              # Orquestador principal
│           ├── extract.py          # Extracción de datos
│           ├── transform.py        # Transformaciones
│           ├── load.py             # Carga de datos
│           ├── config/             # Configuración
│           └── steps/              # Pasos de transformación (opcional)
├── demo_comfandi_project_tests/              # Tests del proyecto
├── pyproject.toml                  # Configuración del proyecto
├── requirements.txt                 # Dependencias principales
└── test-requirements.txt           # Dependencias para testing
```

### Descripción de Componentes

- **`libs/`**: Contiene las librerías fundamentales del proyecto que proporcionan funcionalidades reutilizables como manejo de errores, logging, y utilidades para AWS e Iceberg.

- **`flows/`**: Contiene los flujos de procesamiento de datos. Cada flujo puede configurarse para diferentes patrones (ETL simple, incremental con CDC, etc.) según las necesidades del proyecto.

- **`demo_comfandi_project_tests/`**: Suite completa de tests unitarios que sigue las mejores prácticas de pytest.

## Documentación de Referencia

## Patrón de Flujos (`flows/`)

### Resumen del patrón principal (lo esencial para correr un flujo)
- Entrada: `SparkSession` + `VarsResource` con `[input]`, `[output]`, `[catalog]` y (si aplica) `[cdc_control]` y `[restart]`.
- Job único: `job(spark, vars_instance) -> Status`.
- Secuencia fija: extract -> transform -> load.
- Analytics: usa CDC con tags de Iceberg (salta si no hay cambios) y soporta restart.
- Salida: escribe/actualiza `output.table_id` y emite `Status` con tiempos y tipo (initial | incremental).

Todos los flujos de procesamiento en el proyecto siguen un patrón arquitectónico consistente basado en el patrón **ETL (Extract, Transform, Load)** con características específicas para procesamiento de datos a gran escala usando Apache Spark.

### Arquitectura General de Flujos

Los flujos deben organizarse siguiendo un **patrón medallón (Medallion Architecture)**, que estructura los datos en capas progresivas de calidad y refinamiento:

#### Patrón Medallón

El patrón medallón organiza los datos en tres capas principales:

1. **Bronze (Raw)**: Datos sin procesar desde fuentes externas
2. **Silver (Cleaned)**: Datos limpiados y validados
3. **Gold (Curated)**: Datos agregados y listos para consumo

#### Organización Flexible en el Template

El template proporciona un **flujo genérico configurable** que puede adaptarse a diferentes capas del patrón medallón según la configuración:

#### Configuración por Capa

**Bronze (Raw Data):**
- `use_cdc = false` - Extracción completa
- `check_changes = false` - Sin detección de cambios
- Modo: Overwrite (reemplaza todo)

**Silver (Cleaned Data):**
- `use_cdc = true` - Extracción incremental con CDC
- `check_changes = true` - Detecta cambios y omite si no hay
- Modo: Merge (actualiza/inserta)

**Gold (Curated Data):**
- `use_cdc = true` - Extracción incremental con CDC
- `check_changes = true` - Detecta cambios
- `enable_restart = true` - Soporte para restart
- Modo: Merge con transformaciones complejas

#### Ejemplo de Flujo Medallón

**Ejemplo: Procesamiento de datos de clientes**

```
Fuente Externa (SAP, API, etc.)
    ↓
[Stage Layer - Bronze]
  - extract.py: Extrae datos raw sin transformar
  - transform.py: Limpia y normaliza (elimina duplicados, corrige formatos)
  - load.py: Carga a tabla Iceberg `bronze.clientes`
    ↓
[Stage Layer - Silver]
  - extract.py: Lee desde `bronze.clientes`
  - transform.py: Validaciones, enriquecimiento básico, deduplicación
  - load.py: Carga a tabla Iceberg `silver.clientes`
    ↓
[Analytics Layer - Gold]
  - extract.py: Lee desde `silver.clientes` con CDC
  - transform.py: Agregaciones, cálculos de negocio, joins con otras fuentes
  - load.py: Carga a tabla Iceberg `gold.clientes_analytics`
    ↓
Consumo (Dashboards, APIs, ML Models)
```

**Estructura de directorios recomendada:**

```
flows/
├── _template_flow/           # Template para copiar
│   ├── job.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── config/
│   └── steps/
├── clientes_bronze/          # Datos raw (use_cdc=false)
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── job.py
│   └── config/
├── clientes_silver/          # Datos limpiados (use_cdc=true, check_changes=true)
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── job.py
│   └── config/
└── clientes_gold/            # Datos agregados (use_cdc=true, enable_restart=true)
    ├── extract.py
    ├── transform.py
    ├── load.py
    ├── job.py
    ├── config/
    └── steps/
```

### Crear un Nuevo Flujo desde el Template

El proyecto incluye templates completos para crear nuevos flujos. Estos templates proporcionan una estructura lista para implementar siguiendo las mejores prácticas del proyecto.

#### **Usar el Template de Flujo**

1. **Copiar el template:**
   ```bash
   cp -r flows/_template_flow flows/tu_flujo_nombre
   ```

2. **Renombrar componentes:**
   - Reemplazar `template_flow` con el nombre de tu flujo en todos los archivos
   - Actualizar nombres de funciones: `template_flow_job` → `tu_flujo_nombre_job`
   - Actualizar operaciones en logging: `EXECUTE_TEMPLATE_FLOW_JOB` → `EXECUTE_TU_FLUJO_NOMBRE_JOB`
   - Actualizar `component_name` en `config/default.toml`

3. **Configurar el flujo en `config/default.toml`:**
   - **Flujo simple (Bronze):** `use_cdc = false`, `check_changes = false`
   - **Flujo incremental (Silver):** `use_cdc = true`, `check_changes = true`
   - **Flujo con restart (Gold):** `use_cdc = true`, `check_changes = true`, `enable_restart = true`

4. **Implementar lógica específica:**
   - `extract.py`: Ajustar si es necesario (soporta full y CDC automáticamente)
   - `transform.py`: Agregar pasos de transformación según necesidades
   - `load.py`: Configurar `merge_keys` si usas modo incremental

5. **Ver README del template:**
   - Ver `flows/_template_flow/README.md` para instrucciones detalladas y ejemplos de configuración

#### **Estructura de los Templates**

Los templates incluyen:
- ✅ Estructura completa de archivos
- ✅ Patrones de logging estructurado
- ✅ Manejo de errores configurado
- ✅ Documentación en código
- ✅ Configuración de ejemplo
- ✅ README con instrucciones

### Estructura Común de Cada Flujo

Cada flujo individual sigue esta estructura estándar:

```
flows/
└── {component_name}/
    ├── job.py          # Orquestador principal
    ├── extract.py      # Extracción de datos (full o CDC)
    ├── transform.py    # Transformaciones
    ├── load.py         # Carga de datos (overwrite o merge)
    ├── config/
    │   └── default.toml # Configuración específica
    └── steps/          # Pasos de transformación (opcional)
        ├── step_XXX_*.py
        └── utils/
```

**Nota:** No hay separación por capas (stage/analytics). Cada flujo se configura independientemente según sus necesidades.

### Patrón de Job Principal (`job.py`)

Todos los jobs siguen el mismo patrón de ejecución:

#### **1. Inicialización y Configuración**
```python
def {component}_job(spark: SparkSession, vars_instance: VarsResource) -> Status:
    logger = get_logger(__name__)
    start_time = time.time()
    job_id = f"{component}_{int(start_time)}"
    
    # Logging de inicio con contexto completo
    logger.info("Starting {component} processing job", extra={
        "attributes": {
            "operation": "EXECUTE_{COMPONENT}_JOB",
            "job_id": job_id,
            "job_name": "{component}_job",
            "pipeline_stage": "{stage|analytics}",
            "component": "{component}",
            "input_table": vars_instance.vars.input.table_id,
            "output_table": vars_instance.vars.output.table_id,
            "status": "STARTED"
        }
    })
```

#### **2. Gestión de Estado y Restart (Analytics)**
```python
# Verificación de restart si está habilitado
if vars_instance.vars.restart.{component}:
    restart_result = restart_table(spark, vars_instance.vars.catalog, 
                                 vars_instance.vars.output.table_id, 
                                 vars_instance.vars.cdc_control.table_id)

# Verificación de primera ejecución
first_run = is_empty(spark, vars_instance.vars.output.table_id)

# Verificación de cambios (CDC) para analytics usando tagging strategy
if not first_run:
    changelog_manager = ChangelogManager(
        spark=spark,
        table_id=vars_instance.vars.input.table_id,
        tag_name=vars_instance.vars.last_snapshot_tag_name
    )
    
    # Verificar cambios usando estrategias de tagging
    has_changes = changelog_manager.get_changelog_table(
        changelog_strategy="iceberg_sp"  # o "date_filter"
    ).count() > 0
    
    if not has_changes:
        return Status(status_value="OK", message="No changes since last snapshot")
```

#### **3. Pipeline ETL Estándar**
```python
# EXTRACT
logger.info("Starting data extraction", extra={
    "attributes": {
        "operation": "EXECUTE_{COMPONENT}_JOB",
        "job_id": job_id,
        "step": "extract",
        "source_table": vars_instance.vars.input.table_id,
        "status": "IN_PROGRESS"
    }
})

extracted_data = extract(spark, vars_instance, first_run, error_args)

# TRANSFORM
logger.info("Starting data transformation", extra={
    "attributes": {
        "operation": "EXECUTE_{COMPONENT}_JOB",
        "job_id": job_id,
        "step": "transform",
        "status": "IN_PROGRESS"
    }
})

transformed_data = transform(job_id, spark, vars_instance, extracted_data, first_run)

# LOAD
logger.info("Starting data load", extra={
    "attributes": {
        "operation": "EXECUTE_{COMPONENT}_JOB",
        "job_id": job_id,
        "step": "load",
        "target_table": vars_instance.vars.output.table_id,
        "status": "IN_PROGRESS"
    }
})

load(spark, vars_instance, transformed_data, first_run)
```

#### **4. Finalización y Métricas**
```python
logger.info("{Component} processing job completed successfully", extra={
    "attributes": {
        "operation": "EXECUTE_{COMPONENT}_JOB",
        "job_id": job_id,
        "status": "DONE",
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "execution_type": "initial_load" if first_run else "incremental_load"
    }
})

return Status(status_value="OK", message="{Component} job completed successfully")
```

### Características Técnicas del Patrón

#### **Logging Estructurado Consistente**
- **Atributos estandarizados**: operation, job_id, step, status, execution_time_ms
- **Estados uniformes**: STARTED, IN_PROGRESS, DONE, FAILED, SKIPPED
- **Contexto completo**: input_table, output_table, control_table, execution_type
- **Métricas de rendimiento**: execution_time_ms para monitoreo

#### **Manejo de Errores Robusto**
- **Error Args**: Configuración consistente para manejo de errores
- **Extractores**: "full" para stage, "changelog" para analytics
- **Recuperación**: Soporte para restart de tablas
- **Logging de errores**: Información detallada para debugging

#### **Gestión de Estado Avanzada**
- **CDC Integration**: Detección automática de cambios usando tagging strategy
- **First Run Detection**: Identificación de carga inicial vs incremental
- **Restart Capability**: Capacidad de reiniciar procesamiento
- **Skip Logic**: Omisión inteligente cuando no hay cambios
- **Tagging Strategy**: Uso de tags de Iceberg para seguimiento preciso de snapshots
- **Multiple CDC Strategies**: Soporte para diferentes estrategias de changelog (iceberg_sp, date_filter)

#### **Configuración Flexible**
- **VarsResource**: Configuración centralizada por componente
- **Environment-specific**: Configuraciones por entorno (dev, test, prod)
- **Table Configuration**: Configuración específica de tablas de entrada y salida
- **Error Paths**: Rutas configurables para manejo de errores

### Configuraciones de Flujo

Los flujos se configuran mediante opciones en `config/default.toml`:

| Aspecto | Simple ETL | Incremental ETL | Incremental con Restart |
|---------|------------|-----------------|-------------------------|
| **use_cdc** | false | true | true |
| **check_changes** | false | true | true |
| **enable_restart** | false | false | true |
| **Procesamiento** | Completo | Incremental | Incremental |
| **Modo de carga** | Overwrite | Merge | Merge |
| **Detección cambios** | No | Sí | Sí |
| **Snapshots/Tags** | No | Sí | Sí |
| **Uso típico** | Bronze | Silver | Gold |

### Ejemplo de Configuración (`config/default.toml`)

**Configuración para flujo simple (Bronze):**
```toml
component_name = "bronze_customers"
use_cdc = false
check_changes = false
enable_restart = false

[input]
table_id = "source_table_name"
error_path = "/path/to/errors"

[output]
table_id = "target_table_name"
```

**Configuración para flujo incremental (Silver/Gold):**
```toml
component_name = "silver_customers"
use_cdc = true
check_changes = true
enable_restart = false  # true para Gold

[input]
table_id = "source_table_name"
error_path = "/path/to/errors"

[output]
table_id = "target_table_name"
merge_keys = ["id"]  # Claves para merge

# Configuración CDC
last_snapshot_tag_name = "silver_customers_last_snapshot"
cdc_strategy = "iceberg_sp"  # o "date_filter"

[restart]  # Solo si enable_restart = true
silver_customers = false
```

### Integración con Runner

Los flujos se integran con el sistema Runner para orquestación:

```python
from demo_comfandi_project.libs.runner import JobRunner
from demo_comfandi_project.libs.runner.types import JobDefinition, Status

# Definición de jobs de flujos
job_definitions = [
    JobDefinition(
        name="stage_secuencias",
        job=secuencias_job,
        args={"spark": spark, "vars_instance": vars_instance},
        depends_on=[]
    ),
    JobDefinition(
        name="analytics_comercial",
        job=commercial_iceberg_job,
        args={"spark": spark, "vars_instance": vars_instance},
        depends_on=["stage_secuencias"]
    )
]

# Ejecución con Runner
runner = JobRunner(job_definitions)
result = runner.run("analytics_comercial", executor="sequential")
```

Este patrón arquitectónico garantiza **consistencia**, **mantenibilidad** y **escalabilidad** en todos los flujos de procesamiento de datos del proyecto.
### Core Libraries (`libs/`)

Las librerías core proporcionan las funcionalidades fundamentales del proyecto. Cada módulo está diseñado para ser reutilizable y seguir patrones consistentes.

#### Módulos Principales

- **[AWS Utilities](libs/aws/)** - Utilidades para integración con servicios de AWS
- **[Error Handler](libs/error_handler/)** - Sistema robusto de manejo de errores
- **[Iceberg Utilities](libs/iceberg/)** - Herramientas para Apache Iceberg
- **[Logging](libs/logging/)** - Sistema de logging estandarizado
- **[Resources](libs/resources/)** - Gestión de recursos Spark
- **[Runner](libs/runner/)** - Ejecutores de trabajos
- **[Validator Utils](libs/validator_utils/)** - Utilidades para crear validadores de parámetros

### AWS Utilities (`libs/aws/`)

El módulo AWS proporciona utilidades para interactuar con servicios de Amazon Web Services, específicamente S3 y DynamoDB.

#### S3 Utilities (`libs/aws/s3/`)

**Nombre:** `demo_comfandi_project.libs.aws.s3` — módulo

**Propósito:** Proporciona funcionalidades para descarga de archivos y carpetas desde Amazon S3, optimizado para entornos de procesamiento de datos con Spark.

**Responsabilidades y alcance:**
- Descarga recursiva de carpetas completas desde S3
- Manejo automático de estructura de directorios locales
- Logging estructurado de operaciones de descarga
- Gestión robusta de errores de AWS

No hace:
- Subida de archivos a S3
- Operaciones de streaming de datos
- Gestión de permisos o autenticación

**Conceptos clave:**
- **S3 Bucket**: Contenedor de objetos en Amazon S3
- **S3 Prefix**: Prefijo de ruta dentro del bucket para filtrar objetos
- **Paginación**: Procesamiento por lotes de objetos grandes

**Arquitectura y flujo:**
Entradas → Validación de parámetros → Conexión S3 → Paginación de objetos → Descarga por lotes → Logging de resultados

Punto de inicio: `download_s3_folder_to_local()`

**API pública:**
- `download_s3_folder_to_local(s3_bucket: str, s3_prefix: str, local_dest_path: Path | str) -> None`: Descarga carpeta completa desde S3

**Entradas y salidas:**
Entradas:
- `s3_bucket` (str): Nombre del bucket S3, debe existir y ser accesible
- `s3_prefix` (str): Prefijo de ruta en el bucket, puede ser vacío para todo el bucket
- `local_dest_path` (Path | str): Ruta local de destino, se crea automáticamente si no existe

Salidas:
- Ninguna (función void)
- Efectos colaterales: Archivos descargados en sistema local, logs estructurados

**Configuración:**
- Credenciales AWS: Via AWS CLI, variables de entorno, o IAM roles
- Región AWS: Configurada en perfil AWS o variables de entorno
- Límites de rate: Controlados por AWS SDK (boto3)

**Uso básico:**
```python
from demo_comfandi_project.libs.aws.s3 import download_s3_folder_to_local
from pathlib import Path

# Descarga básica de carpeta
download_s3_folder_to_local(
    s3_bucket="mi-bucket-datos",
    s3_prefix="raw/daily/",
    local_dest_path=Path("./data/downloaded")
)
```

**Ejemplos adicionales:**
```python
# Descarga de todo el bucket (prefijo vacío)
download_s3_folder_to_local(
    s3_bucket="mi-bucket-datos",
    s3_prefix="",
    local_dest_path="./data/full_bucket"
)

# Descarga con ruta absoluta
download_s3_folder_to_local(
    s3_bucket="mi-bucket-datos",
    s3_prefix="processed/2024/",
    local_dest_path="/tmp/spark_data"
)
```

**Errores y manejo de fallos:**
- **ClientError**: Errores de AWS (permisos, bucket no encontrado) → Se relanza con logging
- **Exception**: Errores inesperados → Se relanza con logging completo
- **Bucket vacío**: Warning log si no se encuentran archivos

**Rendimiento y escala:**
- Usa paginación automática para buckets grandes
- Descarga por lotes optimizada por boto3
- No hay límites de tamaño de bucket
- Recomendado para buckets con < 1M objetos para mejor rendimiento

**Concurrencia e idempotencia:**
- No es thread-safe (usa boto3 client local)
- Idempotente: Sobrescribe directorio destino si existe
- Recomendado para uso en procesos únicos

**Seguridad y cumplimiento:**
- Requiere credenciales AWS válidas
- Respeta políticas IAM del usuario/rol
- No maneja datos sensibles directamente
- Logs pueden contener nombres de archivos (no contenido)

**Dependencias:**
- Internas: `demo_comfandi_project.libs.logging` para logging estructurado
- Externas: `boto3`, `botocore` para operaciones AWS

**Puntos de extensión:**
- No aplica (módulo funcional simple)

**Casos borde y limitaciones:**
- Bucket no existe → ClientError con logging
- Sin permisos de lectura → ClientError con logging  
- Prefijo inexistente → Warning log, descarga vacía
- Espacio insuficiente → Exception del sistema operativo

**Logging y observabilidad:**
- Logs clave: "Downloaded files from s3", "Files not found in s3", "Error on AWS S3"
- Métricas: `files_downloaded`, `s3_bucket`, `s3_prefix`, `local_dest_path`
- Niveles: INFO (éxito), WARNING (sin archivos), ERROR (fallos)

**Pruebas:**
- Unitarias: Mock de boto3 client, validación de parámetros
- Integración: Descarga real con bucket de prueba
- Casos: Bucket vacío, prefijo inexistente, errores de permisos

**Versionado y compatibilidad:**
- Compatible con boto3 >= 1.26.0
- Sin cambios breaking conocidos

**FAQ:**
- **¿Puedo descargar archivos individuales?** — No, solo carpetas completas
- **¿Qué pasa si el directorio destino existe?** — Se elimina y recrea completamente
- **¿Hay límite de tamaño?** — No, pero buckets muy grandes pueden ser lentos
- **¿Funciona con S3 compatible?** — Sí, si usa API compatible con AWS S3

**Referencias:**
- Código: `demo_comfandi_project/libs/aws/s3/download_utils.py`
- AWS S3: https://docs.aws.amazon.com/s3/

#### DynamoDB Utilities (`libs/aws/dynamodb/`)

**Nombre:** `demo_comfandi_project.libs.aws.dynamodb` — módulo

**Propósito:** Proporciona un sistema completo para operaciones con Amazon DynamoDB, incluyendo carga masiva de datos usando Spark, gestión de tablas y operaciones de escritura/eliminación optimizadas.

**Responsabilidades y alcance:**
- Carga masiva de datos a DynamoDB usando Spark RDDs
- Operaciones de escritura y eliminación por lotes
- Gestión de tablas (truncate, restart)
- Manejo robusto de throttling y reintentos
- Control de tamaño de items para límites de DynamoDB
- Compresión de datos para optimización de espacio

No hace:
- Creación de tablas DynamoDB
- Operaciones de consulta (query/scan)
- Gestión de índices secundarios

**Conceptos clave:**
- **DynamoDBLoader**: Clase principal para carga masiva usando Spark
- **Handlers**: Implementaciones especializadas para diferentes tipos de operaciones
- **BatchWriter**: Operaciones por lotes optimizadas de DynamoDB
- **Throttling**: Limitaciones de rate de DynamoDB con manejo automático
- **Item Size Limit**: Límite de 400KB por item en DynamoDB

**Arquitectura y flujo:**
DataFrames Spark → Validación → Handler Factory → Procesamiento por particiones → BatchWriter → DynamoDB

Punto de inicio: `DynamoDBLoader.load()`

**API pública:**
- `DynamoDBLoader(job_id, vars_instance, handler_factory)`: Constructor del loader
- `DynamoDBLoader.load(dataframes, first_run, write_handler, delete_handler)`: Carga datos
- `truncate_table(dynamodb_table) -> bool`: Trunca tabla eliminando todos los items
- `restart_table(table_name, region) -> bool`: Reinicia tabla completamente

**Entradas y salidas:**
Entradas:
- `dataframes` (InputDynamoDBLoaderDataFrame): Diccionario con DataFrames de escritura y eliminación
- `first_run` (bool): Indica si es primera ejecución (solo escritura)
- `write_handler` (str): Handler para escritura ("portfolio_writer", "comercial_writer")
- `delete_handler` (str): Handler para eliminación ("delete")

Salidas:
- Ninguna (operaciones void)
- Efectos colaterales: Items escritos/eliminados en DynamoDB, logs estructurados

**Configuración:**
- `output.region` (str): Región AWS de la tabla DynamoDB
- `output.table_name` (str): Nombre de la tabla objetivo
- `output.item_size_limit` (int): Límite de tamaño de item en bytes (default: 389120)
- Credenciales AWS: Via IAM roles, variables de entorno, o AWS CLI

**Uso básico:**
```python
from demo_comfandi_project.libs.aws.dynamodb.loader import DynamoDBLoader
from demo_comfandi_project.libs.resources import VarsResource

# Inicializar loader
loader = DynamoDBLoader(
    job_id="job_123",
    vars_instance=vars_resource
)

# Cargar datos
loader.load(
    dataframes={
        "data_to_write": write_df,
        "data_to_delete": delete_df
    },
    first_run=False,
    write_handler="portfolio_writer",
    delete_handler="delete"
)
```

**Ejemplos adicionales:**
```python
# Primera ejecución (solo escritura)
loader.load(
    dataframes={
        "data_to_write": initial_data_df,
        "data_to_delete": spark.createDataFrame([], schema)  # DataFrame vacío
    },
    first_run=True,
    write_handler="comercial_writer"
)

# Truncar tabla manualmente
from demo_comfandi_project.libs.aws.dynamodb.truncate_table import truncate_table
from demo_comfandi_project.libs.aws.dynamodb.loader.utils import get_table

table = get_table("us-east-1", "mi_tabla")
success = truncate_table(table)

# Reiniciar tabla
from demo_comfandi_project.libs.aws.dynamodb.restart_table import restart_table
success = restart_table("mi_tabla", "us-east-1")
```

**Errores y manejo de fallos:**
- **ThrottlingException**: Manejo automático con backoff exponencial (5 reintentos)
- **ValidationError**: Error de esquema de DataFrames → Se relanza con logging
- **ClientError**: Errores de AWS → Se relanza con logging detallado
- **Item Size Exceeded**: Items muy grandes → Error log, item omitido

**Rendimiento y escala:**
- Procesamiento por particiones de Spark para escalabilidad horizontal
- BatchWriter optimizado para throughput máximo
- Compresión gzip para campos grandes (nivel 9)
- Recomendado para cargas > 10K items

**Concurrencia e idempotencia:**
- Thread-safe por partición (cada partición usa su propio BatchWriter)
- Idempotente: Reescritura de items existentes
- Manejo de concurrencia por AWS DynamoDB

**Seguridad y cumplimiento:**
- Requiere credenciales AWS con permisos DynamoDB
- Respeta políticas IAM del rol/usuario
- Logs contienen claves de items (no datos completos)
- Compresión de datos sensibles en campo "productos"

**Dependencias:**
- Internas: `demo_comfandi_project.libs.logging`, `demo_comfandi_project.libs.resources`
- Externas: `boto3`, `mypy_boto3_dynamodb`, `pyspark`

**Puntos de extensión:**
- **HandlerFactory**: Registro de nuevos handlers personalizados
- **DynamoDBOperationHandler**: Implementación de operaciones custom
- **Handlers disponibles**: `portfolio_writer`, `comercial_writer`, `delete`

```python
# Ejemplo de handler personalizado
class CustomWriteHandler(DynamoDBOperationHandler):
    def process_item(self, bw: BatchWriter, item: dict[str, Any]) -> bool:
        # Lógica personalizada de escritura
        bw.put_item(Item=item)
        return True

# Registrar en factory
HandlerFactory.map_handler["custom_writer"] = CustomWriteHandler
```

**Casos borde y limitaciones:**
- Items > 400KB → Error log, item omitido
- Tabla no existe → ClientError con logging
- Sin permisos → ClientError con logging
- Partición vacía → Skip silencioso
- Throttling excesivo → Fallo después de 5 reintentos

**Logging y observabilidad:**
- Logs clave: "Loading items to DynamoDB", "Items loaded to DynamoDB", "Successfully processed items"
- Métricas: `job_id`, `table_name`, `item_size_limit`, `count`, `count_error`, `partition_id`
- Niveles: INFO (éxito), WARNING (throttling), ERROR (fallos)

**Pruebas:**
- Unitarias: Mock de DynamoDB, validación de handlers
- Integración: Carga real con tabla de prueba
- Casos: Items grandes, throttling, tablas inexistentes

**Versionado y compatibilidad:**
- Compatible con boto3 >= 1.26.0
- Compatible con PySpark >= 3.0.0
- Sin cambios breaking conocidos

**FAQ:**
- **¿Cómo manejo items muy grandes?** — Se omiten con error log, considera particionar datos
- **¿Puedo usar handlers personalizados?** — Sí, extiende DynamoDBOperationHandler y regístralo
- **¿Qué pasa con throttling?** — Manejo automático con backoff exponencial
- **¿Es thread-safe?** — Sí, cada partición de Spark es independiente

**Referencias:**
- Código: `demo_comfandi_project/libs/aws/dynamodb/loader/loader.py`
- Handlers: `template_project/libs/aws/dynamodb/loader/handlers/`
- AWS DynamoDB: https://docs.aws.amazon.com/dynamodb/

### Error Handler (`libs/error_handler/`)

**Nombre:** `demo_comfandi_project.libs.error_handler` — módulo

**Propósito:** Proporciona un sistema robusto y flexible para el manejo de errores en el proyecto, incluyendo captura automática de excepciones, extracción de datos contextuales y escritura de logs de error estructurados.

**Responsabilidades y alcance:**
- Captura automática de excepciones con decorador `@handle_errors`
- Extracción de datos contextuales usando extractores especializados
- Escritura de logs de error estructurados en múltiples formatos
- Manejo programático de errores con ErrorHandler
- Configuración flexible de comportamiento de errores
- Soporte para diferentes estrategias de extracción y escritura

No hace:
- Manejo de errores de infraestructura (red, disco, memoria)
- Recuperación automática de datos corruptos
- Notificaciones externas (email, Slack, etc.)

**Conceptos clave:**
- **ErrorHandler**: Clase principal para manejo programático de errores
- **Extractores**: Componentes que recuperan datos contextuales cuando ocurre un error
- **Writers**: Componentes que escriben información de error en diferentes formatos
- **ErrorData**: Modelo que representa datos de error estructurados
- **ErrorArgs**: Configuración del comportamiento del handler
- **fail_fast**: Control de si continuar o fallar en caso de error

**Arquitectura y flujo:**
Función decorada → Captura de excepción → Extracción de datos contextuales → Creación de ErrorData → Escritura de log → Decisión de continuar/fallar

Punto de inicio: `@handle_errors` decorador o `ErrorHandler.handle_error()`

**API pública:**
- `@handle_errors`: Decorador para manejo automático de errores
- `ErrorHandler(error_writer, row_data_extractor)`: Constructor del handler
- `ErrorHandler.handle_error(spark, error, source, step)`: Maneja excepción específica
- `get_error_handler(spark, error_path, extractor, writer)`: Factory para crear handlers

**Entradas y salidas:**
Entradas:
- `error_args` (dict | ErrorArgs): Configuración del manejo de errores
- `spark` (SparkSession): Sesión de Spark para operaciones de datos
- `error_path` (str): Ruta donde escribir logs de error
- `extractor` (str): Tipo de extractor ("changelog", "full")
- `writer` (str): Tipo de writer ("spark_csv")
- `fail_fast` (bool): Si fallar inmediatamente o continuar

Salidas:
- Ninguna (operaciones void)
- Efectos colaterales: Logs de error escritos, logging estructurado

**Configuración:**
- `extractor`: "changelog" (datos de muestra) o "full" (metadatos completos)
- `writer`: "spark_csv" (formato CSV optimizado para Spark)
- `fail_fast`: True (fallar inmediatamente) o False (continuar procesamiento)
- `error_path`: Ruta de destino para logs de error
- `step`: Nombre del paso donde ocurrió el error (auto-detectado si no se especifica)

**Uso básico:**
```python
from demo_comfandi_project.libs.error_handler import handle_errors

@handle_errors
def process_data(spark, df, error_args=None):
    # Tu lógica de procesamiento aquí
    return processed_df

# Uso con configuración de error
result = process_data(
    spark=spark_session,
    df=input_dataframe,
    error_args={
        "spark": spark_session,
        "error_path": "/path/to/error/logs",
        "extractor": "changelog",
        "writer": "spark_csv",
        "fail_fast": True,
        "step": "data_processing",
        "source": "input_table"
    }
)
```

**Ejemplos adicionales:**
```python
# Manejo programático de errores
from demo_comfandi_project.libs.error_handler.handler import get_error_handler

error_handler = get_error_handler(
    spark=spark_session,
    error_path="/path/to/error/logs",
    extractor="full",  # Metadatos completos
    writer="spark_csv"
)

try:
    result = risky_operation()
except Exception as e:
    error_handler.handle_error(
        spark=spark_session,
        error=e,
        source="input_dataframe",
        step="data_transformation"
    )

# Decorador sin configuración (solo logging)
@handle_errors
def simple_function():
    # Si falla, solo se registra el error sin procesamiento adicional
    return complex_operation()
```

**Errores y manejo de fallos:**
- **Exception**: Cualquier excepción → Capturada y procesada según configuración
- **ValidationError**: Error de configuración → Se relanza con logging
- **DataFrame vacío**: Fuente sin datos → Warning log, datos vacíos extraídos
- **Error de escritura**: Fallo al escribir log → Error log, excepción relanzada

**Rendimiento y escala:**
- Decorador tiene overhead mínimo (< 1ms por llamada)
- Extractores optimizados para tablas grandes (límite de 10 registros)
- Writers usan Spark para escritura eficiente
- Recomendado para pipelines con < 1000 errores por ejecución

**Concurrencia e idempotencia:**
- Thread-safe por diseño (cada llamada es independiente)
- Idempotente: Múltiples errores en mismo paso generan logs separados
- Writers usan modo "append" para evitar conflictos

**Seguridad y cumplimiento:**
- No expone datos sensibles en logs (solo metadatos y muestras)
- Logs estructurados para auditoría
- Configuración de rutas de error para cumplimiento
- Validación automática de tipos de datos

**Dependencias:**
- Internas: `demo_comfandi_project.libs.logging` para logging estructurado
- Externas: `pyspark`, `pydantic` para validación de modelos

**Puntos de extensión:**
- **Extractores personalizados**: Implementar `RowDataExtractorInterface`
- **Writers personalizados**: Implementar `ErrorWriterInterface`
- **Registro en MAP_EXTRACTORS/MAP_WRITERS**: Para nuevos tipos

```python
# Ejemplo de extractor personalizado
class CustomExtractor(RowDataExtractorInterface):
    def extract_row_data(self, spark, source):
        # Lógica personalizada de extracción
        return json.dumps({"custom": "data"})

# Registrar en factory
MAP_EXTRACTORS["custom"] = CustomExtractor

# Ejemplo de writer personalizado
class CustomWriter(ErrorWriterInterface):
    def write_error(self, error_data):
        # Lógica personalizada de escritura
        pass

MAP_WRITERS["custom"] = CustomWriter
```

**Casos borde y limitaciones:**
- Fuente inexistente → Warning log, datos vacíos extraídos
- Error en proceso de logging → Error log, excepción original relanzada
- DataFrame muy grande → Solo primeros 10 registros extraídos
- Ruta de error inaccesible → Error de escritura, fallo del proceso

**Logging y observabilidad:**
- Logs clave: "Step completed successfully", "Step failed, writing error log", "Error in stage"
- Métricas: `step`, `source`, `state`, `error_path`, `result`
- Niveles: INFO (éxito), WARNING (datos vacíos), ERROR (fallos)

**Pruebas:**
- Unitarias: Mock de extractores/writers, validación de modelos
- Integración: Manejo real de errores con Spark
- Casos: DataFrames vacíos, fuentes inexistentes, errores de escritura

**Versionado y compatibilidad:**
- Compatible con PySpark >= 3.0.0
- Compatible con Pydantic >= 2.0.0
- Sin cambios breaking conocidos

**FAQ:**
- **¿Cómo cambio el formato de salida?** — Implementa nuevo writer y regístralo
- **¿Puedo extraer más datos contextuales?** — Implementa extractor personalizado
- **¿Qué pasa si falla la escritura?** — Se relanza la excepción original
- **¿Es thread-safe?** — Sí, cada operación es independiente

**Referencias:**
- Código: `demo_comfandi_project/libs/error_handler/decorator.py`
- Handlers: `template_project/libs/error_handler/handler.py`
- Modelos: `template_project/libs/error_handler/models.py`

### Iceberg Utilities (`libs/iceberg/`)

**Nombre:** `demo_comfandi_project.libs.iceberg` — módulo

**Propósito:** Proporciona herramientas especializadas para trabajar con Apache Iceberg, incluyendo operaciones de tabla, carga de datos, mantenimiento automático y funcionalidades CDC (Change Data Capture) con estrategias de tagging.

**Responsabilidades y alcance:**
- Operaciones básicas de tabla Iceberg (verificación de vacío, reinicio)
- Carga optimizada de datos con configuración avanzada
- Mantenimiento automático diario y semanal
- Sistema CDC con estrategias de tagging para seguimiento de cambios
- Gestión de snapshots y tags de Iceberg
- Optimización automática de archivos y manifiestos

No hace:
- Creación de catálogos Iceberg
- Configuración de conectores externos
- Migración de datos entre formatos

**Conceptos clave:**
- **Apache Iceberg**: Formato de tabla para data lakes con capacidades ACID
- **Snapshots**: Puntos en el tiempo de una tabla Iceberg
- **Tags**: Etiquetas que marcan snapshots específicos para seguimiento
- **CDC**: Change Data Capture para detectar cambios incrementales
- **Manifests**: Archivos que contienen metadatos de archivos de datos
- **Orphan Files**: Archivos que ya no son referenciados por ningún snapshot

**Arquitectura y flujo:**
Operación solicitada → Validación de tabla → Ejecución de operación Iceberg → Mantenimiento automático → Logging de resultados

Punto de inicio: Funciones utilitarias (`is_empty`, `load_overwrite`, `restart_table`) o CDC (`ChangelogManager`)

**API pública:**
- `is_empty(spark, table_id) -> bool`: Verifica si tabla está vacía
- `load_overwrite(spark, dataframe, table_id, ...)`: Carga datos con overwrite
- `restart_table(spark, iceberg_catalog, table_id, ...) -> bool`: Reinicia tabla completamente
- `run_daily_maintenance(spark, catalog, table_id, ...)`: Mantenimiento diario automático
- `run_weekly_maintenance(spark, catalog, table_id, ...)`: Mantenimiento semanal automático
- `ChangelogManager(spark, table_id, tag_name)`: Gestor de CDC con tagging
- `SnapshotManager(spark, table_id)`: Gestor de snapshots y tags

**Entradas y salidas:**
Entradas:
- `spark` (SparkSession): Sesión de Spark para operaciones Iceberg
- `table_id` (str): Identificador de tabla en formato `catalog.schema.table`
- `dataframe` (DataFrame): Datos a cargar (para load_overwrite)
- `iceberg_catalog` (str): Nombre del catálogo Iceberg
- `tag_name` (str): Nombre del tag para seguimiento CDC

Salidas:
- `bool`: True si operación exitosa (para funciones booleanas)
- `DataFrame`: Tabla de changelog (para CDC)
- `None`: Operaciones void con efectos colaterales

**Configuración:**
- `partition_by` (list[str]): Columnas para particionar tabla
- `location` (str): Ubicación personalizada de tabla
- `num_partitions` (int): Número de particiones para reparticionar
- `expire_snapshots` (bool): Si expirar snapshots antiguos (default: True)
- `remove_orphan_files` (bool): Si remover archivos huérfanos (default: True)
- `num_snapshots_to_retain` (int): Snapshots a retener (default: 5)
- `days_to_retain` (int): Días para retener archivos (default: 1)

**Uso básico:**
```python
from demo_comfandi_project.libs.iceberg.utils import load_overwrite, is_empty, restart_table

# Verificar si tabla está vacía
if is_empty(spark, "database.schema.my_table"):
    print("Tabla está vacía")

# Cargar datos con overwrite
load_overwrite(
    spark=spark,
    dataframe=my_dataframe,
    table_id="database.schema.my_table",
    iceberg_catalog="my_catalog",
    partition_by=["year", "month"],
    num_partitions=10
)

# Reiniciar tabla completamente
success = restart_table(
    spark=spark,
    iceberg_catalog="my_catalog",
    table_id="database.schema.my_table",
    cdc_control_table_id="database.schema.control_table"
)
```

**Ejemplos adicionales:**
```python
# Mantenimiento automático
from demo_comfandi_project.libs.iceberg.utils import run_daily_maintenance, run_weekly_maintenance

# Mantenimiento diario (expirar snapshots, limpiar archivos huérfanos)
run_daily_maintenance(
    spark=spark,
    catalog="my_catalog",
    table_id="database.schema.my_table",
    num_snapshots_to_retain=2,
    orphan_files_older_than_days=1
)

# Mantenimiento semanal (optimizar manifiestos y archivos)
run_weekly_maintenance(
    spark=spark,
    catalog="my_catalog",
    table_id="database.schema.my_table",
    target_file_size_mb=256
)

# CDC con tagging strategy
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy import ChangelogManager

changelog_manager = ChangelogManager(
    spark=spark,
    table_id="catalog.schema.table_name",
    tag_name="last_snapshot_tag"
)

# Obtener changelog con estrategia iceberg_sp
changelog_df = changelog_manager.get_changelog_table(
    changelog_strategy="iceberg_sp",
    exclude_cols=["metadata_column", "dt"]
)

# Commit de cambios
changelog_manager.commit_changes()
```

**Errores y manejo de fallos:**
- **InvalidTableFormatError**: Formato de table_id inválido → Se relanza con mensaje descriptivo
- **SnapshotManagerException**: Error en operaciones de snapshot → Se relanza con logging
- **CommitChangesError**: Fallo al establecer tag → Se relanza con contexto
- **Tabla inexistente**: Error de Iceberg → Se relanza con logging detallado

**Rendimiento y escala:**
- Operaciones optimizadas para tablas grandes (> 1TB)
- Mantenimiento automático para evitar degradación de rendimiento
- CDC eficiente usando tags en lugar de escaneo completo
- Soporte para particionado automático
- Recomendado para workloads con alta frecuencia de escritura

**Concurrencia e idempotencia:**
- Operaciones ACID de Iceberg garantizan consistencia
- Idempotente: Múltiples ejecuciones de mantenimiento son seguras
- Tags permiten seguimiento preciso de cambios
- Soporte para escritura concurrente

**Seguridad y cumplimiento:**
- Operaciones respetan permisos de Iceberg
- Logs estructurados para auditoría
- Control de retención de datos configurable
- Validación de formato de identificadores

**Dependencias:**
- Internas: `demo_comfandi_project.libs.logging` para logging estructurado
- Externas: `pyspark` con soporte Iceberg, Apache Iceberg >= 1.0.0

**Puntos de extensión:**
- **Estrategias CDC personalizadas**: Implementar `IChangelogStrategy`
- **Registro en StrategyFactory**: Para nuevas estrategias de changelog
- **Configuración de mantenimiento**: Parámetros personalizables por tabla

```python
# Ejemplo de estrategia CDC personalizada
class CustomChangelogStrategy(IChangelogStrategy):
    def create_changelog(self, *args, **kwargs) -> DataFrame:
        # Lógica personalizada de changelog
        return self.spark.sql("SELECT * FROM custom_changelog_view")

# Registrar en factory
StrategyFactory.MAP_STRATEGY["custom"] = CustomChangelogStrategy
```

**Casos borde y limitaciones:**
- Tabla no existe → Error de Iceberg con logging
- Tag inexistente → Warning log, procesamiento desde inicio
- Snapshot corrupto → Error de Iceberg, requiere intervención manual
- Catálogo inaccesible → Error de conexión con logging

**Logging y observabilidad:**
- Logs clave: "Starting get_changelog_table", "Daily maintenance completed", "Last snapshot tag set"
- Métricas: `table_id`, `tag_name`, `snapshot_id`, `operation`, `state`
- Niveles: INFO (operaciones), WARNING (tags inexistentes), ERROR (fallos)

**Pruebas:**
- Unitarias: Mock de Spark SQL, validación de parámetros
- Integración: Operaciones reales con tablas Iceberg de prueba
- Casos: Tablas vacías, tags inexistentes, snapshots corruptos

**Versionado y compatibilidad:**
- Compatible con Apache Iceberg >= 1.0.0
- Compatible con PySpark >= 3.0.0
- Sin cambios breaking conocidos

**FAQ:**
- **¿Cómo optimizo una tabla grande?** — Usa mantenimiento semanal con parámetros ajustados
- **¿Puedo usar CDC sin tags?** — No, el sistema está diseñado para usar tagging strategy
- **¿Qué pasa si falla el mantenimiento?** — Se registra error pero no afecta operaciones principales
- **¿Es thread-safe?** — Sí, Iceberg garantiza consistencia ACID

**Referencias:**
- Código: `demo_comfandi_project/libs/iceberg/utils/`
- CDC: `template_project/libs/iceberg/cdc_with_tagging_strategy/`
- Apache Iceberg: https://iceberg.apache.org/

### Logging Utilities (`libs/logging/`)

**Nombre:** `demo_comfandi_project.libs.logging` — módulo

**Propósito:** Proporciona un sistema de logging robusto y estandarizado con integración OpenTelemetry y Spark Log4J, diseñado para cumplir con los estándares de observabilidad del proyecto.

**Responsabilidades y alcance:**
- Integración completa entre Python logging y Spark Log4J
- Formateo estructurado en JSON compatible con OpenTelemetry
- Sanitización automática de datos sensibles en logs
- Configuración centralizada de niveles y handlers
- Soporte para contexto de tracing distribuido
- Prevención de recursión y loops infinitos

No hace:
- Almacenamiento persistente de logs
- Configuración de sistemas de monitoreo externos
- Análisis o agregación de logs

**Conceptos clave:**
- **OpenTelemetry**: Estándar de observabilidad para logs, métricas y traces
- **Log4J**: Sistema de logging de Java usado por Spark
- **Log4JProxyHandler**: Handler que proxea mensajes Python a Log4J de Spark
- **OtelStyleJsonFormatter**: Formateador que produce JSON compatible con OpenTelemetry
- **NoRecursiveFilter**: Filtro para prevenir recursión en handlers
- **Context**: Proveedor de contexto para datos de tracing distribuido

**Arquitectura y flujo:**
Entradas → Logger Factory → Configuración OpenTelemetry → Handler Log4J → Sanitización → Formateo JSON → Salida estructurada

Punto de inicio: `get_logger()`

**API pública:**
- `get_logger(name, log_level, capture_spark_logs, service_name, service_version, schema_url, context, force_reconfigure) -> logging.Logger`: Factory principal para crear loggers
- `Logger(spark, name, additional_handlers, service_name, service_version, schema_url, context)`: Clase principal de logger
- `Logger.add_handler(handler) -> Self`: Agrega handlers personalizados
- `Logger.log_level(log_level) -> Self`: Establece nivel de logging
- `Logger.get_logger() -> logging.Logger`: Obtiene instancia del logger
- `OtelStyleJsonFormatter(default_attributes, context, service_name, service_version, schema_url, add_spark_prefix)`: Formateador OpenTelemetry
- `Log4JProxyHandler(spark_session, max_msg_length)`: Handler proxy para Spark Log4J
- `NoRecursiveFilter(name)`: Filtro anti-recursión

**Entradas y salidas:**
Entradas:
- `name` (str | None): Nombre del logger, default "template_project"
- `log_level` (Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] | None): Nivel de logging, default "WARN"
- `capture_spark_logs` (bool): Si capturar logs de Spark, default True
- `service_name` (str | None): Nombre del servicio OpenTelemetry, default "template-project"
- `service_version` (str | None): Versión del servicio, default versión del paquete
- `schema_url` (str | None): URL del esquema OpenTelemetry, default "https://opentelemetry.io/schemas/1.0.0"
- `context` (Context | None): Contexto para datos de tracing
- `force_reconfigure` (bool): Forzar reconfiguración, default False

Salidas:
- `logging.Logger`: Instancia configurada del logger Python
- Efectos colaterales: Configuración de Spark Log4J, handlers agregados al root logger

**Configuración:**
- `LOG_LEVEL` (env var): Nivel de logging por defecto, default "WARN"
- `HOSTNAME` (env var): Nombre del host para atributos de recurso
- `AWS_REGION` (env var): Región AWS para atributos de cloud
- `LoggingDefaults`: Enumeración con valores por defecto del sistema

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.logging import get_logger

logger = get_logger(name="mi_modulo", log_level="INFO")
logger.info("Mensaje de prueba")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.logging import get_logger, Logger
from demo_comfandi_project.libs.resources.spark_resource import SparkResource

# Logger básico con Spark
spark = SparkResource()
logger = get_logger(
    name="mi_modulo",
    log_level="INFO",
    capture_spark_logs=True
)

# Logger con configuración OpenTelemetry avanzada
logger = get_logger(
    name="mi_modulo",
    log_level="INFO",
    service_name="mi-servicio",
    service_version="1.0.0",
    context=mi_contexto
)

# Uso del logger con atributos estructurados
logger.info("Data processing started", extra={
    "attributes": {
        "operation": "DATA_PROCESSING",
        "state": "IN_PROGRESS",
        "records_count": 1000,
        "source_table": "input_table",
        "target_table": "output_table"
    }
})
```

**Ejemplos adicionales:**
```python
# Logger con handler personalizado
from demo_comfandi_project.libs.logging import Logger, OtelStyleJsonFormatter
from logging import FileHandler

spark = SparkResource()
logger_instance = Logger(spark, name="custom_logger")
file_handler = FileHandler("custom.log")
logger_instance.add_handler(file_handler)
logger = logger_instance.get_logger()

# Logger sin Spark (solo Python)
logger = get_logger(
    name="standalone_logger",
    log_level="DEBUG",
    capture_spark_logs=False
)

# Logger con contexto de tracing
from demo_comfandi_project.libs.context import Context

context = Context()
context.set("opel/trace_id", "abc123")
context.set("opel/span_id", "def456")

logger = get_logger(
    name="traced_logger",
    context=context
)
```

**Errores y manejo de fallos:**
- **ValueError**: SparkSession inválida en Log4JProxyHandler → Se valida tipo de entrada
- **Exception**: Errores en emisión de logs → Se manejan con handleError() estándar
- **Recursión**: Loops infinitos de logging → Se previenen con NoRecursiveFilter
- **Datos sensibles**: Exposición accidental → Se sanitizan automáticamente con patrones regex
- **Mensajes largos**: Overflow de buffers → Se truncan con sufijo "... (truncated)"

**Rendimiento y escala:**
- Formateo JSON eficiente con serialización nativa
- Filtrado optimizado con validaciones tempranas
- Sanitización con regex compiladas para mejor rendimiento
- Truncado de mensajes para prevenir memory leaks
- Manejo de errores robusto sin impacto en performance

**Concurrencia e idempotencia:**
- Thread-safe: Usa logging estándar de Python (thread-safe por diseño)
- Process-safe: Cada proceso tiene su propia configuración de logging
- Idempotente: Múltiples llamadas a get_logger() con mismos parámetros producen configuración consistente
- Singleton de Spark: Reutiliza sesión Spark existente cuando es posible

**Seguridad y cumplimiento:**
- **Datos sensibles**: Sanitización automática de contraseñas, tokens, emails, tarjetas de crédito
- **Redacción**: Patrones regex para detectar y redactar información sensible
- **Validación**: Validación de entrada en filtros y handlers
- **Contexto seguro**: Manejo seguro de nombres de logger con sanitización
- **Auditoría**: Logs estructurados facilitan auditoría y compliance

**Dependencias:**
- Internas: `demo_comfandi_project.libs.resources.spark_resource`, `demo_comfandi_project.libs.context`
- Externas: `pyspark` (SparkSession), `logging` (sistema estándar Python)

**Puntos de extensión:**
- **Handlers personalizados**: Agregar handlers adicionales con `Logger.add_handler()`
- **Formateadores personalizados**: Extender `OtelStyleJsonFormatter` para formatos específicos
- **Filtros personalizados**: Crear filtros que extiendan `logging.Filter`
- **Contexto personalizado**: Implementar proveedores de contexto que extiendan `Context`

```python
# Ejemplo de extensión: Handler personalizado
from logging import Handler
from demo_comfandi_project.libs.logging import Logger

class CustomHandler(Handler):
    def emit(self, record):
        # Lógica personalizada de logging
        pass

spark = SparkResource()
logger_instance = Logger(spark)
logger_instance.add_handler(CustomHandler())
logger = logger_instance.get_logger()
```

**Casos borde y limitaciones:**
- **Sesión Spark cerrada**: Log4JProxyHandler falla si SparkSession no está activa
- **Nombres de logger inválidos**: Se sanitizan automáticamente a caracteres seguros
- **Mensajes muy largos**: Se truncan a 10,000 caracteres por defecto
- **Contexto faltante**: Se usa Context() vacío si no se proporciona
- **Recursión**: Se previene pero puede ocurrir con handlers mal configurados

**Logging y observabilidad:**
- **Logs clave**: Configuración de logger, errores de sanitización, warnings de reconfiguración
- **Métricas**: No emite métricas directamente, pero facilita observabilidad con formato estructurado
- **Atributos estándar**: service.name, service.version, host.name, process.pid, cloud.region
- **Tracing**: Integración con trace_id, span_id, trace_flags para correlación distribuida

**Pruebas:**
- **Unitarias**: Formateo JSON, sanitización de patrones, filtros anti-recursión
- **Integración**: Configuración con Spark, handlers Log4J, contexto OpenTelemetry
- **Fixtures**: Mock de SparkSession, Context de prueba, LogRecord sintético

```python
# Ejemplo de prueba unitaria
def test_otel_formatter():
    formatter = OtelStyleJsonFormatter(service_name="test-service")
    record = logging.LogRecord("test", logging.INFO, "test.py", 1, "test message", (), None)
    result = formatter.format(record)
    assert "test-service" in result
    assert "severity_text" in result
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en estructura JSON de OpenTelemetry
- **Compatibilidad**: Mantiene compatibilidad con logging estándar de Python
- **Migración**: Actualizaciones de esquema OpenTelemetry requieren actualización de schema_url

**FAQ:**
- **¿Por qué usar Log4JProxyHandler?** — Para integrar logs Python con el sistema de logging de Spark y mantener consistencia en entornos distribuidos
- **¿Cómo funciona la sanitización?** — Usa patrones regex predefinidos para detectar y redactar datos sensibles automáticamente
- **¿Es thread-safe?** — Sí, usa el sistema de logging estándar de Python que es thread-safe por diseño
- **¿Cómo configurar niveles?** — Usa el parámetro log_level o la variable de entorno LOG_LEVEL
- **¿Qué es el contexto OpenTelemetry?** — Permite correlacionar logs con traces distribuidos usando trace_id y span_id

**Referencias:**
- Código: `demo_comfandi_project/libs/logging/logger.py`
- Formateador: `template_project/libs/logging/formatter.py`
- Handler: `template_project/libs/logging/handler.py`
- Filtros: `template_project/libs/logging/filter.py`
- Configuración: `template_project/libs/logging/defaults.py`
- OpenTelemetry: https://opentelemetry.io/
- Spark Logging: https://spark.apache.org/docs/latest/configuration.html#logging

### Resources Utilities (`libs/resources/`)

**Nombre:** `demo_comfandi_project.libs.resources` — módulo

**Propósito:** Proporciona gestión centralizada de recursos del sistema, incluyendo sesiones de Spark con patrón singleton y configuración de variables usando Dynaconf con soporte multi-entorno.

**Responsabilidades y alcance:**
- Gestión singleton de SparkSession con soporte Hive
- Configuración multi-entorno usando Dynaconf
- Resolución de rutas y extracción de archivos ZIP en clusters Spark
- Validación de configuración con Dynaconf Validators
- Soporte para múltiples formatos de configuración (TOML, YAML, JSON, INI)

No hace:
- Gestión de conexiones a bases de datos
- Configuración de sistemas de monitoreo
- Gestión de credenciales o secretos

**Conceptos clave:**
- **SparkResource**: Gestor singleton de SparkSession con soporte Hive
- **VarsResource**: Wrapper para configuración Dynaconf multi-entorno
- **_VarsStore**: Almacén interno que gestiona múltiples instancias de configuración
- **ZipHandler**: Manejador de extracción ZIP y resolución de rutas para clusters Spark
- **Dynaconf**: Librería de configuración con soporte multi-entorno y validación
- **SparkFiles**: Sistema de Spark para distribución de archivos en clusters

**Arquitectura y flujo:**
Entradas → SparkResource/VarsResource → Configuración/Validación → Recursos gestionados → Acceso centralizado

Punto de inicio: `SparkResource()`, `get_vars_resource()`

**API pública:**
- `SparkResource(conf, new_session, enable_hive_support, session_log_level) -> SparkSession`: Gestor singleton de SparkSession
- `VarsResource(root, env, config_paths, validators)`: Wrapper para configuración Dynaconf
- `get_vars_resource(env, config_paths, validators) -> VarsResource`: Factory para crear VarsResource
- `ZipHandler(spark)`: Manejador de extracción ZIP y resolución de rutas
- `get_working_path(path, in_spark_cluster) -> str`: Función pública para resolver rutas

**Entradas y salidas:**
Entradas:
- `conf` (SparkConf | None): Configuración personalizada de Spark, default None
- `new_session` (bool): Si crear nueva sesión desde la existente, default False
- `enable_hive_support` (bool): Habilitar soporte Hive, default True
- `session_log_level` (str | None): Nivel de logging, default "WARN"
- `root` (str): Directorio raíz de configuración
- `env` (Literal["dev", "test", "prod"]): Entorno a cargar
- `config_paths` (str | list[str] | None): Rutas de configuración específicas
- `validators` (list[Validator] | None): Validadores Dynaconf

Salidas:
- `SparkSession`: Instancia singleton de SparkSession configurada
- `VarsResource`: Instancia de configuración multi-entorno
- `str`: Ruta resuelta y accesible

**Configuración:**
- `LOG_LEVEL` (env var): Nivel de logging por defecto para Spark, default "WARN"
- Formatos soportados: TOML, YAML, JSON, INI
- Entornos soportados: dev, test, prod
- Validadores Dynaconf para validación de configuración

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.resources import SparkResource, get_vars_resource

# Spark básico
spark = SparkResource()

# Configuración básica
vars_resource = get_vars_resource(env="dev", config_paths=["config/app.toml"])
```

**Uso básico:**
```python
from demo_comfandi_project.libs.resources import SparkResource, get_vars_resource
from pyspark import SparkConf
from dynaconf import Validator

# Spark con configuración personalizada
conf = SparkConf()
conf.set("spark.sql.adaptive.enabled", "true")
conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

spark = SparkResource(
    conf=conf,
    enable_hive_support=True,
    session_log_level="INFO"
)

# Configuración con validación
validators = [
    Validator("database.host", must_exist=True),
    Validator("spark.app_name", must_exist=True),
    Validator("log_level", is_in=["DEBUG", "INFO", "WARN", "ERROR"])
]

vars_resource = get_vars_resource(
    env="dev",
    config_paths=["config/parameters.toml"],
    validators=validators
)

# Acceder a configuración
database_host = vars_resource.vars.database.host
spark_app_name = vars_resource.vars.spark.app_name

# Usar Spark
df = spark.read.table("mi_tabla")
```

**Ejemplos adicionales:**
```python
# Nueva sesión Spark desde la existente
new_spark = SparkResource(new_session=True)

# Configuración manual
from demo_comfandi_project.libs.resources import VarsResource

vars_resource = VarsResource(
    root="/path/to/config",
    env="prod",
    config_paths=["config/prod.toml", "config/secrets.yaml"],
    validators=[Validator("api.key", must_exist=True)]
)

# Resolución de rutas con ZipHandler
from demo_comfandi_project.libs.resources.vars.zip_handler import get_working_path

# Ruta local
local_path = get_working_path("/path/to/config", in_spark_cluster=False)

# Ruta en cluster Spark
cluster_path = get_working_path("config.zip", in_spark_cluster=True)

# Ruta de módulo
module_path = get_working_path(template_project.libs, in_spark_cluster=True)
```

**Errores y manejo de fallos:**
- **ValueError**: Ruta de configuración no existe → Se valida existencia y tipo de directorio
- **FileNotFoundError**: Archivos de configuración no encontrados → Se busca recursivamente con extensiones permitidas
- **RuntimeError**: Error en configuración Dynaconf → Se captura y relanza con contexto
- **KeyError**: Configuración no encontrada en almacén → Se valida existencia antes de acceso
- **FileExistsError**: Error en extracción ZIP → Se maneja silenciosamente

**Rendimiento y escala:**
- Patrón singleton para SparkSession evita múltiples inicializaciones costosas
- Cache de rutas extraídas en ZipHandler para evitar re-extracciones
- Búsqueda recursiva optimizada de archivos de configuración
- Merge eficiente de múltiples archivos de configuración
- Reutilización de sesiones Spark existentes

**Concurrencia e idempotencia:**
- Thread-safe: SparkResource usa patrón singleton thread-safe
- Process-safe: Cada proceso tiene su propia instancia de SparkSession
- Idempotente: Múltiples llamadas a SparkResource() retornan la misma instancia
- Singleton: Una sola instancia de SparkSession por proceso

**Seguridad y cumplimiento:**
- **Validación de configuración**: Validadores Dynaconf para campos requeridos
- **Rutas seguras**: Validación de rutas de configuración antes de acceso
- **Archivos ZIP**: Extracción segura a directorios temporales
- **Entornos separados**: Configuraciones aisladas por entorno (dev/test/prod)
- **Auditoría**: Logging de configuración cargada y validaciones aplicadas

**Dependencias:**
- Internas: `demo_comfandi_project.libs.utils` para rutas de paquetes
- Externas: `pyspark` (SparkSession, SparkConf), `dynaconf` (Dynaconf, Validator)

**Puntos de extensión:**
- **Configuración personalizada**: Extender SparkConf con configuraciones específicas
- **Validadores personalizados**: Crear validadores Dynaconf específicos del dominio
- **Handlers de archivos**: Extender ZipHandler para otros formatos de archivo
- **Proveedores de configuración**: Implementar proveedores de configuración personalizados

```python
# Ejemplo de extensión: Configuración personalizada
from pyspark import SparkConf
from demo_comfandi_project.libs.resources import SparkResource

class CustomSparkResource(SparkResource):
    @staticmethod
    def _build_builder(enable_hive_support: bool, conf: SparkConf):
        builder = super()._build_builder(enable_hive_support, conf)
        # Configuraciones personalizadas
        builder.config("spark.sql.adaptive.enabled", "true")
        builder.config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        return builder
```

**Casos borde y limitaciones:**
- **Sesión Spark cerrada**: Acceso a SparkSession cerrada causa errores
- **Archivos ZIP corruptos**: Extracción falla con FileNotFoundError
- **Configuración faltante**: Validadores fallan si campos requeridos no existen
- **Rutas inexistentes**: get_working_path falla si archivo no se encuentra
- **Múltiples entornos**: Solo un entorno por instancia de VarsResource

**Logging y observabilidad:**
- **Logs clave**: Configuración de Spark cargada, archivos de configuración encontrados, validaciones aplicadas
- **Métricas**: No emite métricas directamente, pero facilita observabilidad con configuración centralizada
- **Atributos estándar**: Entorno cargado, archivos de configuración, validadores aplicados
- **Debugging**: Información detallada de rutas resueltas y configuraciones cargadas

**Pruebas:**
- **Unitarias**: Configuración de Spark, carga de configuración, validación de campos
- **Integración**: SparkSession con Hive, resolución de rutas en clusters, validación multi-entorno
- **Fixtures**: Mock de SparkSession, archivos de configuración de prueba, validadores sintéticos

```python
# Ejemplo de prueba unitaria
def test_spark_resource_singleton():
    spark1 = SparkResource()
    spark2 = SparkResource()
    assert spark1 is spark2  # Misma instancia singleton

def test_vars_resource_validation():
    validators = [Validator("required_field", must_exist=True)]
    vars_resource = get_vars_resource("dev", ["test_config.toml"], validators)
    assert vars_resource.vars.required_field is not None
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en API de Dynaconf o Spark
- **Compatibilidad**: Mantiene compatibilidad con versiones de Spark y Dynaconf
- **Migración**: Actualizaciones de configuración requieren validación de esquemas

**FAQ:**
- **¿Por qué usar singleton para Spark?** — Para evitar múltiples inicializaciones costosas y gestionar recursos eficientemente
- **¿Cómo funciona la configuración multi-entorno?** — Dynaconf carga configuraciones específicas por entorno con merge automático
- **¿Es thread-safe?** — Sí, SparkResource usa patrón singleton thread-safe y Dynaconf es thread-safe
- **¿Cómo validar configuración?** — Usa validadores Dynaconf para campos requeridos y tipos de datos
- **¿Qué formatos soporta?** — TOML (recomendado), YAML, JSON, INI con búsqueda recursiva

**Referencias:**
- Código: `demo_comfandi_project/libs/resources/spark_resource.py`
- Configuración: `template_project/libs/resources/vars/resource.py`
- ZIP Handler: `template_project/libs/resources/vars/zip_handler.py`
- Dynaconf: https://dynaconf.readthedocs.io/
- Spark Configuration: https://spark.apache.org/docs/latest/configuration.html

### Runner Utilities (`libs/runner/`)

**Nombre:** `demo_comfandi_project.libs.runner` — módulo

**Propósito:** Proporciona un sistema robusto para la ejecución de trabajos con resolución automática de dependencias y múltiples estrategias de ejecución (secuencial y paralela).

**Responsabilidades y alcance:**
- Resolución automática de dependencias entre trabajos
- Detección de dependencias circulares
- Validación de definiciones de trabajos con Pydantic
- Ejecución secuencial y paralela de trabajos
- Logging estructurado de ejecución y errores
- Manejo robusto de errores con traceback completo

No hace:
- Gestión de recursos del sistema (CPU, memoria)
- Persistencia de estado entre ejecuciones
- Distribución de trabajos en múltiples máquinas

**Conceptos clave:**
- **JobRunner**: Clase principal que ejecuta trabajos con resolución de dependencias
- **JobDefinition**: Definición de trabajo con nombre, función, argumentos y dependencias
- **Status**: Estado de proceso con códigos HTTP-like (OK, ERROR, etc.)
- **JobResult**: Resultado de ejecución de trabajo individual
- **SequentialExecutor**: Ejecutor que procesa trabajos uno después de otro
- **MultithreadExecutor**: Ejecutor que procesa trabajos en paralelo usando hilos
- **ExecutorFactory**: Factory para crear ejecutores por nombre

**Arquitectura y flujo:**
Entradas → JobRunner → Resolución de Dependencias → Ejecutor (Sequential/Parallel) → Ejecución de Trabajos → Agregación de Resultados → Status Final

Punto de inicio: `JobRunner(job_definitions)`

**API pública:**
- `JobRunner(job_definitions, executor_factory)`: Constructor principal del runner
- `JobRunner.run(jobs, executor, *args, **kwargs) -> Status`: Ejecuta trabajos con estrategia especificada
- `JobDefinition(name, job, args, depends_on)`: Define un trabajo individual
- `Status(status_value, message)`: Representa el estado de un proceso
- `JobResult(job_name, status)`: Almacena resultado de ejecución
- `SequentialExecutor()`: Ejecutor secuencial
- `MultithreadExecutor(max_workers)`: Ejecutor paralelo
- `ExecutorFactory()`: Factory para crear ejecutores

**Entradas y salidas:**
Entradas:
- `job_definitions` (Sequence[JobDefinition | dict[str, Any]]): Lista de definiciones de trabajos
- `executor_factory` (ExecutorFactory | None): Factory de ejecutores, default None
- `jobs` (list[str] | str): Nombres de trabajos a ejecutar
- `executor` (str): Tipo de ejecutor ("sequential" o "parallel"), default "parallel"
- `max_workers` (int | None): Número máximo de hilos para ejecutor paralelo

Salidas:
- `Status`: Estado agregado de la ejecución con código HTTP-like y mensaje
- Efectos colaterales: Logging estructurado, ejecución de trabajos definidos

**Configuración:**
- Ejecutores disponibles: "sequential", "parallel"
- Estados de Status: OK (200), CREATED (201), ACCEPTED (202), NOT CONTENT (204), BAD REQUEST (400), UNAUTHORIZED (401), FORBIDDEN (403), NOT FOUND (404), UNPROCESSABLE ENTITY (422), CONFLICT (409), ERROR (500)
- Validación automática con Pydantic para JobDefinition

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.runner import JobRunner
from demo_comfandi_project.libs.runner.types import JobDefinition, Status

def my_job(**kwargs) -> Status:
    return Status(status_value="OK", message="Job completed")

job_definitions = [
    JobDefinition(name="test", job=my_job, args={}, depends_on=[])
]

runner = JobRunner(job_definitions)
result = runner.run("test", executor="sequential")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.runner import JobRunner
from demo_comfandi_project.libs.runner.types import JobDefinition, Status

# Definir trabajos
def extract_data(**kwargs) -> Status:
    # Lógica de extracción
    return Status(status_value="OK", message="Data extracted successfully")

def transform_data(**kwargs) -> Status:
    # Lógica de transformación
    return Status(status_value="OK", message="Data transformed successfully")

def load_data(**kwargs) -> Status:
    # Lógica de carga
    return Status(status_value="OK", message="Data loaded successfully")

# Crear definiciones de trabajos
job_definitions = [
    JobDefinition(
        name="extract",
        job=extract_data,
        args={"source": "database.table1"},
        depends_on=[]
    ),
    JobDefinition(
        name="transform",
        job=transform_data,
        args={"input_table": "raw_data"},
        depends_on=["extract"]
    ),
    JobDefinition(
        name="load",
        job=load_data,
        args={"target_table": "processed_data"},
        depends_on=["transform"]
    )
]

# Crear runner
runner = JobRunner(job_definitions)

# Ejecutar trabajos secuencialmente
result = runner.run("load", executor="sequential")

# Ejecutar trabajos en paralelo (sin dependencias)
result = runner.run(["extract", "transform"], executor="parallel")
```

**Ejemplos adicionales:**
```python
# Definiciones como diccionarios
job_definitions = [
    {
        "name": "extract_data",
        "job": extract_function,
        "args": {"table": "source_table"},
        "depends_on": []
    },
    {
        "name": "process_data", 
        "job": process_function,
        "args": {"input": "raw_data"},
        "depends_on": ["extract_data"]
    }
]

runner = JobRunner(job_definitions)
result = runner.run("process_data", executor="sequential")

# Ejecutor paralelo con máximo de hilos
from demo_comfandi_project.libs.runner.executors import ExecutorFactory

factory = ExecutorFactory()
parallel_executor = factory["parallel"](max_workers=4)
result = parallel_executor.execute(job_definitions)

# Obtener orden de ejecución sin ejecutar
execution_order = runner._get_execution_order(["load"])
# Retorna: ["extract", "transform", "load"]
```

**Errores y manejo de fallos:**
- **ValueError**: Nombres de trabajos duplicados → Se valida unicidad en constructor
- **MissingJobDependencyError**: Dependencia no encontrada → Se valida existencia de trabajos dependientes
- **ValueError**: Dependencia circular detectada → Se usa algoritmo de ordenamiento topológico
- **ValidationError**: Definición de trabajo inválida → Se valida con Pydantic
- **Exception**: Error en ejecución de trabajo → Se captura con traceback completo y logging

**Rendimiento y escala:**
- Algoritmo de ordenamiento topológico eficiente para resolución de dependencias
- Ejecución paralela para trabajos independientes (máximo rendimiento)
- Cambio automático a secuencial cuando hay dependencias
- Control de número máximo de hilos para evitar sobrecarga
- Logging estructurado sin impacto significativo en performance

**Concurrencia e idempotencia:**
- Thread-safe: MultithreadExecutor usa ThreadPoolExecutor thread-safe
- Process-safe: Cada proceso tiene su propia instancia de JobRunner
- Idempotente: Múltiples ejecuciones con mismos parámetros producen resultados consistentes
- Dependencias: Resolución determinística basada en orden topológico

**Seguridad y cumplimiento:**
- **Validación de entrada**: Pydantic valida todas las definiciones de trabajos
- **Logging seguro**: Información estructurada sin exposición de datos sensibles
- **Manejo de errores**: Captura completa de excepciones con contexto
- **Auditoría**: Logging detallado de ejecución y resultados para compliance

**Dependencias:**
- Internas: `demo_comfandi_project.libs.exceptions`, `demo_comfandi_project.libs.logging`
- Externas: `pydantic` (validación), `concurrent.futures` (ThreadPoolExecutor), `typing_extensions` (ParamSpec)

**Puntos de extensión:**
- **Ejecutores personalizados**: Crear ejecutores que extiendan `IExecutor`
- **Validadores personalizados**: Extender validación de JobDefinition con Pydantic
- **Estrategias de ejecución**: Implementar nuevas estrategias de ejecución
- **Manejo de errores**: Personalizar manejo de errores en ejecutores

```python
# Ejemplo de extensión: Ejecutor personalizado
from demo_comfandi_project.libs.runner.executors.base import IExecutor
from demo_comfandi_project.libs.runner.types import JobDefinition, Status

class CustomExecutor(IExecutor):
    def execute(self, jobs: list[JobDefinition]) -> Status:
        # Lógica personalizada de ejecución
        for job in jobs:
            result = job.job(**job.args)
            if result.status_value != "OK":
                return Status(status_value="ERROR", message="Custom execution failed")
        return Status(status_value="OK", message="All jobs completed")

# Registrar en factory
ExecutorFactory.map_executor["custom"] = CustomExecutor
```

**Casos borde y limitaciones:**
- **Dependencias circulares**: Se detectan y causan ValueError
- **Trabajos faltantes**: Se valida existencia antes de ejecución
- **Ejecutor inválido**: Se valida nombre de ejecutor en factory
- **Trabajos con dependencias en paralelo**: Se cambia automáticamente a secuencial
- **Máximo de hilos**: Se respeta límite del sistema operativo

**Logging y observabilidad:**
- **Logs clave**: Inicio/fin de ejecutores, inicio/fin de trabajos, errores con traceback
- **Métricas**: No emite métricas directamente, pero facilita observabilidad con logging estructurado
- **Atributos estándar**: operation, executor, job_name, status, args, result
- **Estados**: IN_PROGRESS, STARTED, DONE, ERROR para tracking de progreso

**Pruebas:**
- **Unitarias**: Resolución de dependencias, validación de JobDefinition, ejecutores individuales
- **Integración**: JobRunner completo con múltiples trabajos y dependencias
- **Fixtures**: JobDefinition sintético, funciones mock, ejecutores de prueba

```python
# Ejemplo de prueba unitaria
def test_dependency_resolution():
    job_definitions = [
        JobDefinition(name="a", job=mock_job, args={}, depends_on=["b"]),
        JobDefinition(name="b", job=mock_job, args={}, depends_on=[])
    ]
    runner = JobRunner(job_definitions)
    order = runner._resolve_dependencies(["a"])
    assert order == ["b", "a"]  # b debe ejecutarse antes que a

def test_circular_dependency():
    job_definitions = [
        JobDefinition(name="a", job=mock_job, args={}, depends_on=["b"]),
        JobDefinition(name="b", job=mock_job, args={}, depends_on=["a"])
    ]
    runner = JobRunner(job_definitions)
    with pytest.raises(ValueError, match="Circular dependency"):
        runner._resolve_dependencies(["a"])
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en API de JobDefinition o Status
- **Compatibilidad**: Mantiene compatibilidad con definiciones de trabajos existentes
- **Migración**: Actualizaciones de Pydantic pueden requerir ajustes en validación

**FAQ:**
- **¿Por qué usar códigos HTTP-like?** — Para estandarizar estados de procesos y facilitar integración con sistemas externos
- **¿Cómo funciona la resolución de dependencias?** — Usa algoritmo de ordenamiento topológico para detectar ciclos y ordenar trabajos
- **¿Es thread-safe?** — Sí, MultithreadExecutor usa ThreadPoolExecutor que es thread-safe
- **¿Qué pasa si un trabajo falla?** — Se captura el error, se registra en logs, y se continúa con otros trabajos
- **¿Cómo elegir entre secuencial y paralelo?** — Paralelo para trabajos independientes, secuencial para trabajos con dependencias complejas

**Referencias:**
- Código: `demo_comfandi_project/libs/runner/job_runner.py`
- Tipos: `template_project/libs/runner/types.py`
- Ejecutores: `template_project/libs/runner/executors/`
- Pydantic: https://pydantic-docs.helpmanual.io/
- ThreadPoolExecutor: https://docs.python.org/3/library/concurrent.futures.html

### Validator Utilities (`libs/validator_utils/`)

**Nombre:** `demo_comfandi_project.libs.validator_utils` — módulo

**Propósito:** Proporciona un sistema robusto de validación de parámetros y configuración usando Dynaconf con validadores personalizados y mensajes de error descriptivos para asegurar la integridad de configuraciones del proyecto.

**Responsabilidades y alcance:**
- Validación automática de parámetros de configuración usando Dynaconf
- Soporte para múltiples entornos (dev, test, prod)
- Validadores personalizados con condiciones específicas
- Logging estructurado de validación y errores
- Integración con VarsResource para gestión de configuración
- Mensajes de error descriptivos y específicos

No hace:
- Validación de datos en tiempo de ejecución
- Validación de esquemas de base de datos
- Validación de APIs externas

**Conceptos clave:**
- **validate_json_parameters()**: Función principal para validar parámetros de configuración
- **Helper functions**: Funciones auxiliares para crear validadores (create_filter_validator, create_dict_validator, etc.)
- **Validator**: Clase de Dynaconf para definir reglas de validación
- **VarsResource**: Recurso de configuración integrado con validación
- **ValidationError**: Excepción de Dynaconf con detalles acumulativos de errores
- **Mensajes Descriptivos**: Mensajes de error claros y específicos para cada tipo de validación

**Arquitectura y flujo:**
Entradas (Config Paths + Environment + Validators) → VarsResource → Dynaconf Validators → Validación de Parámetros → Resultado (Success/Error) + Logging

Punto de inicio: `validate_json_parameters(config_paths, validators, env)`

**API pública:**
- `validate_json_parameters(config_paths, validators, env) -> tuple[bool, str]`: Función principal de validación
- `create_filter_validator()`: Crea validadores para campos de filtros
- `create_string_list_validator()`: Crea validadores para listas de strings
- `create_dict_validator()`: Crea validadores para diccionarios
- `create_version_validator()`: Crea validador para versiones semánticas
- `create_filters_structure_validator()`: Crea validador para estructura de filtros
- `is_uppercase_strings_list(value) -> bool`: Valida lista de strings en mayúsculas
- `is_strings_list(value) -> bool`: Valida lista de strings
- `has_valid_filter_keys(value) -> bool`: Valida claves de filtro válidas
- `is_dict_of_ints(value) -> bool`: Valida diccionario de enteros
- `is_dict_of_bools(value) -> bool`: Valida diccionario de booleanos

**Entradas y salidas:**
Entradas:
- `config_paths` (list[str] | str): Rutas de archivos de configuración
- `validators` (list[Validator]): Lista de validadores (obligatorio). Deben crearse usando las funciones helper.
- `env` (Literal["dev", "test", "prod"]): Entorno a usar, default "dev"

Salidas:
- `tuple[bool, str]`: (success, message) - True si exitoso, False con mensaje de error
- Efectos colaterales: Logging estructurado, validación de configuración

**Configuración:**
- Entornos soportados: "dev", "test", "prod"
- Formatos de archivo: TOML, YAML, JSON, INI
- Tipos de filtros: isin, eq, noteq, notin, lt, lte, gt, gte, isnull, isnotnull
- **Nota**: No hay validadores predefinidos. Los proyectos deben crear sus propios validadores usando las funciones helper.

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.validator_utils import validate_json_parameters
from demo_comfandi_project.libs.validator_utils.validators import (
    create_version_validator,
    create_filters_structure_validator,
)

# Crear validadores para el proyecto
validators = [
    create_version_validator(required=True),
    create_filters_structure_validator(required=True),
]

success, message = validate_json_parameters(
    config_paths=["config/parameters.toml"],
    validators=validators,
    env="dev"
)

if success:
    print("Validación exitosa")
else:
    print(f"Error: {message}")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.validator_utils import validate_json_parameters
from demo_comfandi_project.libs.validator_utils.validators import (
    create_version_validator,
    create_filters_structure_validator,
    create_filter_validator,
)

# Crear validadores del proyecto
validators = [
    create_version_validator(required=True),
    create_filters_structure_validator(required=True),
    create_filter_validator("filters.isin.my_field", required=True),
]

# Validación con validadores personalizados
success, message = validate_json_parameters(
    config_paths=["config/custom.toml", "config/secrets.yaml"],
    validators=validators,
    env="prod"
)

if success:
    print("Validación exitosa")
else:
    print(f"Error de validación: {message}")

# Validación con múltiples archivos
success, message = validate_json_parameters(
    config_paths=[
        "config/base.toml",
        "config/environment/dev.toml",
        "config/secrets.json"
    ],
    validators=validators,
    env="dev"
)
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.validator_utils import validate_json_parameters
from demo_comfandi_project.libs.validator_utils.validators import (
    create_version_validator,
    create_filters_structure_validator,
    create_filter_validator,
    create_dict_validator,
)
from dynaconf import Validator

# Crear validadores personalizados usando funciones helper
validators = [
    create_version_validator(required=True),
    create_filters_structure_validator(required=True),
    create_filter_validator("filters.isin.codigo_organizacion", required=True),
    create_dict_validator("num_partitions", value_type=int),
]

# También puedes crear validadores personalizados directamente
custom_validator = Validator(
        "database.host",
        must_exist=True,
        is_type_of=str,
        condition=lambda v: len(v) > 0
    ),
    Validator(
        "database.port",
        must_exist=True,
        is_type_of=int,
        condition=lambda v: 1 <= v <= 65535
    ),
    Validator(
        "api.timeout",
        must_exist=True,
        is_type_of=int,
        condition=lambda v: v > 0
    )
]

# Combinar validadores predefinidos con personalizados
all_validators = VALIDATORS + custom_validators

# Validar con validadores combinados
success, message = validate_json_parameters(
    config_paths=[
        "config/base.toml",
        "config/database.toml",
        "config/api.toml"
    ],
    env="prod",
    validators=all_validators
)

if success:
    print("✅ Configuración válida para producción")
else:
    print(f"❌ Error de validación: {message}")

# Validación por entorno específico
environments = ["dev", "test", "prod"]
for env in environments:
    success, message = validate_json_parameters(
        config_paths=[f"config/{env}.toml"],
        env=env
    )
    print(f"{env}: {'✅' if success else '❌'} {message}")
```

**Errores y manejo de fallos:**
- **JSONDecodeError**: Error de parsing de archivos JSON → Se captura y retorna mensaje descriptivo
- **ValidationError**: Errores de validación con detalles acumulativos → Se extraen detalles específicos
- **Exception**: Errores inesperados → Se capturan con logging completo y contexto
- **FileNotFoundError**: Archivos de configuración faltantes → Se maneja a través de VarsResource
- **TypeError**: Tipos de datos incorrectos → Se valida con validadores de tipo

**Rendimiento y escala:**
- Validación eficiente usando Dynaconf optimizado
- Carga lazy de archivos de configuración
- Validación en memoria sin persistencia adicional
- Soporte para archivos de configuración grandes
- Logging estructurado sin impacto significativo en performance

**Concurrencia e idempotencia:**
- Thread-safe: Operaciones de Dynaconf son thread-safe
- Process-safe: Cada proceso tiene su propia instancia de validación
- Idempotente: Múltiples validaciones con mismos parámetros producen resultados consistentes
- Stateless: No mantiene estado entre validaciones

**Seguridad y cumplimiento:**
- **Validación de entrada**: Se valida existencia y tipos de parámetros críticos
- **Logging seguro**: Información estructurada sin exposición de datos sensibles
- **Manejo de errores**: Captura completa de excepciones con contexto
- **Auditoría**: Logging detallado de validación para compliance

**Dependencias:**
- Internas: `demo_comfandi_project.libs.resources`, `demo_comfandi_project.libs.logging`
- Externas: `dynaconf` (Validator, ValidationError), `json` (JSONDecodeError), `re` (regex patterns)

**Puntos de extensión:**
- **Validadores personalizados**: Crear validadores específicos usando Dynaconf Validator
- **Funciones de validación**: Implementar funciones de validación personalizadas
- **Mensajes de error**: Personalizar mensajes de error para casos específicos
- **Integración con otros sistemas**: Extender para validar configuraciones de sistemas externos

```python
# Ejemplo de extensión: Validador personalizado
from dynaconf import Validator

def is_valid_email(value):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return isinstance(value, str) and re.match(pattern, value) is not None

custom_validator = Validator(
    "email",
    must_exist=True,
    is_type_of=str,
    condition=is_valid_email,
    messages={
        "must_exist_true": "Email is required",
        "condition": "Email must be a valid email address"
    }
)

# Usar en validación
success, message = validate_json_parameters(
    config_paths=["config/app.toml"],
    env="dev",
    validators=[custom_validator]
)
```

**Casos borde y limitaciones:**
- **Archivos corruptos**: Se maneja con JSONDecodeError y mensajes descriptivos
- **Configuraciones incompletas**: Se valida existencia de campos requeridos
- **Tipos incorrectos**: Se valida con validadores de tipo específicos
- **Validadores circulares**: Se evita con diseño de validadores independientes
- **Archivos muy grandes**: Se maneja eficientemente con Dynaconf

**Logging y observabilidad:**
- **Logs clave**: Inicio/fin de validación, errores específicos, datos validados
- **Métricas**: No emite métricas directamente, pero facilita observabilidad con logging estructurado
- **Atributos estándar**: operation, state, env, config_paths, accumulative_errors
- **Estados**: IN_PROGRESS, SUCCESS, ERROR para tracking de progreso

**Pruebas:**
- **Unitarias**: Validadores individuales, funciones de validación, manejo de errores
- **Integración**: Validación completa con diferentes configuraciones y entornos
- **Fixtures**: Archivos de configuración sintéticos, validadores mock

```python
# Ejemplo de prueba unitaria
def test_validate_json_parameters():
    # Crear archivo de configuración de prueba
    test_config = {
        "version": "1.0.0",
        "filters": {
            "isin": {
                "codigo_organizacion_ventas": ["ORG001", "ORG002"]
            }
        }
    }
    
    # Escribir archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        toml.dump(test_config, f)
        config_path = f.name
    
    try:
        # Ejecutar validación
        success, message = validate_json_parameters(
            config_paths=[config_path],
            env="dev"
        )
        
        # Verificar resultados
        assert success == True
        assert "successfully" in message.lower()
    finally:
        os.unlink(config_path)

def test_custom_validator():
    # Crear validador personalizado
    custom_validator = Validator(
        "test_field",
        must_exist=True,
        is_type_of=str,
        condition=lambda v: len(v) > 0
    )
    
    # Crear configuración de prueba
    test_config = {"test_field": "valid_value"}
    
    # Validar
    success, message = validate_json_parameters(
        config_paths=[create_temp_config(test_config)],
        env="dev",
        validators=[custom_validator]
    )
    
    assert success == True
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en API de validate_json_parameters o funciones helper
- **Compatibilidad**: Mantiene compatibilidad con configuraciones existentes
- **Migración**: Actualizaciones de Dynaconf pueden requerir ajustes en validadores

**FAQ:**
- **¿Cómo agregar nuevos validadores?** — Crear instancias de Dynaconf Validator y pasarlas como parámetro
- **¿Qué formatos de archivo soporta?** — TOML, YAML, JSON, INI a través de Dynaconf
- **¿Cómo personalizar mensajes de error?** — Usar el parámetro messages en Validator
- **¿Es thread-safe?** — Sí, Dynaconf es thread-safe y las operaciones son atómicas
- **¿Cómo validar configuraciones por entorno?** — Usar el parámetro env para especificar el entorno

**Referencias:**
- Código: `demo_comfandi_project/libs/validator_utils/parameters_validation.py`
- Utilidades: `template_project/libs/validator_utils/validators.py`
- Dynaconf: https://dynaconf.readthedocs.io/
- VarsResource: `template_project/libs/resources/vars/resource.py`

### Core Utilities (`libs/`)

#### Args Utilities (`args.py`)

**Nombre:** `demo_comfandi_project.libs.args` — módulo

**Propósito:** Proporciona funciones para parsear argumentos de línea de comandos de manera consistente y validada para configuración de entorno y trabajos del proyecto.

**Responsabilidades y alcance:**
- Parseo de argumentos de línea de comandos usando argparse
- Validación de argumentos requeridos (entorno y trabajos)
- Conversión automática de lista de trabajos separada por comas
- Integración con sistemas de CI/CD y scripts de automatización

No hace:
- Validación de contenido de argumentos (solo estructura)
- Persistencia de argumentos parseados
- Manejo de argumentos opcionales complejos

**Conceptos clave:**
- **get_args()**: Función principal para parsear argumentos de línea de comandos
- **argparse.Namespace**: Objeto contenedor de argumentos parseados
- **Argumentos requeridos**: --env y --jobs son obligatorios
- **Conversión automática**: Lista de trabajos se convierte automáticamente de string a list

**Arquitectura y flujo:**
Argumentos CLI → argparse.ArgumentParser → Validación → Conversión → argparse.Namespace

Punto de inicio: `get_args()`

**API pública:**
- `get_args() -> argparse.Namespace`: Función principal de parseo de argumentos

**Entradas y salidas:**
Entradas:
- Argumentos de línea de comandos: `--env` (str, required), `--jobs` (str, required)

Salidas:
- `argparse.Namespace`: Objeto con atributos `env` (str) y `jobs` (list[str])

**Configuración:**
- Argumentos requeridos: --env y --jobs
- Formato de jobs: Lista separada por comas
- Validación automática de argumentos obligatorios

Ejemplo mínimo:
```bash
python script.py --env dev --jobs job1,job2,job3
```

**Uso básico:**
```python
from demo_comfandi_project.libs.args import get_args

# Parsear argumentos de línea de comandos
args = get_args()

print(f"Entorno: {args.env}")
print(f"Trabajos: {args.jobs}")

# Uso en scripts
if args.env == "prod":
    print("Ejecutando en producción")
    
for job in args.jobs:
    print(f"Ejecutando trabajo: {job}")
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.args import get_args

# Validación de entorno
args = get_args()

valid_environments = ["dev", "test", "prod"]
if args.env not in valid_environments:
    raise ValueError(f"Entorno inválido: {args.env}")

# Procesamiento de trabajos
args = get_args()

if not args.jobs:
    raise ValueError("Debe especificar al menos un trabajo")

# Filtrar trabajos específicos
critical_jobs = ["backup", "sync", "validate"]
critical_to_run = [job for job in args.jobs if job in critical_jobs]

# Integración con otros módulos
from demo_comfandi_project.libs import Context

args = get_args()
Context.set("environment", args.env)
Context.set("jobs_to_run", args.jobs)
```

**Errores y manejo de fallos:**
- **SystemExit**: Argumentos faltantes o inválidos → Se captura con argparse
- **ValueError**: Conversión de argumentos fallida → Se maneja internamente
- **KeyboardInterrupt**: Interrupción del usuario → Se propaga normalmente

**Rendimiento y escala:**
- Parseo eficiente usando argparse optimizado
- Sin overhead significativo para argumentos simples
- Escalable para scripts con múltiples argumentos

**Concurrencia e idempotencia:**
- Thread-safe: argparse es thread-safe
- Process-safe: Cada proceso parsea sus propios argumentos
- Idempotente: Múltiples llamadas con mismos argumentos producen resultados consistentes
- Stateless: No mantiene estado entre llamadas

**Seguridad y cumplimiento:**
- **Validación de entrada**: Argumentos requeridos validados automáticamente
- **Sanitización**: argparse maneja caracteres especiales automáticamente
- **Logging**: No expone información sensible en logs

**Dependencias:**
- Internas: Ninguna
- Externas: `argparse` (módulo estándar de Python)

**Puntos de extensión:**
- **Argumentos adicionales**: Extender ArgumentParser con nuevos argumentos
- **Validación personalizada**: Agregar validadores específicos
- **Conversión de tipos**: Personalizar conversiones de argumentos

```python
# Ejemplo de extensión: Argumentos adicionales
import argparse

def get_extended_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, required=True, help="Environment name")
    parser.add_argument("--jobs", required=True, help="Comma-separated list of jobs")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    
    args = parser.parse_args()
    args.jobs = list(args.jobs.split(','))
    return args
```

**Casos borde y limitaciones:**
- **Argumentos faltantes**: Se lanza SystemExit con mensaje descriptivo
- **Formato inválido**: argparse maneja automáticamente
- **Caracteres especiales**: Se manejan correctamente en nombres de trabajos
- **Lista vacía**: Se permite lista vacía de trabajos (validación externa requerida)

**Logging y observabilidad:**
- **Logs clave**: No emite logs directamente
- **Métricas**: No emite métricas
- **Debugging**: argparse proporciona mensajes de error descriptivos

**Pruebas:**
- **Unitarias**: Parseo de argumentos válidos e inválidos
- **Integración**: Uso con scripts reales
- **Fixtures**: Argumentos sintéticos para testing

```python
# Ejemplo de prueba unitaria
import sys
from unittest.mock import patch
from demo_comfandi_project.libs.args import get_args

def test_get_args():
    # Simular argumentos de línea de comandos
    test_args = ["script.py", "--env", "dev", "--jobs", "job1,job2"]
    
    with patch.object(sys, 'argv', test_args):
        args = get_args()
        
        assert args.env == "dev"
        assert args.jobs == ["job1", "job2"]

def test_missing_args():
    # Simular argumentos faltantes
    test_args = ["script.py"]
    
    with patch.object(sys, 'argv', test_args):
        try:
            get_args()
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass  # Expected behavior
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en estructura de argumentos
- **Compatibilidad**: Mantiene compatibilidad con scripts existentes
- **Migración**: Actualizaciones de argparse pueden requerir ajustes

**FAQ:**
- **¿Cómo agregar nuevos argumentos?** — Extender el ArgumentParser en get_args()
- **¿Qué pasa si faltan argumentos?** — Se lanza SystemExit con mensaje descriptivo
- **¿Cómo validar contenido de argumentos?** — Validación externa después del parseo
- **¿Es thread-safe?** — Sí, argparse es thread-safe
- **¿Cómo usar en tests?** — Mockear sys.argv para simular argumentos

**Referencias:**
- Código: `demo_comfandi_project/libs/args.py`
- argparse: https://docs.python.org/3/library/argparse.html

#### Common Patterns (`common_patterns.py`)

**Nombre:** `demo_comfandi_project.libs.common_patterns` — módulo

**Propósito:** Proporciona funciones utilitarias comunes y optimizadas para manipulación de DataFrames de Spark, encapsulando patrones frecuentes de procesamiento de datos.

**Responsabilidades y alcance:**
- Funciones utilitarias para manipulación de DataFrames de Spark
- Patrones comunes de limpieza y transformación de datos
- Filtros seguros con manejo robusto de casos edge
- Funciones de timestamp con zona horaria
- Manejo de valores nulos y espacios en blanco

No hace:
- Operaciones complejas de agregación
- Transformaciones específicas de dominio
- Optimizaciones de performance avanzadas

**Conceptos clave:**
- **current_timestamp_with_tz()**: Genera timestamp actual con zona horaria específica
- **clean_spaces_and_tabs()**: Limpia espacios y tabs de columnas string
- **safe_isin_filter()**: Filtro seguro con lista de valores (maneja listas vacías)
- **safe_notin_filter()**: Filtro de exclusión seguro
- **get_match_flag_null_condition()**: Bandera de coincidencia con manejo de nulls

**Arquitectura y flujo:**
DataFrame + Parámetros → Funciones Utilitarias → DataFrame Transformado + Columnas Spark

Punto de inicio: Importar funciones específicas según necesidad

**API pública:**
- `current_timestamp_with_tz(timestamp_format: str, tz: str) -> Column`: Timestamp con zona horaria
- `clean_spaces_and_tabs(dataframe: DataFrame, cols: list[str] | None) -> DataFrame`: Limpieza de espacios
- `safe_isin_filter(column_name: str, filter_values: list[Any]) -> Column`: Filtro seguro de inclusión
- `safe_notin_filter(column_name: str, filter_values: list[Any]) -> Column`: Filtro seguro de exclusión
- `get_match_flag_null_condition(col1: str, col2: str, fallback_value: str) -> Column`: Bandera de coincidencia

**Entradas y salidas:**
Entradas:
- `timestamp_format` (str): Formato de timestamp (ej: "yyyy-MM-dd HH:mm:ss")
- `tz` (str): Zona horaria (ej: "America/Bogota")
- `dataframe` (DataFrame): DataFrame de Spark a procesar
- `cols` (list[str] | None): Columnas específicas a limpiar
- `column_name` (str): Nombre de columna para filtros
- `filter_values` (list[Any]): Valores para filtros

Salidas:
- `Column`: Columna de Spark para uso en transformaciones
- `DataFrame`: DataFrame transformado con columnas limpias

**Configuración:**
- Formatos de timestamp: Compatible con Spark date_format
- Zonas horarias: Compatible con Spark timezone functions
- Tipos de columna: Funciones específicas para StringType
- Valores por defecto: fallback_value="FALSE" para banderas

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.common_patterns import clean_spaces_and_tabs

df_clean = clean_spaces_and_tabs(df)
```

**Uso básico:**
```python
from demo_comfandi_project.libs.common_patterns import (
    current_timestamp_with_tz,
    clean_spaces_and_tabs,
    safe_isin_filter,
    safe_notin_filter,
    get_match_flag_null_condition
)

# Timestamp con zona horaria
df = df.withColumn(
    "timestamp_col", 
    current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota")
)

# Limpiar espacios y tabs
df_clean = clean_spaces_and_tabs(df)

# Filtros seguros
df_filtered = df.filter(safe_isin_filter("codigo", ["A", "B", "C"]))
df_excluded = df.filter(safe_notin_filter("codigo", ["X", "Y", "Z"]))

# Bandera de coincidencia
df = df.withColumn(
    "match_flag",
    get_match_flag_null_condition("col1", "col2", "FALSE")
)
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.common_patterns import clean_spaces_and_tabs, safe_isin_filter

# Limpieza selectiva de columnas
string_columns = ["nombre", "descripcion", "comentarios"]
df_clean = clean_spaces_and_tabs(df, string_columns)

# Filtros dinámicos con contexto
valid_codes = Context.get("valid_codes", [])
df_filtered = df.filter(safe_isin_filter("codigo", valid_codes))

# Múltiples filtros combinados
df_result = df.filter(
    safe_isin_filter("tipo", ["A", "B"]) &
    safe_notin_filter("estado", ["INACTIVO", "ELIMINADO"]) &
    safe_isin_filter("region", ["NORTE", "SUR"])
)

# Timestamp para auditoría
df_audit = df.withColumn(
    "created_at",
    current_timestamp_with_tz("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", "UTC")
).withColumn(
    "updated_at",
    current_timestamp_with_tz("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", "UTC")
)

# Bandera de coincidencia con lógica compleja
df_comparison = df.withColumn(
    "data_match",
    get_match_flag_null_condition("source_data", "target_data", "UNKNOWN")
).withColumn(
    "status_match",
    get_match_flag_null_condition("expected_status", "actual_status", "PENDING")
)
```

**Errores y manejo de fallos:**
- **ColumnNotFoundError**: Columna especificada no existe → Se valida antes del uso
- **TypeError**: Tipo de columna incorrecto → Se valida con isinstance
- **ValueError**: Formato de timestamp inválido → Se maneja con Spark functions
- **EmptyDataFrameError**: DataFrame vacío → Se maneja con validaciones

**Rendimiento y escala:**
- Funciones optimizadas para Spark
- Operaciones vectorizadas cuando es posible
- Manejo eficiente de nulls y espacios
- Escalable para DataFrames grandes

**Concurrencia e idempotencia:**
- Thread-safe: Operaciones de Spark son thread-safe
- Process-safe: Cada proceso tiene su propia instancia de Spark
- Idempotente: Múltiples aplicaciones producen resultados consistentes
- Stateless: No mantiene estado entre operaciones

**Seguridad y cumplimiento:**
- **Sanitización de datos**: Limpieza de espacios y caracteres especiales
- **Validación de entrada**: Verificación de tipos de columna
- **Manejo de nulls**: Lógica específica para valores nulos

**Dependencias:**
- Internas: Ninguna
- Externas: `pyspark.sql` (Column, DataFrame, functions), `pyspark.sql.types` (StringType)

**Puntos de extensión:**
- **Funciones personalizadas**: Crear funciones específicas para patrones comunes
- **Validadores de columna**: Extender validación de tipos
- **Formateadores**: Agregar formatos de timestamp adicionales

```python
# Ejemplo de extensión: Función personalizada
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType

def safe_contains_filter(column_name: str, search_values: list[str]) -> Column:
    """Filtro seguro que busca si la columna contiene alguno de los valores."""
    if not search_values:
        return sf.lit(True)
    
    conditions = [sf.col(column_name).contains(value) for value in search_values]
    return sf.expr(" OR ".join([f"({cond})" for cond in conditions]))

# Usar función personalizada
df_filtered = df.filter(safe_contains_filter("descripcion", ["urgente", "crítico"]))
```

**Casos borde y limitaciones:**
- **DataFrame vacío**: Funciones manejan DataFrames vacíos correctamente
- **Columnas inexistentes**: Se valida existencia antes del uso
- **Tipos incorrectos**: Se valida tipo de columna antes de procesar
- **Listas vacías**: Filtros seguros manejan listas vacías apropiadamente
- **Valores nulos**: Se manejan con lógica específica en cada función

**Logging y observabilidad:**
- **Logs clave**: No emite logs directamente
- **Métricas**: No emite métricas
- **Debugging**: Funciones de Spark proporcionan información de debugging

**Pruebas:**
- **Unitarias**: Funciones individuales con diferentes tipos de entrada
- **Integración**: Uso con DataFrames reales de Spark
- **Fixtures**: DataFrames sintéticos para testing

```python
# Ejemplo de prueba unitaria
from pyspark.sql import SparkSession
from demo_comfandi_project.libs.common_patterns import clean_spaces_and_tabs, safe_isin_filter

def test_clean_spaces_and_tabs():
    spark = SparkSession.builder.appName("test").getOrCreate()
    
    # Crear DataFrame de prueba
    data = [("  test  ", "normal"), ("\t\ttab\t\t", "spaces")]
    df = spark.createDataFrame(data, ["col1", "col2"])
    
    # Aplicar limpieza
    df_clean = clean_spaces_and_tabs(df, ["col1"])
    
    # Verificar resultados
    result = df_clean.collect()
    assert result[0]["col1"] == "test"
    assert result[1]["col1"] == "tab"

def test_safe_isin_filter():
    spark = SparkSession.builder.appName("test").getOrCreate()
    
    data = [("A",), ("B",), ("C",)]
    df = spark.createDataFrame(data, ["codigo"])
    
    # Filtro con valores
    df_filtered = df.filter(safe_isin_filter("codigo", ["A", "B"]))
    assert df_filtered.count() == 2
    
    # Filtro con lista vacía
    df_all = df.filter(safe_isin_filter("codigo", []))
    assert df_all.count() == 3
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en firmas de funciones o tipos de retorno
- **Compatibilidad**: Mantiene compatibilidad con DataFrames existentes
- **Migración**: Actualizaciones de PySpark pueden requerir ajustes

**FAQ:**
- **¿Cómo limpiar solo columnas específicas?** — Usar el parámetro cols en clean_spaces_and_tabs
- **¿Qué pasa con listas vacías en filtros?** — safe_isin_filter retorna True, safe_notin_filter retorna True
- **¿Cómo manejar valores nulos?** — Las funciones tienen lógica específica para nulls
- **¿Es compatible con Spark 3.x?** — Sí, usa funciones estándar de PySpark
- **¿Cómo agregar nuevos patrones?** — Crear funciones siguiendo el mismo patrón

**Referencias:**
- Código: `demo_comfandi_project/libs/common_patterns.py`
- PySpark: https://spark.apache.org/docs/latest/api/python/

#### Context (`context.py`)

**Nombre:** `demo_comfandi_project.libs.context` — clase

**Propósito:** Proporciona una clase singleton thread-safe para gestión de estado global de aplicación con soporte para namespaces jerárquicos y operaciones atómicas.

**Responsabilidades y alcance:**
- Gestión de estado global de aplicación usando patrón singleton
- Soporte para namespaces jerárquicos para organización de datos
- Operaciones thread-safe con locks reentrantes
- Snapshot y limpieza de estado
- Operaciones atómicas para consistencia de datos

No hace:
- Persistencia de estado entre sesiones
- Serialización automática de objetos complejos
- Gestión de memoria automática

**Conceptos clave:**
- **Singleton Thread-Safe**: Una sola instancia compartida entre threads
- **Double-Checked Locking**: Patrón optimizado para inicialización thread-safe
- **Namespaces Jerárquicos**: Organización de datos por namespace (ej: "opel/span_id")
- **Operaciones Atómicas**: Todas las operaciones son thread-safe
- **Snapshot**: Copia del estado actual para rollback o auditoría

**Arquitectura y flujo:**
Operación → Lock → Validación → Modificación → Unlock → Resultado

Punto de inicio: `Context.set()`, `Context.get()`, `Context.instance()`

**API pública:**
- `instance() -> Context`: Obtiene instancia singleton
- `set(key: str, value: Any) -> None`: Establece valor en contexto
- `get(key: str, default: Any | None) -> Any | None`: Obtiene valor del contexto
- `has(key: str) -> bool`: Verifica existencia de clave
- `update(values: dict[str, Any]) -> None`: Actualiza múltiples valores
- `delete(key: str) -> bool`: Elimina clave del contexto
- `clear() -> None`: Limpia todo el contexto
- `snapshot() -> dict[str, Any]`: Crea snapshot del estado actual
- `get_namespace(namespace: str) -> dict[str, Any]`: Obtiene datos de namespace
- `set_namespace(namespace: str, key: str, value: Any) -> None`: Establece valor en namespace
- `clear_namespace(namespace: str) -> int`: Limpia namespace específico

**Entradas y salidas:**
Entradas:
- `key` (str): Clave para almacenar/recuperar valor
- `value` (Any): Valor a almacenar
- `namespace` (str): Namespace para organización jerárquica
- `default` (Any | None): Valor por defecto si clave no existe

Salidas:
- `Any | None`: Valor almacenado o default
- `bool`: True si operación exitosa, False si no
- `dict[str, Any]`: Datos de namespace o snapshot
- `int`: Número de claves eliminadas

**Configuración:**
- Patrón singleton: Una instancia por proceso
- Locks: RLock para operaciones reentrantes
- Namespaces: Separados por "/" (ej: "opel/span_id")
- Threading: Thread-safe por diseño

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.context import Context

Context.set("user_id", "12345")
user_id = Context.get("user_id")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.context import Context

# Operaciones básicas
Context.set("user_id", "12345")
Context.set("session_id", "abc123")

user_id = Context.get("user_id")
has_user = Context.has("user_id")

# Operaciones con namespace
Context.set_namespace("opel", "span_id", "span_001")
Context.set_namespace("opel", "trace_id", "trace_001")

opel_data = Context.get_namespace("opel")
# Resultado: {"span_id": "span_001", "trace_id": "trace_001"}

# Actualización masiva
Context.update({
    "config.database.host": "localhost",
    "config.database.port": 5432,
    "config.api.timeout": 30
})

# Snapshot del estado
state_snapshot = Context.snapshot()
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.context import Context

# Gestión de estado de procesamiento
Context.set_namespace("processing", "current_job", "job_001")
Context.set_namespace("processing", "status", "IN_PROGRESS")
Context.set_namespace("processing", "start_time", "2024-01-01T10:00:00Z")

# Verificar estado
if Context.get_namespace_key("processing", "status") == "IN_PROGRESS":
    print("Procesamiento en curso")

# Limpiar namespace específico
cleared_count = Context.clear_namespace("processing")
print(f"Eliminadas {cleared_count} claves del namespace processing")

# Operaciones con jerarquía
Context.set("config/database/host", "localhost")
Context.set("config/database/port", 5432)
Context.set("config/api/timeout", 30)

# Recuperar configuración completa
config = Context.get("config")
# Resultado: {"database": {"host": "localhost", "port": 5432}, "api": {"timeout": 30}}

# Gestión de sesiones
def start_session(session_id: str, user_id: str):
    Context.set_namespace("session", session_id, {
        "user_id": user_id,
        "start_time": "2024-01-01T10:00:00Z",
        "status": "ACTIVE"
    })

def end_session(session_id: str):
    Context.delete_namespace_key("session", session_id)

# Uso en contexto de aplicación
start_session("sess_001", "user_123")
session_data = Context.get_namespace_key("session", "sess_001")
```

**Errores y manejo de fallos:**
- **KeyError**: Clave no encontrada → Se maneja con valores por defecto
- **TypeError**: Tipo de valor incorrecto → Se valida antes del almacenamiento
- **ThreadingError**: Problemas de concurrencia → Se maneja con locks
- **MemoryError**: Estado muy grande → Se limita con limpieza periódica

**Rendimiento y escala:**
- Operaciones O(1) para acceso por clave
- Locks optimizados para concurrencia
- Escalable para estado moderado
- Snapshot eficiente con copia superficial

**Concurrencia e idempotencia:**
- Thread-safe: Todas las operaciones son thread-safe
- Process-safe: Cada proceso tiene su propia instancia
- Idempotente: Múltiples operaciones con mismos parámetros son consistentes
- Atómico: Operaciones complejas son atómicas

**Seguridad y cumplimiento:**
- **Datos sensibles**: No se almacenan datos sensibles por defecto
- **Acceso controlado**: Operaciones thread-safe previenen condiciones de carrera
- **Auditoría**: Snapshot permite auditoría del estado

**Dependencias:**
- Internas: Ninguna
- Externas: `threading` (Lock, RLock)

**Puntos de extensión:**
- **Serialización**: Agregar serialización de estado
- **Persistencia**: Extender para persistir estado
- **Validación**: Agregar validadores de tipo
- **Observadores**: Implementar patrón observer para cambios

```python
# Ejemplo de extensión: Context con validación
class ValidatedContext(Context):
    def __init__(self):
        super().__init__()
        self._validators = {}
    
    def add_validator(self, key_pattern: str, validator_func):
        """Agregar validador para claves que coincidan con el patrón."""
        self._validators[key_pattern] = validator_func
    
    def _set(self, key: str, value: Any) -> None:
        # Validar antes de establecer
        for pattern, validator in self._validators.items():
            if key.startswith(pattern):
                if not validator(value):
                    raise ValueError(f"Valor inválido para clave {key}")
        
        super()._set(key, value)

# Usar contexto validado
validated_context = ValidatedContext()
validated_context.add_validator("config/", lambda v: isinstance(v, (str, int, bool)))
```

**Casos borde y limitaciones:**
- **Estado muy grande**: Puede consumir mucha memoria
- **Claves circulares**: Se evita con diseño cuidadoso
- **Serialización**: Objetos complejos pueden no ser serializables
- **Persistencia**: Estado se pierde al reiniciar aplicación

**Logging y observabilidad:**
- **Logs clave**: No emite logs directamente
- **Métricas**: No emite métricas
- **Debugging**: Snapshot permite inspección del estado

**Pruebas:**
- **Unitarias**: Operaciones individuales con diferentes tipos de datos
- **Integración**: Uso en contexto multi-thread
- **Fixtures**: Estado sintético para testing

```python
# Ejemplo de prueba unitaria
import threading
from demo_comfandi_project.libs.context import Context

def test_context_operations():
    # Limpiar estado inicial
    Context.clear()
    
    # Operaciones básicas
    Context.set("test_key", "test_value")
    assert Context.get("test_key") == "test_value"
    assert Context.has("test_key") == True
    
    # Operaciones con namespace
    Context.set_namespace("test", "key1", "value1")
    Context.set_namespace("test", "key2", "value2")
    
    namespace_data = Context.get_namespace("test")
    assert namespace_data == {"key1": "value1", "key2": "value2"}
    
    # Snapshot
    snapshot = Context.snapshot()
    assert "test_key" in snapshot

def test_thread_safety():
    Context.clear()
    
    def worker(thread_id: int):
        for i in range(100):
            Context.set(f"thread_{thread_id}_key_{i}", f"value_{i}")
    
    # Crear múltiples threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Esperar a que terminen
    for thread in threads:
        thread.join()
    
    # Verificar que no hay condiciones de carrera
    snapshot = Context.snapshot()
    assert len(snapshot) == 500  # 5 threads * 100 operaciones
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en API de métodos públicos
- **Compatibilidad**: Mantiene compatibilidad con código existente
- **Migración**: Cambios en estructura interna no afectan API

**FAQ:**
- **¿Es thread-safe?** — Sí, todas las operaciones son thread-safe
- **¿Cómo usar namespaces?** — Usar set_namespace/get_namespace para organización
- **¿Se persiste el estado?** — No, es solo en memoria
- **¿Cómo limpiar el estado?** — Usar clear() o clear_namespace()
- **¿Cómo hacer backup del estado?** — Usar snapshot() para crear copia

**Referencias:**
- Código: `demo_comfandi_project/libs/context.py`
- Threading: https://docs.python.org/3/library/threading.html

#### Exceptions (`exceptions.py`)

**Nombre:** `demo_comfandi_project.libs.exceptions` — módulo

**Propósito:** Define una jerarquía de excepciones personalizadas del proyecto con mensajes descriptivos y contexto específico para facilitar el debugging y manejo de errores.

**Responsabilidades y alcance:**
- Jerarquía clara de excepciones del proyecto
- Mensajes descriptivos con contexto específico
- Preservación de información adicional en excepciones
- Facilitación de debugging y resolución de problemas
- Integración con sistemas de logging y monitoreo

No hace:
- Manejo automático de excepciones
- Logging automático de errores
- Persistencia de información de errores

**Conceptos clave:**
- **BaseProjectException**: Clase base para todas las excepciones del proyecto
- **TableNotFoundError**: Excepción para tablas no encontradas
- **ColumnsNotMatchedError**: Excepción para columnas que no coinciden
- **UpdateControlTableError**: Excepción para errores de actualización de tabla de control
- **MissingJobDependencyError**: Excepción para dependencias de trabajo faltantes
- **ValidationError**: Excepción para errores de validación

**Arquitectura y flujo:**
Error Detectado → Excepción Específica → Contexto Preservado → Propagación → Manejo/Captura

Punto de inicio: Importar excepciones específicas según necesidad

**API pública:**
- `BaseProjectException`: Clase base para todas las excepciones del proyecto
- `TableNotFoundError(table_name: str)`: Excepción para tabla no encontrada
- `ColumnsNotMatchedError(expected: set, actual: set)`: Excepción para columnas no coincidentes
- `UpdateControlTableError(message: str)`: Excepción para error de actualización de tabla de control
- `MissingJobDependencyError(job_name: str, missing_dependency: str)`: Excepción para dependencia faltante
- `ValidationError(message: str)`: Excepción para error de validación

**Entradas y salidas:**
Entradas:
- `table_name` (str): Nombre de la tabla no encontrada
- `expected` (set): Conjunto de columnas esperadas
- `actual` (set): Conjunto de columnas actuales
- `message` (str): Mensaje de error descriptivo
- `job_name` (str): Nombre del trabajo con dependencia faltante
- `missing_dependency` (str): Nombre de la dependencia faltante

Salidas:
- Excepciones con mensajes descriptivos y contexto preservado
- Atributos adicionales para debugging

**Configuración:**
- Jerarquía de herencia: BaseProjectException como clase base
- Mensajes descriptivos: Formato consistente para cada tipo
- Contexto preservado: Atributos adicionales en cada excepción
- Integración: Compatible con sistemas de logging estándar

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.exceptions import TableNotFoundError

if not table_exists("mi_tabla"):
    raise TableNotFoundError("mi_tabla")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.exceptions import (
    TableNotFoundError, 
    ColumnsNotMatchedError,
    MissingJobDependencyError,
    ValidationError
)

# Excepción de tabla no encontrada
if not table_exists("usuarios"):
    raise TableNotFoundError("usuarios")

# Excepción de columnas no coincidentes
expected_cols = {"id", "nombre", "fecha"}
actual_cols = {"id", "descripcion", "fecha"}
if expected_cols != actual_cols:
    raise ColumnsNotMatchedError(expected_cols, actual_cols)

# Excepción de dependencia faltante
available_jobs = ["job1", "job2", "job3"]
required_deps = ["job4", "job5"]
for dep in required_deps:
    if dep not in available_jobs:
        raise MissingJobDependencyError("main_job", dep)

# Excepción de validación
if not is_valid_config(config):
    raise ValidationError("Configuración inválida: campos requeridos faltantes")
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.exceptions import (
    TableNotFoundError,
    ColumnsNotMatchedError,
    UpdateControlTableError,
    MissingJobDependencyError,
    ValidationError
)

# Validación de tablas con contexto
def validate_table_schema(table_name: str, expected_schema: dict):
    if not table_exists(table_name):
        raise TableNotFoundError(table_name)
    
    actual_schema = get_table_schema(table_name)
    if actual_schema != expected_schema:
        raise ColumnsNotMatchedError(
            set(expected_schema.keys()),
            set(actual_schema.keys())
        )

# Manejo de dependencias de trabajos
def validate_job_dependencies(jobs: list[str], dependencies: dict[str, list[str]]):
    for job_name, deps in dependencies.items():
        if job_name not in jobs:
            continue
        
        for dep in deps:
            if dep not in jobs:
                raise MissingJobDependencyError(job_name, dep)

# Validación de configuración con mensajes específicos
def validate_database_config(config: dict):
    required_fields = ["host", "port", "database"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise ValidationError(f"Campos faltantes en configuración de base de datos: {missing_fields}")
    
    if not isinstance(config["port"], int) or config["port"] <= 0:
        raise ValidationError(f"Puerto inválido: {config['port']}")

# Manejo de errores de actualización de tabla de control
def update_control_table(table_name: str, update_data: dict):
    try:
        # Lógica de actualización
        result = execute_update(table_name, update_data)
        if not result.success:
            raise UpdateControlTableError(f"Error en actualización: {result.error_message}")
    except Exception as e:
        raise UpdateControlTableError(f"Error inesperado: {str(e)}")

# Uso en contexto de procesamiento
def process_data_with_validation(data: dict):
    try:
        # Validar datos de entrada
        if not data.get("id"):
            raise ValidationError("ID es requerido")
        
        # Validar tabla de destino
        if not table_exists("processed_data"):
            raise TableNotFoundError("processed_data")
        
        # Procesar datos
        process_data(data)
        
    except (ValidationError, TableNotFoundError) as e:
        # Log específico para errores de validación
        logger.error(f"Error de validación: {e}")
        raise
    except Exception as e:
        # Log para errores inesperados
        logger.error(f"Error inesperado: {e}")
        raise ValidationError(f"Error inesperado en procesamiento: {str(e)}")
```

**Errores y manejo de fallos:**
- **Exception**: Excepciones base de Python → Se capturan y convierten a excepciones específicas
- **AttributeError**: Atributos faltantes → Se valida antes del acceso
- **TypeError**: Tipos incorrectos → Se valida antes del uso
- **ValueError**: Valores inválidos → Se convierte a ValidationError

**Rendimiento y escala:**
- Creación eficiente de excepciones
- Mensajes descriptivos sin overhead significativo
- Escalable para sistemas con alto volumen de errores
- Preservación de contexto sin impacto en performance

**Concurrencia e idempotencia:**
- Thread-safe: Creación de excepciones es thread-safe
- Process-safe: Cada proceso maneja sus propias excepciones
- Idempotente: Mismas condiciones producen mismas excepciones
- Stateless: No mantiene estado entre excepciones

**Seguridad y cumplimiento:**
- **Información sensible**: No se expone información sensible en mensajes
- **Auditoría**: Excepciones proporcionan contexto para auditoría
- **Debugging**: Información específica para resolución de problemas

**Dependencias:**
- Internas: Ninguna
- Externas: `Exception` (clase base de Python)

**Puntos de extensión:**
- **Excepciones personalizadas**: Crear nuevas excepciones heredando de BaseProjectException
- **Mensajes personalizados**: Personalizar mensajes según contexto
- **Contexto adicional**: Agregar atributos específicos para debugging
- **Integración con logging**: Extender para logging automático

```python
# Ejemplo de extensión: Excepción personalizada
class DatabaseConnectionError(BaseProjectException):
    """Excepción para errores de conexión a base de datos."""
    
    def __init__(self, host: str, port: int, error_message: str):
        super().__init__(f"Error conectando a base de datos {host}:{port}: {error_message}")
        self.host = host
        self.port = port
        self.error_message = error_message
        self.timestamp = datetime.now().isoformat()

# Usar excepción personalizada
def connect_to_database(host: str, port: int):
    try:
        connection = create_connection(host, port)
        return connection
    except ConnectionError as e:
        raise DatabaseConnectionError(host, port, str(e))
```

**Casos borde y limitaciones:**
- **Mensajes muy largos**: Se limitan para evitar problemas de memoria
- **Contexto circular**: Se evita con diseño cuidadoso
- **Serialización**: Objetos complejos en contexto pueden no ser serializables
- **Propagación**: Excepciones se propagan normalmente

**Logging y observabilidad:**
- **Logs clave**: No emite logs directamente, pero facilita logging estructurado
- **Métricas**: No emite métricas directamente
- **Debugging**: Información específica para debugging
- **Contexto**: Atributos adicionales para análisis

**Pruebas:**
- **Unitarias**: Creación y propagación de excepciones específicas
- **Integración**: Uso en contexto de aplicación real
- **Fixtures**: Datos sintéticos para testing

```python
# Ejemplo de prueba unitaria
import pytest
from demo_comfandi_project.libs.exceptions import (
    TableNotFoundError,
    ColumnsNotMatchedError,
    MissingJobDependencyError,
    ValidationError
)

def test_table_not_found_error():
    error = TableNotFoundError("test_table")
    assert str(error) == "Table 'test_table' not found."
    assert error.table_name == "test_table"

def test_columns_not_matched_error():
    expected = {"id", "name"}
    actual = {"id", "description"}
    error = ColumnsNotMatchedError(expected, actual)
    assert "Expected columns" in str(error)
    assert error.expected == expected
    assert error.actual == actual

def test_missing_job_dependency_error():
    error = MissingJobDependencyError("main_job", "dependency_job")
    assert "main_job" in str(error)
    assert "dependency_job" in str(error)
    assert error.job_name == "main_job"
    assert error.missing_dependency == "dependency_job"

def test_validation_error():
    error = ValidationError("Invalid configuration")
    assert str(error) == "Validation error: Invalid configuration"
    assert error.message == "Invalid configuration"

def test_exception_inheritance():
    # Verificar herencia
    assert issubclass(TableNotFoundError, BaseProjectException)
    assert issubclass(ColumnsNotMatchedError, BaseProjectException)
    assert issubclass(MissingJobDependencyError, BaseProjectException)
    assert issubclass(ValidationError, BaseProjectException)
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en estructura de excepciones o mensajes
- **Compatibilidad**: Mantiene compatibilidad con código existente
- **Migración**: Nuevas excepciones no afectan código existente

**FAQ:**
- **¿Cómo crear nuevas excepciones?** — Heredar de BaseProjectException
- **¿Cómo personalizar mensajes?** — Sobrescribir __init__ con mensaje personalizado
- **¿Cómo agregar contexto adicional?** — Agregar atributos en __init__
- **¿Es thread-safe?** — Sí, creación de excepciones es thread-safe
- **¿Cómo integrar con logging?** — Usar en bloques try/except con logging

**Referencias:**
- Código: `demo_comfandi_project/libs/exceptions.py`
- Python Exceptions: https://docs.python.org/3/tutorial/errors.html

#### Utils (`utils.py`)

**Nombre:** `demo_comfandi_project.libs.utils` — módulo

**Propósito:** Proporciona utilidades generales para manejo de recursos de paquetes, resolución de rutas y manipulación de configuraciones DynaBox.

**Responsabilidades y alcance:**
- Copia segura de recursos de paquetes a directorios temporales
- Resolución robusta de rutas de recursos
- Utilidades para manipulación de DynaBox
- Gestión de archivos y directorios temporales
- Integración con importlib.resources

No hace:
- Persistencia de recursos copiados
- Gestión de permisos de archivos
- Validación de contenido de recursos

**Conceptos clave:**
- **get_package_resource_path()**: Copia recursos de paquetes a directorio temporal
- **get_key_by_value()**: Busca clave por valor en DynaBox
- **importlib.resources**: Módulo estándar para acceso a recursos de paquetes
- **DynaBox**: Contenedor de Dynaconf para configuraciones
- **Directorios temporales**: Uso de tempfile para recursos copiados

**Arquitectura y flujo:**
Recurso del Paquete → importlib.resources → Copia Temporal → Ruta Resuelta

Punto de inicio: `get_package_resource_path()`, `get_key_by_value()`

**API pública:**
- `get_package_resource_path(package_name: str, resource_path: str | None, string: bool) -> Path | str`: Copia recurso a directorio temporal
- `get_key_by_value(box: DynaBox, target_value: str) -> str | None`: Busca clave por valor en DynaBox

**Entradas y salidas:**
Entradas:
- `package_name` (str): Nombre del paquete que contiene el recurso
- `resource_path` (str | None): Ruta al recurso dentro del paquete
- `string` (bool): Si retornar como string en lugar de Path
- `box` (DynaBox): Contenedor DynaBox para buscar
- `target_value` (str): Valor a buscar en el box

Salidas:
- `Path | str`: Ruta al recurso copiado en directorio temporal
- `str | None`: Clave correspondiente al valor objetivo

**Configuración:**
- Directorio temporal: tempfile.gettempdir() / package_name
- Formatos soportados: Archivos y directorios
- Copia: shutil.copytree para directorios, shutil.copy2 para archivos
- Resolución: importlib.resources para acceso a recursos

Ejemplo mínimo:
```python
from demo_comfandi_project.libs.utils import get_package_resource_path

config_path = get_package_resource_path("template_project", "config/default.toml")
```

**Uso básico:**
```python
from demo_comfandi_project.libs.utils import get_package_resource_path, get_key_by_value
from dynaconf import DynaBox

# Copiar archivo de configuración
config_path = get_package_resource_path(
    "template_project", 
    "config/default.toml"
)

# Copiar directorio completo
data_path = get_package_resource_path(
    "template_project", 
    "data"
)

# Obtener como string
config_str = get_package_resource_path(
    "template_project", 
    "config/default.toml",
    string=True
)

# Buscar clave por valor en DynaBox
box = DynaBox({
    "env_dev": "development",
    "env_prod": "production",
    "env_test": "testing"
})

key = get_key_by_value(box, "production")
# Resultado: "env_prod"
```

**Ejemplos adicionales:**
```python
from demo_comfandi_project.libs.utils import get_package_resource_path, get_key_by_value
from dynaconf import DynaBox
from pathlib import Path

# Copiar múltiples recursos
def copy_project_resources():
    resources = [
        ("template_project", "config/default.toml"),
        ("template_project", "config/secrets.yaml"),
        ("template_project", "data/sample.csv"),
        ("template_project", "templates/")
    ]
    
    copied_paths = {}
    for package, resource in resources:
        path = get_package_resource_path(package, resource)
        copied_paths[resource] = path
    
    return copied_paths

# Trabajar con DynaBox complejo
def find_environment_config(config_data: DynaBox, env_name: str):
    # Buscar configuración por entorno
    cfg_k = get_key_by_value(config_data, env_name)
    if cfg_k:
        return config_data[cfg_k]
    
    # Buscar por patrón
    for key, value in config_data.items():
        if env_name in key.lower():
            return value
    
    return None

# Gestión de recursos con validación
def get_validated_resource(package_name: str, resource_path: str) -> Path:
    try:
        path = get_package_resource_path(package_name, resource_path)
        
        # Validar que el recurso existe
        if not path.exists():
            raise FileNotFoundError(f"Recurso no encontrado: {resource_path}")
        
        return path
        
    except Exception as e:
        raise ValueError(f"Error copiando recurso {resource_path}: {str(e)}")

# Uso en contexto de configuración
def load_config_from_package(package_name: str, config_name: str):
    config_path = get_package_resource_path(
        package_name, 
        f"config/{config_name}.toml"
    )
    
    # Cargar configuración
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    return config_content

# Integración con DynaBox
def create_environment_mapping(config_box: DynaBox) -> dict[str, str]:
    """Crear mapeo de entornos basado en DynaBox."""
    mapping = {}
    
    for key, value in config_box.items():
        if key.startswith("env_"):
            env_name = key[4:]  # Remover prefijo "env_"
            mapping[env_name] = value
    
    return mapping

# Buscar configuración específica
def find_config_by_pattern(config_box: DynaBox, pattern: str) -> dict:
    """Buscar configuraciones que coincidan con un patrón."""
    matching_configs = {}
    
    for key, value in config_box.items():
        if pattern.lower() in key.lower():
            matching_configs[key] = value
    
    return matching_configs
```

**Errores y manejo de fallos:**
- **FileNotFoundError**: Recurso no encontrado → Se valida existencia antes de copiar
- **PermissionError**: Permisos insuficientes → Se maneja con try/catch
- **ValueError**: Parámetros inválidos → Se valida antes del procesamiento
- **ImportError**: Paquete no encontrado → Se valida existencia del paquete

**Rendimiento y escala:**
- Copia eficiente usando shutil optimizado
- Resolución lazy de recursos
- Escalable para recursos moderados
- Limpieza automática de temporales

**Concurrencia e idempotencia:**
- Thread-safe: Operaciones de archivo son thread-safe
- Process-safe: Cada proceso tiene sus propios temporales
- Idempotente: Múltiples copias con mismos parámetros producen resultados consistentes
- Stateless: No mantiene estado entre operaciones

**Seguridad y cumplimiento:**
- **Recursos seguros**: Solo copia recursos del paquete especificado
- **Temporales**: Usa directorios temporales del sistema
- **Permisos**: Respeta permisos del sistema de archivos

**Dependencias:**
- Internas: Ninguna
- Externas: `tempfile`, `shutil`, `pathlib`, `importlib.resources`, `dynaconf.utils.boxing` (DynaBox)

**Puntos de extensión:**
- **Validadores de recurso**: Agregar validación de contenido
- **Compresores**: Soporte para recursos comprimidos
- **Cache**: Implementar cache de recursos copiados
- **Filtros**: Filtrar recursos por tipo o patrón

```python
# Ejemplo de extensión: Utils con cache
import hashlib
from functools import lru_cache
from demo_comfandi_project.libs.utils import get_package_resource_path

class CachedResourceManager:
    def __init__(self):
        self._cache = {}
    
    def get_resource_with_cache(self, pkg_name: str, res_path: str) -> Path:
        # Crear clave de cache
        cache_name = f"{pkg_name}:{res_path}"
        
        if cache_name in self._cache:
            cached_path = self._cache[cache_name]
            if cached_path.exists():
                return cached_path
        
        # Copiar recurso
        path = get_package_resource_path(pkg_name, res_path)
        self._cache[cache_name] = path
        
        return path
    
    def clear_cache(self):
        """Limpiar cache de recursos."""
        self._cache.clear()

# Usar manager con cache
resource_manager = CachedResourceManager()
config_path = resource_manager.get_resource_with_cache("template_project", "config/default.toml")
```

**Casos borde y limitaciones:**
- **Recursos muy grandes**: Pueden consumir mucho espacio en temporales
- **Paquetes inexistentes**: Se valida existencia antes de acceso
- **Permisos insuficientes**: Se maneja con excepciones apropiadas
- **Recursos corruptos**: Se detecta durante la copia

**Logging y observabilidad:**
- **Logs clave**: No emite logs directamente
- **Métricas**: No emite métricas
- **Debugging**: Información de rutas para debugging

**Pruebas:**
- **Unitarias**: Funciones individuales con diferentes tipos de recursos
- **Integración**: Uso con paquetes reales
- **Fixtures**: Recursos sintéticos para testing

```python
# Ejemplo de prueba unitaria
import tempfile
import shutil
from pathlib import Path
from demo_comfandi_project.libs.utils import get_package_resource_path, get_key_by_value
from dynaconf import DynaBox

def test_get_package_resource_path():
    # Crear paquete de prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        # Simular estructura de paquete
        package_dir = Path(temp_dir) / "test_package"
        package_dir.mkdir()
        
        # Crear archivo de prueba
        test_file = package_dir / "test.txt"
        test_file.write_text("test content")
        
        # Probar copia de archivo
        copied_path = get_package_resource_path("test_package", "test.txt")
        assert copied_path.exists()
        assert copied_path.read_text() == "test content"

def test_get_key_by_value():
    box = DynaBox({
        "key1": "value1",
        "key2": "value2",
        "key3": "value1"  # Valor duplicado
    })
    
    # Buscar valor único
    key = get_key_by_value(box, "value2")
    assert key == "key2"
    
    # Buscar valor duplicado (retorna primera coincidencia)
    key = get_key_by_value(box, "value1")
    assert key == "key1"
    
    # Buscar valor inexistente
    key = get_key_by_value(box, "nonexistent")
    assert key is None

def test_get_package_resource_path_string():
    # Probar retorno como string
    path_str = get_package_resource_path("test_package", "test.txt", string=True)
    assert isinstance(path_str, str)
    assert Path(path_str).exists()
```

**Versionado y compatibilidad:**
- **Breaking changes**: Cambios en firmas de funciones o tipos de retorno
- **Compatibilidad**: Mantiene compatibilidad con código existente
- **Migración**: Actualizaciones de importlib.resources pueden requerir ajustes

**FAQ:**
- **¿Cómo copiar directorios completos?** — Usar resource_path que apunte al directorio
- **¿Qué pasa si el recurso no existe?** — Se lanza FileNotFoundError
- **¿Cómo obtener la ruta como string?** — Usar parámetro string=True
- **¿Es thread-safe?** — Sí, operaciones de archivo son thread-safe
- **¿Cómo limpiar recursos temporales?** — Se limpian automáticamente al cerrar aplicación

**Referencias:**
- Código: `demo_comfandi_project/libs/utils.py`
- importlib.resources: https://docs.python.org/3/library/importlib.resources.html
- Dynaconf: https://dynaconf.readthedocs.io/
