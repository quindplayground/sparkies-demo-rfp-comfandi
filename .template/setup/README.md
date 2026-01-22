# Project Setup Scripts

Scripts para configurar un nuevo proyecto desde el template. Automatiza el renombrado de directorios, actualización de imports, y configuración de archivos de proyecto.

## Uso Rápido

```bash
# Ver qué haría sin hacer cambios (recomendado primero)
python .template/setup/setup.py --name mi-proyecto --dry-run

# Ejecución básica (requerido: --name)
python .template/setup/setup.py --name mi-proyecto
```

## Qué Transforma el Script

El script renombra directorios, paquetes y actualiza todas las referencias en el proyecto.

### Directorios

- `template-project` → `{project-name}-project`
- `template_project` → `{project_name}_project`
- `template_project_tests` → `{project_name}_project_tests`

**Nota:** El directorio del proyecto usa guiones (`-`), mientras que los paquetes Python usan guiones bajos (`_`).

### Archivos Actualizados

**`pyproject.toml`**
- ✅ Nombre del proyecto (automático)
- ✅ Referencias al paquete (automático)
- ✅ Rutas de tests (automático)
- ✅ Configuración de coverage (automático)
- ✅ Descripción (si se proporciona `--description`)
- ✅ Autores (si se proporcionan `--author-name` y `--author-email`)
- ✅ Keywords (si se proporciona `--keywords`)

**`REFERENCE.md`**
- ✅ Todos los imports en ejemplos de código
- ✅ Rutas de directorios
- ✅ Referencias a módulos

**`LICENSE`**
- ✅ Año del copyright (automático o con `--year`)
- ✅ Titular de derechos (automático o con `--copyright-holder`)
- ✅ Referencias al nombre del proyecto

**Otros archivos**
- ✅ Todos los imports de Python
- ✅ Referencias en `spark_script.py`
- ✅ Referencias en `README.md` (si existe)

### Ejemplo de Transformación

Si ejecutas con `--name nutresa-compras`:

**Antes:**
```
template-project/
├── template_project/
│   └── libs/
└── template_project_tests/
```

**Después:**
```
nutresa-compras-project/
├── nutresa_compras_project/
│   └── libs/
└── nutresa_compras_project_tests/
```

**Imports:**
```python
# Antes
from template_project.libs import ...

# Después
from nutresa_compras_project.libs import ...
```

## Argumentos del CLI

### Argumentos Requeridos

#### `--name` (requerido)

Nombre del proyecto. Se usa para renombrar directorios y paquetes.

**Ejemplos:**
```bash
--name mi-proyecto
--name nutresa-compras
--name sistema-etl
```

**Transformaciones automáticas:**
- `mi-proyecto` → Directorio: `mi-proyecto-project`
- `mi-proyecto` → Paquete: `mi_proyecto_project`
- `mi-proyecto` → Tests: `mi_proyecto_project_tests`

**Nota:** Los guiones en el nombre se convierten automáticamente a guiones bajos en el código Python.

### Argumentos Opcionales

#### Configuración de `pyproject.toml`

**`--description`**
Descripción del proyecto para el archivo `pyproject.toml`.

```bash
--description "Sistema de procesamiento de datos con Apache Spark"
```

**`--author-name`** y **`--author-email`**
Nombre y email del autor del proyecto. Deben usarse juntos para actualizar los autores en `pyproject.toml`.

```bash
--author-name "Juan Pérez" \
--author-email "juan.perez@example.com"
```

**`--keywords`**
Lista de palabras clave separadas por comas para el proyecto.

```bash
--keywords "pyspark,data-processing,etl,apache-spark"
```

#### Configuración de `LICENSE`

**`--copyright-holder`**
Titular de los derechos de autor en el archivo LICENSE.

```bash
--copyright-holder "Mi Empresa S.A.S."
```

**Por defecto:** Si no se especifica, se usa el nombre del proyecto formateado (ej: `Mi Proyecto`).

