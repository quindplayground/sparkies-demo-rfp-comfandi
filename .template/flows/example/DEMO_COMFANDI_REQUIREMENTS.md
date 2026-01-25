# Especificación en lenguaje natural (HU / Instrucciones) para un ETL en Spark que consume la API de datos.gov.co (Socrata SODA v3)

> **Objetivo**: Estas instrucciones están diseñadas para un **agente generador de código Spark**.  
> El agente debe producir un job/pipeline **end-to-end**: **extraer** desde la API SODA v3 con **App Token**, **procesar** (incluyendo agregaciones complejas) y **escribir** en tablas analíticas con estrategia idempotente (MERGE/UPSERT).

---

## 1) Alcance y resultado esperado

### 1.1 Qué debe construir el agente (deliverables)
1. Un **job de Spark** (batch) que:
   - Consuma la API SODA v3 del dataset `ese3-e6sh` con **POST** y **paginación**.
   - Aplique **tipado, estandarización, reglas de calidad** y genere una capa “clean” (**Silver**).
   - Calcule una capa **Gold** con **KPIs y agregaciones complejas** (tendencias, shares, HHI, rankings, anomalías).
   - Escriba resultados en una o más **tablas** (formato lakehouse recomendado: Iceberg/Delta/Hudi).
2. Una **tabla de control** para watermark/observabilidad del pipeline.
3. Logging y métricas básicas por corrida.

### 1.2 Qué NO debe asumir el agente
- No asumir que el dataset es pequeño (debe soportar paginación y límites).
- No asumir que siempre se puede traer “todo”; debe existir modo incremental/backfill.
- No asumir que todos los campos vienen completos (manejo de nulos y tipos robusto).

---

## 2) Contrato de fuente (API) — **OBLIGATORIO / NO NEGOCIABLE**

### 2.1 Endpoint
- **URL**: `https://www.datos.gov.co/api/v3/views/ese3-e6sh/query.json`
- **Método**: `POST`

### 2.2 Autenticación (App Token)
- Enviar el token en header:
  - `X-App-Token: <APP_TOKEN>`
- El token **debe** provenir de un secreto (env var / secret manager).  
  **Nunca** hardcodearlo ni imprimirlo en logs.

### 2.3 Headers requeridos
- `Content-Type: application/json`
- `Accept: application/json`
- `X-App-Token: <APP_TOKEN>`

### 2.4 Body del request (JSON)
Debe incluir, como mínimo:
- `query`: string SoQL
- `page`: objeto con:
  - `pageNumber`: entero **inicia en 1**
  - `pageSize`: entero (sugerido 1000–5000)
- Recomendado:
  - `includeSynthetic`: `false` (para evitar campos sintéticos)
  - `orderingSpecifier`: `"discard"` (mejor performance si no se requiere orden estable)

#### 2.4.1 Plantilla de payload (referencia)
```json
{
  "query": "SELECT a_o, mes, ccf, empresas_afiliadas, total_afiliados_cajas, trabajadores_afiliados, afiliados_facultativos, afiliados_pensionados, afiliados_fidelidad, no_afiliados_con_derecho, personas_cargo_2, total_poblaci_n_cubierta",
  "page": { "pageNumber": 1, "pageSize": 5000 },
  "includeSynthetic": false,
  "orderingSpecifier": "discard"
}
```

### 2.5 Paginación (cómo debe implementarse)
- Empezar con `pageNumber = 1`.
- Repetir requests incrementando `pageNumber` hasta que:
  - la página devuelva **cero filas**, o
  - el número de filas devueltas sea **< pageSize**.
- El pipeline debe **consolidar** todas las páginas en un único dataset de entrada.

### 2.6 Manejo de rate limits, errores y retries (OBLIGATORIO)
- Para status codes: `429`, `500`, `502`, `503`, `504`:
  - Reintentar con **exponential backoff** (p.ej. 1.5^intento) con tope.
  - Si existe header `Retry-After`, respetarlo.
