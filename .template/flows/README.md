# Flow Implementation Orchestration

Scripts y herramientas para automatizar la implementación de flujos de datos usando comandos de Cursor.

## Descripción

Este directorio contiene scripts para orquestar la implementación completa de flujos de datos siguiendo el patrón del template. Los scripts ejecutan comandos de Cursor en secuencia para implementar todos los módulos de un flujo (extract, transform, load, job) de manera automatizada.

## Requisitos Previos

1. **Cursor IDE instalado** (o VS Code como alternativa)
2. **Comandos de Cursor disponibles** en `.cursor/commands/`
3. **Template de flujo** en `template-project/template_project/flows/_template_flow/`

## Uso Rápido

```bash
# 1. Crear archivo de requerimientos (usar EXAMPLE_REQUIREMENTS.md como base)
cp .template/flows/EXAMPLE_REQUIREMENTS.md my_flow_requirements.md
# Editar my_flow_requirements.md con tus requerimientos

# 2. Verificar qué se ejecutará (dry-run - recomendado primero)
.template/flows/scripts/orchestrate_flow.sh --requirements my_flow_requirements.md --dry-run

# 3. Ejecutar implementación completa
.template/flows/scripts/orchestrate_flow.sh --requirements my_flow_requirements.md
```

## Archivo de Requerimientos

El script requiere un archivo markdown (`.md`) que contenga toda la información necesaria para implementar el flujo. Este archivo se pasa a cada comando de Cursor como contexto.

### Cómo Crear el Archivo

Puedes crear un archivo de requerimientos desde cero o usar la plantilla:

```bash
# Opción 1: Copiar la plantilla
cp .template/flows/EXAMPLE_REQUIREMENTS.md my_flow_requirements.md

# Opción 2: Crear desde cero
cat > requirements/my_flow.md << 'EOF'
# Flow Requirements

## Flow Information
- Name: my_flow_name
- Purpose: Description of what this flow does
- Layer: Bronze

## Source Requirements
- Type: Table
- Location: catalog.database.table
...

EOF
```

### Formato del Archivo

El archivo debe contener toda la información necesaria para implementar el flujo. Ejemplo de estructura:

```markdown
# Flow Requirements

## Flow Information
- Name: customers_bronze
- Purpose: Extract and load raw customer data from source system
- Layer: Bronze

## Source Requirements
- Type: Table
- Location: catalog.database.customers_source
- Format: Iceberg
- Schema: customer_id, name, email, registration_date
- Extraction mode: Full

## Target Requirements
- Type: Table
- Location: catalog.database.customers_bronze
- Format: Iceberg
- Load strategy: Overwrite
- Schema: customer_id, name, email, registration_date, current_timestamp_dwh

## Transformation Requirements
- Complexity: Simple (inline)
- Transformations:
  - Remove duplicates on customer_id
  - Cast registration_date to date type
  - Add current_timestamp_dwh column
  - Normalize name and email (trim, uppercase)

## Flow Behavior
- Use CDC: false
- Change detection: false
- Restart capability: false

## Configuration
- Environment variables:
  - GLUE_CATALOG_NAME: my_catalog
  - GLUE_CATALOG_DB_STAGE: stage_db
- Error path: s3://bucket/errors/customers_bronze
- Partitioning: None
```

### Secciones Requeridas

El archivo debe incluir al menos:

1. **Flow Information**: Nombre, propósito, capa (Bronze/Silver/Gold)
2. **Source Requirements**: Tipo, ubicación, formato, esquema, modo de extracción
3. **Target Requirements**: Tipo, ubicación, formato, estrategia de carga, esquema
4. **Transformation Requirements**: Complejidad, transformaciones necesarias
5. **Flow Behavior**: Configuración de CDC, detección de cambios, restart (solo si se requiere)
6. **Configuration**: Variables de entorno, rutas de error, particionado

## Guía Paso a Paso

### Paso 1: Preparar Requerimientos

