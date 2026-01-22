# Data Flow Template - Implementation Guide

This is a comprehensive template for creating new data flows. This guide provides detailed, step-by-step instructions for implementing flows that can work with various storage systems (Iceberg, Delta Lake, Parquet files, databases, etc.).

## Table of Contents

1. [Quick Start](#quick-start)
2. [Detailed Implementation Steps](#detailed-implementation-steps)
3. [File Structure and Responsibilities](#file-structure-and-responsibilities)
4. [Module Implementation Guide](#module-implementation-guide)
5. [Flow Design Patterns](#flow-design-patterns)
6. [Configuration Guide](#configuration-guide)
7. [Naming Conventions](#naming-conventions)
8. [Best Practices](#best-practices)
9. [Testing Guidelines](#testing-guidelines)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Copy the Template

```bash
# From project root
cd template-project/template_project/flows
cp -r _template_flow your_flow_name
```

**Important:** Choose a descriptive name that follows naming conventions (see [Naming Conventions](#naming-conventions)).

### Step 2: Rename All References

You must update all references to `template_flow` in the following files:

1. **`job.py`**:
   - Function name: `template_flow_job` → `your_flow_name_job`
   - Operation name in logging: `EXECUTE_TEMPLATE_FLOW_JOB` → `EXECUTE_YOUR_FLOW_NAME_JOB`
   - Import paths: `from template_project.flows._template_flow.*` → `from template_project.flows.your_flow_name.*`

2. **`extract.py`**, **`transform.py`**, **`load.py`**:
   - Update import paths if they reference the flow name
   - Update any flow-specific references

3. **`config/default.toml`**:
   - `component_name = "template_flow"` → `component_name = "your_flow_name"`
   - `[restart].template_flow` → `[restart].your_flow_name`

### Step 3: Configure Your Flow

Edit `config/default.toml` with your specific configuration (see [Configuration Guide](#configuration-guide)).

### Step 4: Implement ETL Modules

Implement the three core modules:
- `extract.py`: Data extraction logic
- `transform.py`: Data transformation logic
- `load.py`: Data loading logic

See [Module Implementation Guide](#module-implementation-guide) for detailed instructions.

---

## Detailed Implementation Steps

### Phase 1: Setup and Configuration

#### 1.1 Copy and Rename

   ```bash
# Navigate to flows directory
cd template-project/template_project/flows

# Copy template
cp -r _template_flow your_flow_name

# Navigate to new flow
cd your_flow_name
   ```

#### 1.2 Update File Imports

**In `job.py`**, update imports:

```python
# Before:
from template_project.flows._template_flow.extract import extract
from template_project.flows._template_flow.load import load
from template_project.flows._template_flow.transform import transform

# After:
from template_project.flows.your_flow_name.extract import extract
from template_project.flows.your_flow_name.load import load
from template_project.flows.your_flow_name.transform import transform
```

**In `job.py`**, update function name:

```python
# Before:
def template_flow_job(spark: SparkSession, vars_instance: VarsResource) -> Status:

# After:
def your_flow_name_job(spark: SparkSession, vars_instance: VarsResource) -> Status:
```

**In `job.py`**, update logging operation names:

```python
# Before:
"operation": "EXECUTE_TEMPLATE_FLOW_JOB"

# After:
"operation": "EXECUTE_YOUR_FLOW_NAME_JOB"
```

**In `job.py`**, update job_id pattern:

```python
# Before:
job_id = f"template_flow_{int(start_time)}"

# After:
job_id = f"your_flow_name_{int(start_time)}"
```

#### 1.3 Update Configuration

**In `config/default.toml`**:

```toml
# Update component name
[default]
component_name = "your_flow_name"

# Update table names (use nested sections)
[default.input]
table_name = "your_source_table"

[default.output]
table_name = "your_target_table"

# Add restart section only if your flow requires restart functionality
# [default.restart]
# your_flow_name = false  # Must match component_name
```

### Phase 2: Implement Extract Module

#### 2.1 Understand Your Source

Determine based on your requirements:
- **Source type**: Table, files, database, API?
- **Storage system**: Iceberg, Delta, Parquet, JDBC?
- **Extraction strategy**: Full load, incremental, CDC, or other? (only if your flow requires it)

#### 2.2 Implement Extract Function

**Basic extraction (simple):**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
) -> DataFrame:
    """Extract data from source."""
    # Simple extraction from table
    source_table = spark.table(vars_instance.vars.input.table_id)
    return source_table
```

**Extraction from files:**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
) -> DataFrame:
    """Extract data from files."""
    source_path = vars_instance.vars.input.table_id  # Can be a path
    return spark.read.parquet(source_path)
```

**Extraction with optional parameters (if flow requires):**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
    **kwargs  # Only add if flow requires specific parameters
) -> DataFrame:
    """Extract data with optional parameters."""
    # Only add parameters if your flow specifically requires them
    # Example: if flow requires incremental extraction
    first_run = kwargs.get("first_run", True)
    if first_run:
        return spark.table(vars_instance.vars.input.table_id)
    else:
        # Implement incremental extraction logic based on requirements
        return incremental_extract(spark, vars_instance)
```

**Incremental extraction with Iceberg (if flow requires and using Iceberg):**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
    **kwargs
) -> DataFrame:
    """Extract data using incremental strategy (if required)."""
    # Only implement if your flow specifically requires incremental extraction
    from template_project.libs.iceberg.cdc_with_tagging_strategy import ChangelogManager
    
    first_run = kwargs.get("first_run", True)
    if first_run:
        return spark.table(vars_instance.vars.input.table_id)
    
    changelog_manager = ChangelogManager(
        spark=spark,
        table_id=vars_instance.vars.input.table_id,
        tag_name=vars_instance.vars.get("last_snapshot_tag_name")
    )
    return changelog_manager.get_changelog_table(...)
```

**Note**: Only add parameters and implement incremental/CDC logic if your flow specifically requires it based on your requirements.

### Phase 3: Implement Transform Module

#### 3.1 Design Transformation Steps

Plan your transformation pipeline:
1. List all transformations needed
2. Determine order of operations
3. Identify dependencies between steps
4. Consider performance implications

#### 3.2 Implement Transform Function

**Simple transformations (inline):**

```python
@handle_errors
def transform(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    extracted_data: DataFrame,
) -> DataFrame:
    """Transform data."""
    from pyspark.sql import functions as sf
    from template_project.libs.common_patterns import current_timestamp_with_tz

    # Step 1: Clean data
    cleaned = extracted_data.dropDuplicates()

    # Step 2: Cast types
    typed = cleaned.withColumn("date_col", sf.col("date_col").cast("date"))

    # Step 3: Add metadata
    final = typed.withColumn(
        "current_timestamp_dwh",
        current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota")
    )

    return final
```

**Transformations with optional parameters (if flow requires):**

```python
@handle_errors
def transform(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    extracted_data: DataFrame,
    **kwargs  # Only add if flow requires specific parameters
) -> DataFrame:
    """Transform data with optional parameters."""
    # Only add parameters if your flow specifically requires them
    first_run = kwargs.get("first_run", True)
    if first_run:
        # Full transformation logic
        return full_transform(extracted_data)
    else:
        # Incremental transformation logic
        return incremental_transform(extracted_data)
```

**Complex transformations (with steps directory):**

1. Create step functions in `steps/` directory:

```python
# steps/step_100_clean_data.py
def step_100_clean_data(dataframe: DataFrame) -> DataFrame:
    """Clean and normalize data."""
    return dataframe.dropDuplicates()

# steps/step_200_cast_types.py
def step_200_cast_types(dataframe: DataFrame) -> DataFrame:
    """Cast columns to appropriate types."""
    return dataframe.withColumn("date_col", sf.col("date_col").cast("date"))
```

2. Import and use in `transform.py`:

```python
from template_project.flows.your_flow_name.steps.step_100_clean_data import step_100_clean_data
from template_project.flows.your_flow_name.steps.step_200_cast_types import step_200_cast_types

@handle_errors
def transform(...) -> DataFrame:
    step_100 = step_100_clean_data(extracted_data)
    step_200 = step_200_cast_types(step_100)
    return step_200
```

#### 3.3 Step Naming Convention

Name steps with numeric prefixes to indicate order:
- `step_100_*`: Initial cleaning/normalization
- `step_200_*`: Type casting and validation
- `step_300_*`: Basic transformations
- `step_400_*`: Joins and enrichment
- `step_500_*`: Aggregations
- `step_600_*`: Business logic
- `step_700_*`: Final formatting

Use increments of 100 to allow insertion of new steps later.

### Phase 4: Implement Load Module

#### 4.1 Determine Load Strategy

Determine load strategy based on your flow requirements:
- **Overwrite**: Replace all data (full load)
- **Merge**: Update/insert based on keys (incremental load)
- **Append**: Add new data without replacing
- **Other**: Custom strategy as needed

The strategy should be determined from your requirements, not from configuration flags.

#### 4.2 Implement Load Function

**For overwrite mode:**

```python
@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
) -> None:
    """Load data using overwrite."""
    # Simple overwrite
    transformed_data.write \
        .mode("overwrite") \
        .saveAsTable(vars_instance.vars.output.table_id)
```

**For merge mode (if using merge strategy):**

```python
@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
) -> None:
    """Load data using merge."""
    from template_project.libs.iceberg.utils import load_merge

    load_merge(
        spark=spark,
        dataframe=transformed_data,
        table_id=vars_instance.vars.output.table_id,
        merge_keys=vars_instance.vars.output.merge_keys,
        num_partitions=vars_instance.vars.num_partitions.min_global
    )
```

**Load with optional parameters (if flow requires):**

```python
@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
    **kwargs  # Only add if flow requires specific parameters
) -> None:
    """Load data with optional parameters."""
    # Only add parameters if your flow specifically requires them
    first_run = kwargs.get("first_run", True)
    if first_run:
        load_overwrite(...)
    else:
        load_merge(...)
```

**For other storage systems**, implement appropriate load logic based on your requirements.

### Phase 5: Update Job Module

#### 5.1 Basic ETL Orchestration

The job module orchestrates the ETL pipeline. Basic implementation:

```python
def your_flow_name_job(spark: SparkSession, vars_instance: VarsResource) -> Status:
    """Orchestrate ETL pipeline."""
    logger = get_logger(__name__)
    
    # Extract
    extracted_data = extract(spark=spark, vars_instance=vars_instance)
    
    # Transform
    transformed_data = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=vars_instance,
        extracted_data=extracted_data
    )
    
    # Load
    load(
        job_id=job_id,
        spark=spark,
        vars_instance=vars_instance,
        transformed_data=transformed_data
    )
    
    return Status(status_value="OK", message="Job completed successfully")
```

#### 5.2 Add Flow-Specific Logic (if needed)

Only add flow-specific logic if your flow requirements specifically need it:

**State Detection (if flow requires):**
```python
# Only if flow requires state tracking
from template_project.libs.iceberg.utils import is_empty

first_run = is_empty(spark, vars_instance.vars.output.table_id)
extracted_data = extract(spark=spark, vars_instance=vars_instance, first_run=first_run)
```

**Change Detection (if flow requires):**
```python
# Only if flow requires change detection
from template_project.libs.iceberg.cdc_with_tagging_strategy import SnapshotManager

snapshot_manager = SnapshotManager(...)
if not snapshot_manager.has_changed(...):
    return Status(status_value="OK", message="No changes detected")
```

**Restart Logic (if flow requires):**
```python
# Only if flow requires restart capability
from template_project.libs.iceberg.utils import restart_table

if vars_instance.vars.restart.get(component_name, False):
    restart_table(...)
```

**Note**: Only implement these if your flow specifically requires them based on your requirements. Don't assume.

---

## File Structure and Responsibilities

### Complete File Structure

```
your_flow_name/
├── job.py                    # Main orchestrator - coordinates ETL pipeline
├── extract.py                # Data extraction - reads from source
├── transform.py              # Data transformation - applies business logic
├── load.py                   # Data loading - writes to target
├── config/
│   └── default.toml          # Flow configuration (Dynaconf format)
├── steps/                    # Optional: Individual transformation steps
│   ├── __init__.py
│   ├── step_100_*.py         # Initial cleaning steps
│   ├── step_200_*.py         # Type casting steps
│   ├── step_300_*.py         # Basic transformations
│   ├── step_400_*.py         # Joins and enrichment
│   ├── step_500_*.py         # Aggregations
│   └── utils/                # Optional: Shared utilities for steps
│       └── *.py
└── README.md                 # This file
```

### File Responsibilities

#### `job.py` - Main Orchestrator

**Purpose:** Coordinates the entire ETL pipeline execution.

**Responsibilities:**
- Initialize logging and job tracking
- Call extract, transform, and load in sequence
- Handle error propagation
- Log execution metrics
- Return Status object
- Add flow-specific orchestration logic only if required

**What it should NOT do:**
- Implement extraction logic (delegate to extract.py)
- Implement transformation logic (delegate to transform.py)
- Implement loading logic (delegate to load.py)
- Contain business logic

**Key Patterns:**
- Always use structured logging with consistent attributes
- Track execution time
- Handle errors gracefully
- Provide clear status messages

#### `extract.py` - Data Extraction

**Purpose:** Read data from source systems.

**Responsibilities:**
- Connect to source (table, file, database, API)
- Implement extraction logic based on requirements
- Handle source-specific errors
- Return DataFrame with source data

**What it should NOT do:**
- Transform data (delegate to transform.py)
- Load data (delegate to load.py)
- Contain business logic

**Key Patterns:**
- Use `@handle_errors` decorator
- Implement extraction based on flow requirements
- Only add parameters (like first_run) if flow specifically requires them
- Log extraction details

#### `transform.py` - Data Transformation

**Purpose:** Apply business logic and data transformations.

**Responsibilities:**
- Clean and normalize data
- Cast data types
- Apply business rules
- Join with reference data
- Perform aggregations
- Return transformed DataFrame

**What it should NOT do:**
- Extract data (delegate to extract.py)
- Load data (delegate to load.py)
- Connect to external systems (except for reference data)

**Key Patterns:**
- Organize transformations into logical steps
- Use step functions for complex transformations
- Maintain transformation order
- Log transformation progress

#### `load.py` - Data Loading

**Purpose:** Write data to target systems.

**Responsibilities:**
- Connect to target (table, file, database)
- Implement load strategy based on requirements (overwrite, merge, append, etc.)
- Handle target-specific operations
- Add flow-specific operations (snapshot tagging, versioning, etc.) only if required

**What it should NOT do:**
- Extract data (delegate to extract.py)
- Transform data (delegate to transform.py)
- Contain business logic

**Key Patterns:**
- Implement load strategy based on flow requirements
- Configure merge keys only if using merge strategy
- Only add parameters (like first_run) if flow specifically requires them
- Add flow-specific operations (snapshot tagging, etc.) only if required

#### `config/default.toml` - Configuration

**Purpose:** Centralize all flow configuration.

**Responsibilities:**
- Define input/output sources (using nested sections [default.input], [default.output])
- Configure flow-specific settings (only what your flow requires)
- Define partitioning settings (if applicable)
- Configure error paths
- Add environment-specific overrides ([dev.input], [qa.input], [prod.input]) if needed

**Key Patterns:**
- Use format strings for dynamic values
- Reference environment variables
- Keep configuration environment-agnostic
- Document all configuration options

#### `steps/` - Transformation Steps (Optional)

**Purpose:** Organize complex transformations into reusable steps.

**When to use:**
- Transformations have 5+ steps
- Steps are reusable across flows
- Steps need individual testing
- Steps have clear separation of concerns

**Naming Convention:**
- `step_XXX_description.py` where XXX is a number (100, 200, 300, etc.)
- Use descriptive names that indicate the step's purpose
- Number steps in execution order

---

## Module Implementation Guide

### Implementing Extract Module

#### Step 1: Determine Source Type

Identify your source:
- **Table**: Iceberg, Delta, Hive table
- **Files**: Parquet, CSV, JSON files
- **Database**: JDBC connection
- **API**: REST API, streaming source

#### Step 2: Choose Extraction Strategy

Determine extraction strategy based on your flow requirements:
- **Full Extraction**: Read entire source dataset (simple, always works)
- **Incremental Extraction**: Read only changed/new data (if flow requires it)
- **Other Strategies**: Custom extraction logic as needed

The strategy should be determined from your requirements, not from configuration flags.

#### Step 3: Implement Extract Function

**Template for basic extraction:**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
) -> DataFrame:
    """Extract data from source."""
    # Get source identifier from configuration
    source_id = vars_instance.vars.input.table_id
    
    # Implement extraction based on source type
    # Example for table:
    return spark.table(source_id)
    
    # Example for files:
    # return spark.read.parquet(source_id)
    
    # Example for database:
    # return spark.read.format("jdbc").option("url", source_id).load()
```

**Template for incremental extraction (if flow requires and using Iceberg):**

```python
@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
    **kwargs  # Only add if flow requires parameters
) -> DataFrame:
    """Extract data using incremental strategy (if required)."""
    # Only implement if your flow specifically requires incremental extraction
    from template_project.libs.iceberg.cdc_with_tagging_strategy import ChangelogManager
    from template_project.libs.iceberg.utils import is_empty
    
    source_id = vars_instance.vars.input.table_id
    
    # Only add first_run detection if flow requires it
    first_run = kwargs.get("first_run", True)
    if first_run:
        return spark.table(source_id)
    
    # Incremental extraction logic
    changelog_manager = ChangelogManager(
        spark=spark,
        table_id=source_id,
        tag_name=vars_instance.vars.get("last_snapshot_tag_name")
    )
    return changelog_manager.get_changelog_table(...)
```

**Note**: Only implement incremental/CDC extraction if your flow specifically requires it based on your requirements.

#### Step 4: Add Logging (Optional)

```python
from template_project.libs.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Extracting data",
    extra={
        "attributes": {
            "source": vars_instance.vars.input.table_id
        }
    }
)
```

### Implementing Transform Module

#### Step 1: Plan Transformation Pipeline

Create a transformation plan:
1. List all required transformations
2. Determine execution order
3. Identify dependencies
4. Consider performance

**Example transformation plan:**

```
Input: Raw customer data
├── Step 1: Remove duplicates
├── Step 2: Cast date columns
├── Step 3: Normalize strings
├── Step 4: Join with reference table (countries)
├── Step 5: Calculate derived fields
└── Output: Cleaned customer data
```

#### Step 2: Implement Simple Transformations

For simple flows (3-4 steps), implement inline:

```python
@handle_errors
def transform(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    extracted_data: DataFrame,
) -> DataFrame:
    """Transform data."""
    from pyspark.sql import functions as sf
    
    # Step 1: Remove duplicates
    step1 = extracted_data.dropDuplicates(["customer_id"])
    
    # Step 2: Cast types
    step2 = step1.withColumn("birth_date", sf.col("birth_date").cast("date"))
    
    # Step 3: Normalize
    step3 = step2.withColumn("name", sf.upper(sf.trim(sf.col("name"))))
    
    return step3
```

#### Step 3: Implement Complex Transformations

For complex flows (5+ steps), use step functions:

**Create step files:**

```python
# steps/step_100_remove_duplicates.py
from pyspark.sql import DataFrame

def step_100_remove_duplicates(dataframe: DataFrame, key_columns: list[str]) -> DataFrame:
    """Remove duplicate records based on key columns."""
    return dataframe.dropDuplicates(key_columns)
```

```python
# steps/step_200_cast_types.py
from pyspark.sql import DataFrame
from pyspark.sql import functions as sf

def step_200_cast_types(dataframe: DataFrame) -> DataFrame:
    """Cast columns to appropriate data types."""
    return dataframe.withColumn("birth_date", sf.col("birth_date").cast("date"))
```

**Use in transform.py:**

```python
from template_project.flows.your_flow_name.steps.step_100_remove_duplicates import step_100_remove_duplicates
from template_project.flows.your_flow_name.steps.step_200_cast_types import step_200_cast_types

@handle_errors
def transform(...) -> DataFrame:
    step_100 = step_100_remove_duplicates(extracted_data, ["customer_id"])
    step_200 = step_200_cast_types(step_100)
    return step_200
```

#### Step 4: Handle Joins and Enrichment

```python
def step_400_enrich_with_reference(
    spark: SparkSession,
    vars_instance: VarsResource,
    dataframe: DataFrame
) -> DataFrame:
    """Enrich data with reference table."""
    reference_table = spark.table(vars_instance.vars.input.reference_table_id)
    
    return dataframe.join(
        reference_table,
        dataframe["country_code"] == reference_table["code"],
        "left"
    ).select(
        dataframe["*"],
        reference_table["country_name"].alias("country")
    )
```

#### Step 5: Add Logging

```python
from template_project.libs.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Transformation started",
    extra={
        "attributes": {
            "job_id": job_id,
            "input_rows": extracted_data.count()
        }
    }
)

# After transformations
logger.info(
    "Transformation completed",
    extra={
        "attributes": {
            "job_id": job_id,
            "output_rows": transformed_data.count()
        }
    }
)
```

### Implementing Load Module

#### Step 1: Determine Load Strategy

Determine load strategy based on your flow requirements:
- **Overwrite**: Replace all data (full load)
- **Merge**: Update/insert based on keys (incremental load)
- **Append**: Add new data without replacing
- **Other**: Custom strategy as needed

The strategy should be determined from your requirements, not from configuration flags.

#### Step 2: Implement Overwrite Mode

**Simple overwrite:**

```python
transformed_data.write \
    .mode("overwrite") \
    .saveAsTable(vars_instance.vars.output.table_id)
```

**With Iceberg utilities:**

```python
from template_project.libs.iceberg.utils import load_overwrite

load_overwrite(
    spark=spark,
    dataframe=transformed_data,
    table_id=vars_instance.vars.output.table_id,
    num_partitions=vars_instance.vars.num_partitions.min_global
)
```

#### Step 3: Implement Merge Mode

**With Iceberg utilities:**

```python
from template_project.libs.iceberg.utils import load_merge

load_merge(
    spark=spark,
    dataframe=transformed_data,
    table_id=vars_instance.vars.output.table_id,
    merge_keys=vars_instance.vars.output.merge_keys,  # e.g., ["id"]
    num_partitions=vars_instance.vars.num_partitions.min_global
)
```

**With Delta Lake:**

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, vars_instance.vars.output.table_id)
merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in vars_instance.vars.output.merge_keys])

delta_table.alias("target") \
    .merge(transformed_data.alias("source"), merge_condition) \
    .whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()
```

#### Step 4: Add Flow-Specific Operations (if required)

Only add these if your flow specifically requires them:

**Snapshot Tagging (if using Iceberg and flow requires state tracking):**
```python
# Only if flow requires snapshot tagging
from template_project.libs.iceberg.cdc_with_tagging_strategy import SnapshotManager

snapshot_manager = SnapshotManager(
    spark=spark,
    table_id=vars_instance.vars.input.table_id,
    tag_name=vars_instance.vars.get("last_snapshot_tag_name")
)
snapshot_manager.tag_current_snapshot(
    vars_instance.vars.get("last_snapshot_tag_name")
)
```

**Note**: Only implement snapshot tagging, versioning, or other flow-specific operations if your flow specifically requires them.

---

## Flow Design Patterns

These are example patterns. Your flow should be designed based on your specific requirements, not forced into a pattern.

### Pattern 1: Simple ETL

**Use Case:** Basic data processing with full loads.

**Characteristics:**
- Full extraction every run
- Simple transformations (cleaning, type casting)
- Overwrite target
- Fast and simple

**Implementation Notes:**
- Extract: Read entire source table/file
- Transform: Basic cleaning and normalization
- Load: Overwrite mode

### Pattern 2: Incremental Processing

**Use Case:** Process only changed/new data.

**Characteristics:**
- Incremental extraction (only changed/new data)
- Merge target table
- More efficient than full loads

**Implementation Notes:**
- Extract: Implement incremental extraction logic based on requirements
- Transform: Apply business logic
- Load: Merge mode with merge keys
- Job: Add state tracking if required

### Pattern 3: Complex Transformations

**Use Case:** Advanced transformations with multiple steps.

**Characteristics:**
- Full or incremental extraction (based on requirements)
- Complex multi-step transformations
- Aggregations and calculations
- Organized into step functions

**Implementation Notes:**
- Extract: Based on requirements
- Transform: Multiple steps in `steps/` directory
- Load: Based on requirements (overwrite, merge, etc.)
- Job: Add flow-specific logic only if required

### Pattern 4: Custom Requirements

**Use Case:** Flows with specific requirements (state tracking, change detection, restart, etc.).

**Characteristics:**
- Custom extraction strategy
- Custom transformation logic
- Custom load strategy
- Flow-specific orchestration logic

**Implementation Notes:**
- Implement only what your flow specifically requires
- Don't add features unless needed
- Base implementation on requirements, not patterns

---

## Configuration Guide

### Understanding Configuration Structure

The configuration uses Dynaconf format with sections:

```toml
[default]          # Global settings and environment variables
[input]            # Source configuration
[output]           # Target configuration
[restart]          # Restart configuration (if enabled)
[num_partitions]   # Partitioning configuration
```

### Required Configuration

**Minimum required configuration:**

```toml
[default]
component_name = "your_flow_name"

[default.input]
table_name = "source_table"
table_id = "@format {this.dl_catalog}.{this.stage_db}.{this.input.table_name}"

[default.output]
table_name = "target_table"
table_id = "@format {this.local_catalog}.{this.local_db}.{this.output.table_name}"
```

### Flow-Specific Configuration

Only add configuration that your flow specifically requires:

**For merge operations (if using merge strategy):**

```toml
[default.output]
merge_keys = ["id"]  # Primary key columns (only if using merge)
```

**For state tracking (if flow requires):**

```toml
[default]
# Add state tracking configuration only if flow requires it
# last_snapshot_tag_name = "@format {this.component_name}_last_snapshot"
```

**For restart capability (if flow requires):**

```toml
[default]
# Add restart configuration only if flow requires it
# enable_restart = true

# [default.restart]
# your_flow_name = false  # Set to true to restart
```

**Note**: Don't add configuration flags unless your flow specifically requires them. Base configuration on your requirements, not on patterns.

### Environment Variables

Set these in your deployment environment:

```bash
export GLUE_CATALOG_DB_STAGE="your_stage_db"
export ARTIFACTORY_BUCKET="your-bucket"
export GLUE_CATALOG_NAME="your_catalog"
export LOCAL_CATALOG_NAME="local"
```

---

## Naming Conventions

### Flow Names

**Format:** `{domain}_{layer}_{entity}`

**Examples:**
- `customers_bronze` - Bronze layer for customers
- `orders_silver` - Silver layer for orders
- `sales_gold` - Gold layer for sales analytics
- `inventory_daily` - Daily inventory processing

**Rules:**
- Use lowercase
- Use underscores to separate words
- Be descriptive but concise
- Avoid abbreviations unless widely understood

### Function Names

**Job function:**
```python
def {flow_name}_job(spark: SparkSession, vars_instance: VarsResource) -> Status:
```

**Examples:**
- `customers_bronze_job`
- `orders_silver_job`

### Operation Names (Logging)

**Format:** `EXECUTE_{FLOW_NAME}_JOB`

**Examples:**
- `EXECUTE_CUSTOMERS_BRONZE_JOB`
- `EXECUTE_ORDERS_SILVER_JOB`

### Step Function Names

**Format:** `step_{number}_{description}`

**Examples:**
- `step_100_clean_data`
- `step_200_cast_types`
- `step_300_join_reference`

### Configuration Keys

**Component name:**
```toml
component_name = "your_flow_name"  # Must match flow directory name
```

**Restart key (only if flow requires restart):**
```toml
# Only add if flow requires restart functionality
# [default.restart]
# your_flow_name = false  # Must match component_name
```

---

## Best Practices

### Code Organization

1. **Keep functions focused**: Each function should do one thing well
2. **Use step functions**: For complex transformations, break into steps
3. **Document everything**: Use docstrings for all functions
4. **Follow naming conventions**: Be consistent across flows

### Error Handling

1. **Use `@handle_errors` decorator**: On all ETL functions
2. **Log errors properly**: Include context in error logs
3. **Handle edge cases**: Empty data, null values, etc.
4. **Validate inputs**: Check DataFrame schemas when needed

### Performance

1. **Partition appropriately**: Use num_partitions configuration
2. **Avoid unnecessary shuffles**: Design transformations to minimize shuffles
3. **Cache when needed**: Cache DataFrames used multiple times
4. **Optimize joins**: Use broadcast joins for small tables

### Logging

1. **Use structured logging**: Always include attributes dictionary
2. **Log at key points**: Start, end, and major steps
3. **Include metrics**: Row counts, execution times
4. **Use appropriate levels**: INFO for normal flow, ERROR for errors

### Testing

1. **Test each module**: Unit tests for extract, transform, load
2. **Test step functions**: Individual tests for each step
3. **Test integration**: End-to-end tests for the flow
4. **Use fixtures**: Reusable test data and mocks

### Configuration

1. **Use format strings**: For dynamic configuration
2. **Document all options**: In config file comments
3. **Environment-specific**: Use environment variables
4. **Validate configuration**: Check required fields

---

## Testing Guidelines

### Unit Testing Structure

Create test files matching your flow structure:

```
template_project_tests/
└── flows/
    └── your_flow_name/
        ├── test_extract.py
        ├── test_transform.py
        ├── test_load.py
        ├── test_job.py
        └── steps/
            ├── test_step_100_*.py
            └── test_step_200_*.py
```

### Testing Extract Module

```python
# test_extract.py
import pytest
from pyspark.sql import SparkSession
from template_project.flows.your_flow_name.extract import extract
from template_project.libs.resources import VarsResource

def test_extract_full_load(spark: SparkSession, mock_vars_resource: VarsResource):
    """Test full extraction."""
    result = extract(spark, mock_vars_resource)
    assert result is not None
    assert result.count() > 0
```

### Testing Transform Module

```python
# test_transform.py
def test_transform_cleaning(spark: SparkSession, sample_dataframe: DataFrame):
    """Test data cleaning step."""
    from template_project.flows.your_flow_name.transform import transform
    
    result = transform(
        job_id="test_123",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=sample_dataframe
    )
    
    # Assert no duplicates
    assert result.count() == result.dropDuplicates().count()
```

### Testing Load Module

```python
# test_load.py
def test_load_overwrite(spark: SparkSession, mock_vars_resource: VarsResource):
    """Test overwrite load."""
    from template_project.flows.your_flow_name.load import load
    
    test_data = spark.createDataFrame([(1, "test")], ["id", "name"])
    
    load(
        job_id="test_123",
        spark=spark,
        vars_instance=mock_vars_resource,
        transformed_data=test_data
    )
    
    # Verify data was loaded
    loaded = spark.table(mock_vars_resource.vars.output.table_id)
    assert loaded.count() > 0
```

### Integration Testing

```python
# test_job.py
def test_full_flow_execution(spark: SparkSession, mock_vars_resource: VarsResource):
    """Test complete flow execution."""
    from template_project.flows.your_flow_name.job import your_flow_name_job
    
    status = your_flow_name_job(spark, mock_vars_resource)
    
    assert status.status_value == "OK"
    # Verify target table has data
    result = spark.table(mock_vars_resource.vars.output.table_id)
    assert result.count() > 0
```

---

## Troubleshooting

### Common Issues

#### Issue: Import Errors

**Problem:** `ImportError: cannot import name 'extract' from 'template_project.flows.your_flow_name.extract'`

**Solution:**
1. Verify file exists: `flows/your_flow_name/extract.py`
2. Check function name matches: `def extract(...)`
3. Verify `__init__.py` if using package structure
4. Check import path in `job.py`

#### Issue: Configuration Not Loading

**Problem:** `KeyError: 'input'` or configuration values are None

**Solution:**
1. Verify `config/default.toml` exists
2. Check format strings are correct: `@format {this.key}`
3. Verify environment variables are set
4. Check config path in `get_vars_resource()`

#### Issue: Table Not Found

**Problem:** `AnalysisException: Table or view not found`

**Solution:**
1. Verify table exists in catalog
2. Check table_id format: `catalog.database.table`
3. Verify catalog is registered in Spark
4. Check table permissions

#### Issue: Merge Keys Error

**Problem:** `AnalysisException: Cannot resolve column`

**Solution:**
1. Verify merge_keys exist in DataFrame
2. Check column names match exactly (case-sensitive)
3. Verify merge_keys are in output schema
4. Check DataFrame schema before merge

#### Issue: Incremental Extraction Not Working

**Problem:** Always extracts full table or incremental logic not working

**Solution:**
1. Verify incremental extraction logic is correctly implemented
2. Check state tracking configuration (if using state tracking)
3. Verify parameters are passed correctly to extract function
4. Review extraction logic matches requirements
3. Verify state tracking is working correctly (if using state tracking)
4. Check extraction logic matches requirements
5. Verify source table supports required operations (if applicable)

### Debugging Tips

1. **Add logging**: Log DataFrame schemas and row counts
2. **Check intermediate results**: Save DataFrames to temporary tables
3. **Validate configuration**: Print `vars_instance.vars.as_dict()`
4. **Test in isolation**: Test each module separately
5. **Use Spark UI**: Monitor job execution and performance

---

## Available Utilities

The project provides utilities that you can use (but are not required):

### Iceberg Utilities (if using Iceberg)

- `template_project.libs.iceberg.utils`: Table operations
  - `load_overwrite()`: Overwrite table
  - `load_merge()`: Merge data into table
  - `is_empty()`: Check if table is empty
  - `restart_table()`: Restart table

- `template_project.libs.iceberg.cdc_with_tagging_strategy`: CDC operations
  - `ChangelogManager`: Manage changelog extraction
  - `SnapshotManager`: Manage snapshot tagging

### Core Utilities

- `template_project.libs.error_handler`: Error handling decorator
- `template_project.libs.logging`: Structured logging
- `template_project.libs.resources`: Configuration management
- `template_project.libs.common_patterns`: Common transformation patterns

### Usage Examples

See docstrings in each module for detailed examples of how to use these utilities.

---

## Additional Resources

- **REFERENCE.md**: Complete technical reference for the project
- **Dynaconf Documentation**: https://www.dynaconf.com/
- **PySpark Documentation**: https://spark.apache.org/docs/latest/api/python/
- **Iceberg Documentation**: https://iceberg.apache.org/ (if using Iceberg)

---

## Summary Checklist

When implementing a new flow, ensure you have:

- [ ] Copied template directory
- [ ] Renamed all references (`template_flow` → `your_flow_name`)
- [ ] Updated imports in `job.py`
- [ ] Updated function names
- [ ] Updated logging operation names
- [ ] Updated `config/default.toml` with your configuration
- [ ] Implemented `extract()` function
- [ ] Implemented `transform()` function
- [ ] Implemented `load()` function
- [ ] Updated `job.py` with any flow-specific logic (only if required)
- [ ] Tested each module individually
- [ ] Tested complete flow execution
- [ ] Documented any custom logic
- [ ] Followed naming conventions
- [ ] Added appropriate logging
- [ ] Handled errors properly

---

This template provides a solid foundation for implementing data flows. Follow this guide step-by-step to create robust, maintainable flows that integrate seamlessly with the project architecture.