- Para otros `4xx` (excepto 429):
  - Considerar error no recuperable (fallar con mensaje claro).
- Timeouts:
  - Definir `timeout` razonable (p.ej. 60s).
- Observabilidad mínima por request:
  - `pageNumber`, `pageSize`, filas recibidas, latencia, #retries.

---

## 3) Dataset: columnas y tipado esperado

### 3.1 Columnas origen (12)
**Claves temporales / dimensión**
- `a_o` (Año) → entero
- `mes` (Mes) → entero 1..12
- `ccf` (Caja de Compensación Familiar) → string

**Métricas (todas son totales del mes, NO acumulables)**
- `empresas_afiliadas` → numérico (entero >= 0)
- `total_afiliados_cajas` → numérico (entero >= 0)
- `trabajadores_afiliados` → numérico (entero >= 0)
- `afiliados_facultativos` → numérico (entero >= 0)
- `afiliados_pensionados` → numérico (entero >= 0)
- `afiliados_fidelidad` → numérico (entero >= 0)
- `no_afiliados_con_derecho` → numérico (entero >= 0)
- `personas_cargo_2` → numérico (entero >= 0)
- `total_poblaci_n_cubierta` → numérico (entero >= 0)

### 3.2 Reglas de negocio relevantes
- Los valores son **snapshot mensual** (no sumar meses como si fuera acumulado anual sin advertencia).
- Identificador natural del snapshot: **(a_o, mes, ccf)**.

---

## 4) Parámetros del pipeline (para ejecución flexible)

El agente debe generar un job parametrizable con, al menos:

### 4.1 Parámetros de extracción
- `app_token_secret_ref`: referencia a secreto o variable de entorno
- `page_size`: default 5000
- `max_pages` (opcional, para pruebas)
- `soql_base_select`: SELECT explícito con las 12 columnas
- `ordering_specifier`: default `"discard"`
- `include_synthetic`: default `false`

### 4.2 Parámetros de carga incremental
- `load_mode`: `full | incremental`
- `watermark_strategy`: `control_table | manual`
- `start_year`, `start_month`, `end_year`, `end_month` (si manual)
- `backfill_months`: default 3 (para incremental robusto)

### 4.3 Parámetros de escritura
- `catalog_db`, `table_silver`, `table_gold`, `table_control`
- `table_format`: `iceberg | delta | hudi` (según stack)
- `write_mode`: `merge | overwrite_partitions` (merge recomendado)

---

## 5) Diseño de tablas (propuesta concreta)

> Si tu plataforma ya tiene convención, el agente puede adaptar, pero **debe** mantener los granos y llaves.

### 5.1 Tabla Bronze (opcional pero recomendada)
**Nombre sugerido**: `tbl_bronze_ssf_poblacion_subsidio_familiar_raw`  
**Grano**: filas tal como llegan de la API (por página)  
**Campos mínimos adicionales (metadatos)**
- `ingestion_ts` (timestamp)
- `job_run_id` (string)
- `source_endpoint` (string)
- `page_number` (int)
- `raw_record` (string/json) o columnas “tal cual” + metadatos

**Propósito**: auditoría, replay y troubleshooting.

### 5.2 Tabla Silver (requerida)
**Nombre sugerido**: `tbl_silver_ssf_poblacion_subsidio_familiar_mensual`  
**Grano**: 1 fila por `(a_o, mes, ccf)`  
**Partición**: `a_o`, `mes`  
**Campos**
- Todas las 12 columnas tipadas/limpias
- `year_month` (string `YYYY-MM` o int `YYYYMM`) para ventanas
- Flags DQ:
  - `dq_is_valid_month`
  - `dq_non_negative`
  - `dq_total_cubierta_consistente`
  - `dq_has_duplicate_key`
- `ingestion_ts`, `job_run_id` (para trazabilidad)