```bash
# Crear directorio para requerimientos (opcional)
mkdir -p requirements

# Crear archivo de requerimientos desde la plantilla
cp .template/flows/EXAMPLE_REQUIREMENTS.md requirements/my_flow.md

# Editar con tus requerimientos
code requirements/my_flow.md
# o
nano requirements/my_flow.md
```

### Paso 2: Validar con Dry Run

Antes de ejecutar, es recomendable hacer un dry-run para ver qué se ejecutará:

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/my_flow.md \
  --dry-run
```

Esto mostrará:
- Qué comandos se ejecutarán
- En qué orden
- Qué archivos se usarán
- Sin hacer cambios reales

### Paso 3: Ejecutar la Orquestación

Una vez verificado, ejecuta el script:

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/my_flow.md
```

#### Durante la Ejecución

El script:
1. Validará el archivo de requerimientos
2. Mostrará un resumen de los requerimientos
3. Mostrará el plan de ejecución
4. Pedirá confirmación
5. Ejecutará cada comando en secuencia
6. Esperará tu confirmación después de cada comando

#### Interacción con Cursor

- Si Cursor CLI está disponible: intentará ejecutar comandos automáticamente
- Si no: abrirá los archivos en Cursor IDE y esperará que ejecutes el comando manualmente
- El archivo de requerimientos estará disponible como contexto

### Paso 4: Revisar Implementación

Después de cada comando:
- Revisa los cambios realizados
- Verifica que el código sea correcto
- Confirma antes de continuar

### Paso 5: Verificar y Probar

Después de completar la orquestación:

1. **Revisar el flujo implementado**
   ```bash
   ls template-project/template_project/flows/{flow_name}/
   ```

2. **Verificar configuración**
   ```bash
   cat template-project/template_project/flows/{flow_name}/config/default.toml
   ```

3. **Ejecutar tests** (si no se ejecutaron automáticamente)
   ```bash
   cd template-project
   pytest template_project_tests/flows/{flow_name}/ -v
   ```

4. **Probar el flujo**
   ```python
   from template_project.flows.{flow_name}.job import {flow_name}_job
   # ... ejecutar con datos de prueba
   ```

## Opciones del Script

### Argumentos Requeridos

**`--requirements <file.md>`**
Archivo markdown con todos los requerimientos del flujo.

### Opciones

**`--dry-run`**
Muestra qué comandos se ejecutarían sin ejecutarlos realmente.

**`--skip-tests`**
Omite la creación y ejecución de tests unitarios.

**`--skip-optimize`**
Omite el paso de optimización del flujo.

**`--start-from <command>`**
Inicia la ejecución desde un comando específico. Útil para continuar una implementación interrumpida.

**`--help`**
Muestra la ayuda del script.

## Comandos Ejecutados

El script ejecuta los siguientes comandos en orden:

1. **setup_flow_structure**
   - Copia el template
   - Configura estructura básica
   - Actualiza referencias iniciales

2. **implement_extract**
   - Implementa lógica de extracción
   - Configura según source requirements

3. **implement_transform**
   - Implementa transformaciones
   - Organiza en steps si es complejo

4. **implement_load**
   - Implementa lógica de carga
   - Configura overwrite/merge según requirements

5. **implement_job**
   - Implementa orquestación
   - Configura lógica específica según requirements

6. **optimize_flow** (opcional con `--skip-optimize`)
   - Optimiza transformaciones
   - Aplica mejores prácticas de Spark

7. **implement_unit_tests** (opcional con `--skip-tests`)
   - Crea tests unitarios
   - Configura fixtures y mocks

8. **run_and_fix_tests** (opcional con `--skip-tests`)
   - Ejecuta tests
   - Corrige fallos iterativamente

9. **review_flow_implementation**
   - Revisa la implementación completa
   - Compara requerimientos vs implementación
   - Redirige a steps específicos si hay problemas

## Ejemplos de Uso

### Ejemplo 1: Implementación Completa

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/customers_bronze.md
```

### Ejemplo 2: Solo Validación (Dry Run)

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/customers_bronze.md \
  --dry-run
```