**`--year`**
Año del copyright en el archivo LICENSE.

```bash
--year 2025
```

**Por defecto:** Año actual.

#### Opciones Generales

**`--dry-run`**
Ejecuta el script sin hacer cambios. Muestra qué haría sin modificar archivos.

```bash
--dry-run
```

**`--yes`**
Salta la confirmación interactiva y confirma automáticamente los cambios.

```bash
--yes
```

Útil para automatización o cuando ya revisaste los cambios con `--dry-run`.

## Ejemplos de Uso

### Ejemplo 1: Setup Básico

```bash
python .template/setup/setup.py --name mi-proyecto
```

Esto:
- Renombra `template-project` → `mi-proyecto-project`
- Renombra `template_project` → `mi_proyecto_project`
- Actualiza todos los imports y referencias
- Solicita confirmación antes de finalizar

### Ejemplo 2: Con Descripción y Autor

```bash
python .template/setup/setup.py --name mi-proyecto \
  --description "Sistema de procesamiento de datos con Apache Spark" \
  --author-name "Juan Pérez" \
  --author-email "juan.perez@example.com"
```

### Ejemplo 3: Setup Completo

```bash
python .template/setup/setup.py --name mi-proyecto \
  --description "Sistema de procesamiento de datos con Apache Spark" \
  --author-name "Juan Pérez" \
  --author-email "juan.perez@example.com" \
  --keywords "pyspark,data-processing,etl" \
  --copyright-holder "Mi Empresa S.A.S." \
  --year 2025
```

### Ejemplo 4: Verificar Cambios (Dry Run)

```bash
python .template/setup/setup.py --name mi-proyecto \
  --description "Mi descripción" \
  --author-name "Juan Pérez" \
  --author-email "juan@example.com" \
  --dry-run
```

### Ejemplo 5: Setup Automático sin Confirmación

```bash
python .template/setup/setup.py --name mi-proyecto --yes
```

Útil para automatización o cuando ya revisaste los cambios con `--dry-run`.

### Ejemplo 6: Proyecto con Guiones en el Nombre

```bash
python .template/setup/setup.py --name nutresa-compras
```

Los guiones se convierten automáticamente a guiones bajos en el código:
- Directorio: `nutresa-compras-project`
- Paquete: `nutresa_compras_project`
- Tests: `nutresa_compras_project_tests`

## Flujo de Ejecución

1. **Ejecutar el script** con los argumentos deseados
2. **El script realiza las transformaciones:**
   - Renombra directorios
   - Actualiza `pyproject.toml`
   - Actualiza `REFERENCE.md`
   - Actualiza `LICENSE`
   - Actualiza todos los imports en archivos Python
3. **Se muestra un resumen** de los cambios realizados
4. **Confirmación interactiva** (a menos que uses `--yes`):
   - `yes` → Se mantienen los cambios
   - `no` → Se hace rollback automático de todos los cambios
5. **Finalización:** El proyecto está listo para usar

## Pasos Después del Setup

1. **Instalar el paquete:**
   ```bash
   cd {project-name}-project
   pip install -e .
   ```

2. **Verificar instalación:**
   ```bash
   python -c "import {project_name}_project; print({project_name}_project.__version__)"
   ```

3. **Actualizar información del proyecto** (si no se hizo durante el setup):
   - Edita `{project-name}-project/pyproject.toml` con información específica
   - Actualiza `{project-name}-project/REFERENCE.md` si es necesario

## Características

- ✅ **Rollback automático**: Si rechazas los cambios o hay un error, se revierten automáticamente
- ✅ **Confirmación interactiva**: Revisa los cambios antes de confirmarlos
- ✅ **Modo dry-run**: Verifica qué haría sin hacer cambios
- ✅ **Logging estructurado**: Mensajes claros sobre lo que está haciendo
- ✅ **Preservación del template**: El directorio `.template` se mantiene para futuros usos
- ✅ **Idempotente**: Puedes ejecutarlo múltiples veces sin problemas