### 5.3 Tabla Gold (requerida)
**Nombre sugerido**: `tbl_gold_ssf_kpis_cobertura_mensual`  
**Grano**:
- 1 fila por `(a_o, mes, ccf)` con KPIs
- Además, fila “Total País” por `(a_o, mes, ccf='__TOTAL_PAIS__')`

**Partición**: `a_o`, `mes`  
**Campos (mínimos)**
- `a_o`, `mes`, `ccf`, `year_month`
- Métricas base: `total_poblaci_n_cubierta`, `total_afiliados_cajas`, `personas_cargo_2`, `empresas_afiliadas`, etc.
- KPIs derivados (ver sección 7)
- Rankings y anomalías (ver sección 7)
- `ingestion_ts`, `job_run_id`

### 5.4 Tabla Control (requerida)
**Nombre sugerido**: `tbl_ctl_ssf_etl_runs`  
**Campos mínimos**
- `pipeline_name`
- `job_run_id`
- `start_ts`, `end_ts`
- `status` (`SUCCESS|FAILED`)
- `watermark_year`, `watermark_month`
- `rows_read`, `rows_silver`, `rows_gold`
- `pages_consumed`, `retries_count`, `http_429_count`, `http_5xx_count`
- `dq_invalid_count`, `dq_warning_count`

---

## 6) Flujo general del ETL (paso a paso)

### Paso 0 — Inicialización
1. Crear `job_run_id` único (UUID).
2. Resolver parámetros (modo de carga, rango temporal, page_size, etc.).
3. Leer App Token desde secreto.

### Paso 1 — Construcción de SoQL (pushdown en origen)
- El agente debe construir un `SELECT` **explícito** con las 12 columnas.
- En `incremental`:
  - Agregar `WHERE` por rango de (año/mes).
  - Incluir backfill N meses.
- Debe evitar traer campos no usados.

**Regla importante**: como la API trabaja con SoQL, el filtro ideal es por `a_o` y `mes`.
- Ejemplo conceptual:
  - “desde (a_o, mes) >= watermark-backfill”
  - “hasta (a_o, mes) <= end”

> Si el agente decide filtrar por lista explícita de meses (IN), debe manejar rangos grandes de forma eficiente.

### Paso 2 — Extracción paginada
1. Ejecutar POST con `pageNumber=1`.
2. Concatenar resultados hasta terminar paginación.
3. Guardar métricas de extracción y, si existe Bronze, persistir también.

### Paso 3 — Normalización / Tipado / Limpieza (Silver staging)
- Convertir tipos:
  - `a_o`, `mes` a entero
  - métricas a entero (o decimal si se requiere)
- Normalizar `ccf`:
  - trim
  - mayúsculas
  - colapsar espacios
- Generar `year_month`:
  - `YYYY-MM` o `YYYYMM` (estable y ordenable)
- Deduplicar por key:
  - clave `a_o, mes, ccf`
  - si duplicados, conservar el registro con `ingestion_ts` mayor (o estrategia determinística)

### Paso 4 — Reglas de calidad (DQ) y enrutamiento
Aplicar al menos:
1. `dq_is_valid_month`: `mes` entre 1 y 12
2. `dq_non_negative`: todas las métricas >= 0
3. `dq_total_cubierta_consistente`:
   - `total_poblaci_n_cubierta == total_afiliados_cajas + personas_cargo_2`
   - si no cumple: marcar warning (no necesariamente descartar)
4. Null checks: `a_o`, `mes`, `ccf` no nulos

**Salida**
- Dataset válido → Silver
- Dataset inválido crítico (p.ej. null en clave) → tabla de rechazados (si se implementa) y métricas DQ

### Paso 5 — Persistir Silver (idempotente)
- Estrategia recomendada: `MERGE` por `(a_o, mes, ccf)`
- Alternativa: `overwrite` de particiones `(a_o, mes)` para el rango cargado

