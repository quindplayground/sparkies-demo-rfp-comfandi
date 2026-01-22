# Flow Requirements: Portafolios DynamoDB

## Flow Information

- Name: portafolios_dynamodb
- Purpose: Extract data from Iceberg table incrementally using CDC, transform and aggregate by client portfolio combination, and load to DynamoDB table with specific key structure and GSI indexes
- Layer: Analytics

## Source Requirements

- Type: Table
- Location: portafolios_iceberg.db_quind_tech_eval_stage_dev.tbl_dim_mat_portafolios_poststage_ppd_emr
- Format: Iceberg
- Sample data: ./sparkies-template-spark-project/.template/flows/example/sample_portfolio.parquet
- Extraction mode: Incremental
- Storage system: Iceberg
- Schema: Contains columns for portfolio materials including (see sample_portfolio.parquet for reference):
  - cod_transaccional
  - cod_org_vent
  - cod_canal
  - cod_vendedor
  - fec_actualizacion_dl
  - ind_cliente_activo
  - ind_material_activo
  - Multiple material and client classification columns
  - Multiple exclusion and substitution columns
  - Multiple boolean flags (ban_pb_*, des_*)

## Target Requirements

- Type: DynamoDB Table
- Location: portafolio-cliente-{environment}
- Format: DynamoDB
- Load strategy: Merge (upsert based on PK+SK)
- Table configuration:
  - Billing Mode: PAY_PER_REQUEST (on-demand)
  - Warm throughput: 4000 write units per second
  - Streams: Enabled with NEW_AND_OLD_IMAGES
  - Point-in-Time Recovery: Enabled
  - Global Secondary Indexes: GSI1, GSI2

### Key Structure

**Primary Key (PK):**
- pk = cod_transaccional (String, required)

**Sort Key (SK):**
- sk = cod_org_vent#cod_canal#cod_vendedor (String, optional)
- Construction: cod_org_vent + "#" + cod_canal + "#" + cod_vendedor
- Example: "CO10#01#V001"

**GSI1:**
- gsi1_pk = cod_org_vent (String, required)
- gsi1_sk = cod_canal#cod_transaccional (String, optional)
- Construction: cod_canal + "#" + cod_transaccional
- Example: "01#12345"

**GSI2:**
- gsi2_pk = cod_vendedor (String, required)
- gsi2_sk = cod_transaccional (String, optional)

### Attributes

- productos: Array/List JSON compressed in GZIP containing materials associated with the client for the combination of cod_transaccional + cod_org_vent + cod_canal + cod_vendedor
- fecha_actualizacion: ISO 8601 timestamp extracted from fec_actualizacion_dl

### Excluded Columns from productos Array

The following columns must NOT be included in the productos array:
- cod_condicion_pago_area_venta
- cod_tipo_jerarquia
- cod_clas_fiscal_cliente_1
- cod_clas_fiscal_cliente_2
- cod_clas_fiscal_material_1
- cod_clas_fiscal_material_2
- cod_categoria
- cod_subcategoria
- cod_linea
- cod_sublinea
- cod_marca
- cod_submarca
- ind_material_activo
- ind_cliente_activo
- cod_secuencia_exclusion
- cod_clase_condicion_exclusion
- cod_secuencia_sustitucion
- cod_clase_condicion_sustitucion
- ban_pb_ind_cliente
- ban_bloqueo_soporte_ind_cliente
- ban_bloqueo_pedido_area_venta_cliente
- ban_pb_area_venta_cliente
- ban_pb_niv_canal_material
- ban_pb_mandante_material
- des_aplica_ibua_en_ventas
- des_calculo_valor_ibua
- des_hash_contenido_registro

## Transformation Requirements

- Complexity: Complex (requires steps directory)
- Transformations:
  1. Filter active records: ind_cliente_activo = true AND ind_material_activo = true
  2. Group by combination: cod_transaccional + cod_org_vent + cod_canal + cod_vendedor
  3. Aggregate productos array: Collect all material records for each combination
  4. Exclude specified columns from productos array
  5. Compress productos array to GZIP JSON
  6. Build DynamoDB keys:
     - pk = cod_transaccional
     - sk = cod_org_vent#cod_canal#cod_vendedor
     - gsi1_pk = cod_org_vent
     - gsi1_sk = cod_canal#cod_transaccional
     - gsi2_pk = cod_vendedor
     - gsi2_sk = cod_transaccional
  7. Extract fecha_actualizacion from fec_actualizacion_dl as ISO 8601 timestamp
  8. Handle deletions: Records that become inactive (ind_cliente_activo = false OR ind_material_activo = false) must be deleted from DynamoDB
- Reference data: None
- Business rules:
  - Only load active records (ind_cliente_activo = true AND ind_material_activo = true)
  - Delete records that become inactive
  - Ensure idempotency: same PK+SK combination updates existing item
  - No duplicates allowed for same PK+SK combination
  - productos array must be GZIP compressed
  - All key fields must be String type

## Flow Behavior

- Use CDC: true
- Change detection: true
- Restart capability: true
- First run detection: Auto-detect (check if target table is empty)
- CDC strategy: iceberg_sp (snapshot comparison)
- CDC date column: fec_actualizacion_dl

## Configuration

- Environment variables:
  - GLUE_CATALOG_NAME: portafolios_iceberg
  - GLUE_CATALOG_DB_STAGE: db_quind_tech_eval_stage_dev
  - DYNAMODB_TABLE_PREFIX: portafolio-cliente-
  - RESOURCE_SUFFIX: (to be determined from environment)
- Error path: s3://bucket/errors/portafolios_dynamodb
- Partitioning: None (DynamoDB doesn't use partitioning)
- Num partitions: 10 (for Spark processing before DynamoDB write)

## Special Requirements

### Idempotency
- Load must be idempotent: repeating the load should not generate duplicate items
- Same keys must update existing item in DynamoDB
- Use DynamoDB PutItem or UpdateItem with proper key matching

### Data Integrity
- Each item must contain at least: pk, sk, gsi1_pk, gsi1_sk, gsi2_pk, gsi2_sk
- productos attribute must be GZIP compressed
- When decompressed, productos must faithfully reflect Iceberg table data for the combination

### Active/Inactive Handling
- Only active records are loaded: ind_cliente_activo = true AND ind_material_activo = true
- Records that become inactive must be deleted from DynamoDB
- CDC must track both inserts/updates and deletes

### Key Construction
- All key fields are String type (S in DynamoDB)
- Use "#" as separator in composite keys
- Handle null/empty values appropriately

## Notes

- This is a complex analytics layer flow that aggregates portfolio data by client combination
- Requires CDC to track changes incrementally
- DynamoDB structure requires careful key construction and GZIP compression
- Must handle both active record loading and inactive record deletion
- GSI indexes enable querying by organization (GSI1) and seller (GSI2)
- Must implement custom loader for DynamoDB; has to do this because Spark doesn't have a loader for this sink.