## Notas Importantes

- El script es **idempotente**: puedes ejecutarlo múltiples veces sin problemas
- Los archivos binarios se omiten automáticamente
- Los directorios `.git` y ocultos se omiten
- El script preserva la estructura y formato de los archivos
- El directorio `.template` se mantiene para permitir crear múltiples proyectos desde el mismo template
- Todos los cambios se rastrean para permitir rollback automático en caso de error
- El template se copia desde `.template/setup/template-project` si existe, preservando el original

## Troubleshooting

### Error: "Directory not found"

- Asegúrate de ejecutar el script desde la raíz del proyecto template
- Verifica que existan los directorios `template-project`, `template_project`, etc.
- Si el template está en `.template/setup/template-project`, el script lo usará automáticamente

### Error: "Permission denied"

- Verifica que tengas permisos de escritura en el directorio
- En Linux/Mac, puede ser necesario usar `chmod +x .template/setup/scripts/setup_project.py`

### Los imports no se actualizaron

- Verifica que el archivo no esté en `.gitignore` o `.cursorignore`
- Algunos archivos binarios se omiten automáticamente

### El script no encuentra los módulos

- Asegúrate de ejecutar desde la raíz del proyecto: `python .template/setup/setup.py --name ...`
- No ejecutes directamente desde `.template/setup/scripts/`

## Referencia Técnica

### Estructura de Scripts

```
.template/setup/
├── setup.py                    # Script principal (orquestador)
└── scripts/
    ├── setup_project.py        # Script principal (orquestador)
    ├── setup_directories.py    # Renombra directorios y módulos
    ├── setup_pyproject.py      # Actualiza pyproject.toml
    ├── setup_reference.py       # Actualiza REFERENCE.md
    ├── setup_license.py         # Actualiza LICENSE
    ├── setup_files.py           # Actualiza todos los demás archivos
    ├── common.py                # Utilidades compartidas
    ├── logger_config.py         # Configuración del sistema de logging
    └── rollback.py              # Gestión de rollback automático
```

### Desarrollo

Para modificar o extender los scripts:

1. **Agregar nuevo módulo de setup**: Crea un nuevo archivo en `.template/setup/scripts/`
2. **Importar en setup_project.py**: Agrega el import y la llamada en `main()`
3. **Mantener compatibilidad**: Asegúrate de que los módulos sigan la misma interfaz

#### Estructura de un módulo de setup

```python
def setup_xxx(file_path: str, ..., dry_run: bool = False,
              logger: Optional[logging.Logger] = None,
              rollback_manager: Optional[RollbackManager] = None) -> bool:
    """Updates XXX file with new project information.

    Args:
        file_path: Path to the file to update.
        ...
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        True if successful, False otherwise.
    """
    log = logger or setup_logger("setup_xxx", dry_run=dry_run)
    
    if not os.path.exists(file_path):
        log.warning(f"File not found at {file_path}")
        return False
    
    # Lógica de actualización
    ...
    
    return True
```

#### Convenciones de código

- **Estilo**: Google Python Style Guide
- **Type hints**: Todos los parámetros y valores de retorno tienen type hints
- **Docstrings**: Estilo Google en inglés para todas las funciones y clases
- **Logging**: Uso de `logging` en lugar de `print` para todos los mensajes
- **Tipos**: Preferencia por `list`, `dict`, `tuple` en lugar de `List`, `Dict`, `Tuple`

#### Módulos principales

**logger_config.py**
Configura el sistema de logging con soporte para modo dry-run.

**rollback.py**
Gestiona el rollback automático de cambios. Rastrea todas las operaciones y puede revertirlas en caso de error.

**common.py**
Funciones utilitarias compartidas:
- `replace_in_file()`: Reemplaza texto en archivos
- `rename_directory()`: Renombra directorios