### Ejemplo 3: Sin Tests

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/customers_bronze.md \
  --skip-tests
```

### Ejemplo 4: Continuar desde un Punto Específico

Si la implementación se interrumpió, puedes continuar desde un comando específico:

```bash
# Continuar desde transform (ya se hizo setup y extract)
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/my_flow.md \
  --start-from implement_transform
```

### Ejemplo 5: Solo Optimización y Tests

Si ya implementaste todo manualmente y solo quieres optimizar y testear:

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/my_flow.md \
  --start-from optimize_flow
```

### Ejemplo 6: Sin Optimización

```bash
.template/flows/scripts/orchestrate_flow.sh \
  --requirements requirements/my_flow.md \
  --skip-optimize
```

## Paso de Outputs Entre Comandos

El script captura outputs estructurados en formato JSON de cada comando y los pasa a los comandos siguientes como contexto. Esto asegura continuidad y permite que comandos posteriores usen información de implementaciones anteriores.

### Estructura del Output

Cada comando debe proporcionar un resumen JSON con:
- `status`: 'success' o 'error'
- `files_created`: Lista de rutas de archivos creados
- `files_modified`: Lista de rutas de archivos modificados
- `key_decisions`: Decisiones importantes de implementación
- `schema_info`: Información de esquemas de entrada/salida (si aplica)
- `next_steps`: Información que el siguiente comando debe conocer
- `errors`: Lista de errores (si hay)

**Ejemplo de output:**
```json
{
  "status": "success",
  "files_created": [
    "template-project/template_project/flows/my_flow/extract.py"
  ],
  "files_modified": [
    "template-project/template_project/flows/my_flow/config/default.toml"
  ],
  "key_decisions": [
    "Usando extracción incremental con Iceberg CDC",
    "Tabla fuente: catalog.db.table"
  ],
  "schema_info": {
    "input_schema": {
      "columns": ["id", "name", "updated_at"]
    }
  },
  "next_steps": [
    "El módulo transform debe manejar deduplicación por id",
    "El esquema de salida debe incluir columnas calculadas"
  ]
}
```

Los outputs se guardan en `.template/flows/.temp_outputs/` para referencia y depuración.

## Troubleshooting

### Error: "Requirements file not found"

```bash
# Usa ruta absoluta
.template/flows/scripts/orchestrate_flow.sh \
  --requirements "$(pwd)/requirements/my_flow.md"
```

### Error: "Command file not found"

Verifica que los comandos existan:
```bash
ls .cursor/commands/
```

Asegúrate de estar en la raíz del proyecto.

### Cursor CLI no disponible

El script abrirá los archivos en Cursor IDE. Ejecuta los comandos manualmente:
1. El comando se abre en Cursor
2. El archivo de requerimientos está disponible
3. Ejecuta el comando en Cursor
4. Presiona Enter para continuar

### Continuar después de interrupción

```bash
# Identifica el último comando completado
# Luego continúa desde el siguiente
.template/flows/scripts/orchestrate_flow.sh \
  --requirements my_flow.md \
  --start-from implement_load  # ejemplo
```

## Consejos

1. **Siempre haz dry-run primero** para verificar el plan
2. **Revisa cada comando** antes de continuar
3. **Guarda el archivo de requerimientos** para referencia futura
4. **Usa versionado** para los archivos de requerimientos
5. **Documenta cambios** si modificas algo manualmente

## Notas

- El script requiere que Cursor IDE esté instalado
- Los comandos se ejecutan en secuencia, cada uno espera confirmación
- El archivo de requerimientos se pasa como contexto a cada comando
- El script valida que todos los prerrequisitos estén cumplidos antes de ejecutar

## Estructura

```
.template/flows/
├── README.md                    # Este archivo (documentación completa)
├── EXAMPLE_REQUIREMENTS.md      # Ejemplo de archivo de requerimientos
└── scripts/
    └── orchestrate_flow.sh      # Script de orquestación
```