**Requisito**: re-ejecutar el mismo rango **no** debe duplicar.

### Paso 6 — Construcción de Gold (agregaciones complejas)
- A partir de Silver, calcular KPIs (sección 7).
- Generar filas `__TOTAL_PAIS__` por (a_o, mes) con agregación sumatoria consistente.
- Calcular concentración (HHI) y rankings.

### Paso 7 — Persistir Gold (idempotente)
- `MERGE` por `(a_o, mes, ccf)` incluyendo `__TOTAL_PAIS__`.

### Paso 8 — Control/Observabilidad
- Escribir registro en `tbl_ctl_ssf_etl_runs`.
- Actualizar watermark al último (a_o, mes) cargado con éxito.

---

## 7) Procesamiento “complejo” (KPIs y agregaciones avanzadas)

> Todas las divisiones deben ser “safe divide” (si denominador=0 → null o 0 según regla).

### 7.1 KPIs de composición (por CCF/mes)
- `share_dependientes = trabajadores_afiliados / total_afiliados_cajas`
- `share_independientes = afiliados_facultativos / total_afiliados_cajas`
- `share_pensionados = afiliados_pensionados / total_afiliados_cajas`
- `share_fidelidad = afiliados_fidelidad / total_afiliados_cajas`
- `share_no_afiliados_derecho = no_afiliados_con_derecho / total_afiliados_cajas`

### 7.2 KPIs de cobertura familiar
- `cargas_por_afiliado = personas_cargo_2 / total_afiliados_cajas`
- `cobertura_por_afiliado = total_poblaci_n_cubierta / total_afiliados_cajas`
- `gap_cobertura = total_poblaci_n_cubierta - (total_afiliados_cajas + personas_cargo_2)`
  - (debe ser 0 si la fuente es consistente; si no, sirve para auditoría)

### 7.3 Productividad empresarial
- `afiliados_por_empresa = total_afiliados_cajas / empresas_afiliadas`
- `cubiertos_por_empresa = total_poblaci_n_cubierta / empresas_afiliadas`

### 7.4 Tendencias MoM y YoY (por CCF)
> Orden por `year_month`.

- `mom_cubierta_abs = cubierta_mes - cubierta_mes_anterior`
- `mom_cubierta_pct = (cubierta_mes - cubierta_mes_anterior) / cubierta_mes_anterior`
- `yoy_cubierta_abs = cubierta_mes - cubierta_mismo_mes_año_anterior`
- `yoy_cubierta_pct = (cubierta_mes - cubierta_mismo_mes_año_anterior) / cubierta_mismo_mes_año_anterior`

Aplicar lo mismo (si se desea) para:
- `total_afiliados_cajas`
- `empresas_afiliadas`
- `personas_cargo_2`

### 7.5 Promedios móviles (suavizado) (por CCF)
- `ma_3m_cubierta = avg(cubierta) over last 3 months`
- `ma_6m_cubierta = avg(cubierta) over last 6 months`
- `ma_12m_cubierta = avg(cubierta) over last 12 months`

### 7.6 Índice estacional (por CCF)
- `avg_anual_cubierta_ccf = avg(cubierta) over (partition by ccf, a_o)`
- `seasonality_index = cubierta_mes / avg_anual_cubierta_ccf`

### 7.7 “Total País” y participación de mercado (por mes)
1. Para cada `(a_o, mes)`:
   - `cubierta_total_pais = sum(total_poblaci_n_cubierta)`
2. Para cada CCF:
   - `market_share_ccf = total_poblaci_n_cubierta / cubierta_total_pais`

### 7.8 Concentración: HHI (por mes) — **complejo y valioso**
- `hhi_cobertura = sum(market_share_ccf ^ 2)` por `(a_o, mes)`
- Guardar `hhi_cobertura` en:
  - fila `__TOTAL_PAIS__`, y/o
  - repetirlo en todas las filas del mes (según preferencia)

### 7.9 Rankings (por mes)
- `rank_cubierta = rank() over (partition by a_o, mes order by total_poblaci_n_cubierta desc)`
- `rank_afiliados = rank() ... total_afiliados_cajas desc`
- `quartile_cubiertos_por_empresa` usando `ntile(4)` (por mes)

### 7.10 Detección de anomalías (por CCF)
- Calcular z-score de `mom_cubierta_pct` por CCF (en ventana larga o global):
  - `z = (x - mean) / stddev`
- Flag:
  - `is_anomaly_mom = abs(z) >= 3` (ajustable)

---

## 8) Reglas de ingeniería (cómo debe generar el código Spark)

### 8.1 Estructura recomendada del código
- Módulos/funciones separadas:
  - `api_client`: requests/paginación/retries
  - `schema`: definición de schema Spark estable
  - `transform_silver`: limpieza y DQ
  - `transform_gold`: KPIs y ventanas
  - `writer`: merge/overwrite y control table
  - `main`: orquestación

### 8.2 Requisitos de estilo
- Type hints (PEP 484) en funciones principales.
- Variables en `snake_case` en inglés.
- Logs estructurados (clave=valor).
- No imprimir secretos.

### 8.3 Consideraciones Spark
- La extracción desde API no debe ejecutarse como una acción por partición de Spark (evitar N requests por executor).
  - Patrón recomendado:
    1) extraer en driver en lotes/páginas
    2) paralelizar (si aplica) a través de `spark.createDataFrame(rows)` o escribir Bronze y luego leer con Spark
- Para datasets grandes:
  - descargar páginas a almacenamiento (S3/GCS/ADLS/HDFS) en archivos y luego leer con Spark (más robusto).
- Ventanas:
  - construir un campo ordenable `year_month` para `orderBy`.

---

## 9) Idempotencia y consistencia

### 9.1 Idempotencia
- Re-ejecutar el mismo rango temporal debe producir el mismo estado final.
- Evitar duplicados por clave `(a_o, mes, ccf)`.

### 9.2 Estrategias permitidas
- `MERGE INTO` (recomendado) por clave.
- `overwrite` por particiones (a_o, mes) del rango cargado.

---

## 10) Pruebas mínimas (para el generador)
El agente debe incluir pruebas o validaciones ejecutables (según tu estándar) para:
- Construcción de SoQL por rangos (incremental/backfill).
- Lógica de paginación (terminación correcta).
- DQ: meses fuera de rango, negativos, inconsistencia de cubierta.
- Cálculo de KPIs con denominadores cero.

---

## 11) Checklist de “hecho” (Definition of Done)

- [ ] Consume `https://www.datos.gov.co/api/v3/views/ese3-e6sh/query.json` vía POST con `X-App-Token`
- [ ] Implementa paginación `pageNumber` desde 1, termina cuando filas < pageSize
- [ ] Implementa retries con backoff para 429 y 5xx
- [ ] Silver tipada, deduplicada, con DQ flags y particionada por (a_o, mes)
- [ ] Gold con KPIs avanzados: shares, ratios, MoM/YoY, moving averages, estacionalidad, HHI, rankings, anomalías
- [ ] Escritura idempotente (MERGE u overwrite de particiones)
- [ ] Control table con métricas por corrida y watermark actualizado
- [ ] Token manejado como secreto y sin filtraciones en logs

---

## 12) SoQL recomendado (base)

**SELECT explícito (mínimo)**
```sql
SELECT a_o, mes, ccf,
       empresas_afiliadas, total_afiliados_cajas, trabajadores_afiliados,
       afiliados_facultativos, afiliados_pensionados, afiliados_fidelidad,
       no_afiliados_con_derecho, personas_cargo_2, total_poblaci_n_cubierta
```

**Filtro incremental (conceptual)**
- Agregar cláusulas `WHERE` por `a_o` y `mes` para rango objetivo + backfill.

---

> Fin de la especificación.