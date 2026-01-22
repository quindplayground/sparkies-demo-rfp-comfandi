# Infrastructure as Code (IaC) Scripts

Este directorio contiene scripts reutilizables para empaquetado y despliegue que pueden utilizarse independientemente del framework de IaC que uses (CloudFormation, Terraform, CDK, etc.).

## Objetivo

Este directorio proporciona scripts genéricos que:
- **Empaquetan el proyecto Python** y lo suben a almacenamiento en la nube
- **Instalan el paquete en clusters EMR/Dataproc** durante la inicialización
- Son **agnósticos del framework de IaC** - puedes usarlos con cualquier herramienta
- Son **agnósticos del proveedor de nube** - soportan AWS, GCP, Azure y métodos personalizados

## Estructura

```
iac-refs/
├── README.md                    # Este archivo
├── init_scripts/                # Scripts de inicialización para clusters
│   └── install_package.sh      # Instala el paquete Python desde almacenamiento
└── project/                     # Scripts de empaquetado
    └── package.sh               # Empaqueta el proyecto y sube a almacenamiento
```

## Scripts Disponibles

### `project/package.sh`

Script para empaquetar el proyecto Python y subirlo a almacenamiento en la nube.

**Qué hace:**
1. Detecta automáticamente el directorio del proyecto (busca `pyproject.toml`)
2. Construye el paquete wheel usando `python -m build`
3. Copia archivos adicionales:
   - `spark_script.py` (si existe en la raíz)
   - `deploy/scripts/add_package.sh` (si existe)
   - `deploy/scripts/cloudwatch/` (si existe)
4. (Opcional) Sube a almacenamiento en la nube si `UPLOAD_TO_CLOUD` está configurado

**Uso básico (solo empaquetar):**
```bash
cd iac-refs/project
./package.sh
```

**Variables de entorno configurables:**
- `PROJECT_DIR_NAME`: Nombre del directorio del proyecto (se detecta automáticamente si existe `pyproject.toml`)
- `DIST_DIR_NAME`: Nombre del directorio de distribución (default: `dist`)
- `UPLOAD_TO_CLOUD`: Si está configurado (cualquier valor), intenta subir a la nube (default: no sube)
- `CLOUD_UPLOAD_COMMAND`: Comando personalizado para subir a la nube (opcional)
- `ARTIFACTS_BUCKET`: Nombre del bucket/contenedor de artefactos (para métodos automáticos)
- `ARTIFACTS_PREFIX`: Prefijo/ruta en el almacenamiento (para métodos automáticos)

**Ejemplo con subida a AWS S3:**
```bash
export UPLOAD_TO_CLOUD=1
export ARTIFACTS_BUCKET="my-artifacts-bucket"
export ARTIFACTS_PREFIX="assets/mi-proyecto"
cd iac-refs/project
./package.sh
```

**Ejemplo con comando personalizado:**
```bash
export UPLOAD_TO_CLOUD=1
export CLOUD_UPLOAD_COMMAND='rsync -av dist/ user@server:/path/to/artifacts/'
cd iac-refs/project
./package.sh
```

**Salida esperada:**
```
==========================================
Packaging Project: mi-proyecto-project
Distribution Directory: dist
==========================================
Building mi-proyecto-project package...
mi-proyecto-project package built and copied to dist/.
Packaging additional files...
  ✓ spark_script.py
Package location: /path/to/project/dist/

Uploading to cloud storage...
Uploading to AWS S3...
✅ Package uploaded to s3://my-artifacts-bucket/assets/mi-proyecto/dist/
```

### `init_scripts/install_package.sh`

Script de inicialización para instalar el paquete Python en un cluster EMR/Dataproc.

**Qué hace:**
1. Detecta automáticamente el tipo de almacenamiento (S3, GCS, Azure) o usa el método especificado
2. Descarga el directorio `dist/` desde el almacenamiento al directorio de trabajo
3. Detecta el archivo wheel más reciente (por fecha de modificación)
4. Verifica e instala pip si es necesario
5. Actualiza pip a la última versión
6. Instala el paquete wheel

**Uso:**
Este script se ejecuta automáticamente durante la inicialización del cluster. Recibe como argumento el URI del directorio `dist/` en el almacenamiento.

**Variables de entorno configurables:**
- `TARGET_DIR`: Directorio donde se descargan los archivos (default: `/home/hadoop/working_dir`)
- `PYTHON`: Ruta al ejecutable de Python (default: `/usr/bin/python3.11`)
- `DOWNLOAD_METHOD`: Método de descarga - `auto` (detecta automáticamente), `aws`, `gcp`, `azure`, o `custom` (default: `auto`)
- `CUSTOM_DOWNLOAD_CMD`: Comando personalizado para descargar (solo si `DOWNLOAD_METHOD=custom`)

**Ejemplos de uso:**
```bash
# AWS S3 (detección automática)
./install_package.sh s3://your-bucket/assets/your-project/dist/

# Google Cloud Storage (detección automática)
./install_package.sh gs://your-bucket/assets/your-project/dist/

# Azure Blob Storage (detección automática)
./install_package.sh https://account.blob.core.windows.net/container/path/dist/

# Método personalizado
DOWNLOAD_METHOD=custom CUSTOM_DOWNLOAD_CMD="curl -L -o" ./install_package.sh https://example.com/dist/
```

## Flujo de Trabajo Recomendado

### 1. Configuración Inicial

```bash
# Configurar el prefijo de artefactos según tu proyecto
export ARTIFACTS_PREFIX="assets/mi-proyecto"
export ARTIFACTS_BUCKET="my-artifacts-bucket"  # Si vas a subir a la nube
```

### 2. Empaquetado

```bash
cd iac-refs/project
./package.sh
```

Esto construye el paquete y (opcionalmente) lo sube a almacenamiento en la nube en: `s3://<ARTIFACTS_BUCKET>/<ARTIFACTS_PREFIX>/dist/`

### 3. Integración con tu IaC

Usa el URI del almacenamiento donde se subieron los artefactos en tu configuración de IaC (CloudFormation, Terraform, CDK, etc.) para:
- Configurar el bootstrap action que ejecuta `install_package.sh`
- Referenciar el `spark_script.py` en tus jobs de Spark

## Ejemplos de Integración

### AWS EMR

**CloudFormation:**
```yaml
BootstrapActions:
  - Name: "Install Python Package"
    ScriptBootstrapAction:
      Path: "s3://your-bucket/scripts/install_package.sh"
      Args:
        - "s3://your-bucket/assets/your-project/dist/"
```

**Terraform:**
```hcl
bootstrap_action {
  path = "s3://your-bucket/scripts/install_package.sh"
  args = ["s3://your-bucket/assets/your-project/dist/"]
}
```

**CDK:**
```python
cluster.add_bootstrap_action(
    emr.BootstrapAction(
        name="Install Python Package",
        script_bootstrap_action=emr.ScriptBootstrapActionProps(
            path="s3://your-bucket/scripts/install_package.sh",
            args=["s3://your-bucket/assets/your-project/dist/"]
        )
    )
)
```

### Google Cloud Dataproc

```bash
# En la inicialización del cluster
gcloud dataproc clusters create my-cluster \
  --initialization-actions gs://your-bucket/scripts/install_package.sh \
  --initialization-action-args "gs://your-bucket/assets/your-project/dist/"
```

### Azure HDInsight / Synapse

```bash
# Usar en script de inicialización personalizado
./install_package.sh https://account.blob.core.windows.net/container/path/dist/
```

## Ejemplo Completo

### Paso 1: Empaquetar

**Solo empaquetar (sin subir a la nube):**
```bash
cd iac-refs/project
./package.sh
```

**Con subida a AWS S3:**
```bash
export UPLOAD_TO_CLOUD=1
export ARTIFACTS_BUCKET="my-artifacts-bucket"
export ARTIFACTS_PREFIX="assets/mi-proyecto"
cd iac-refs/project
./package.sh
```

El paquete estará disponible en:
- **Localmente:** `./dist/` (si no subiste a la nube)
- **En la nube:** URI según tu proveedor (ej: `s3://bucket/path/dist/`, `gs://bucket/path/dist/`)

### Paso 2: Usar en tu IaC

Úsalo en tu configuración de IaC para:
1. **Bootstrap Action:** Ejecutar `install_package.sh` con el URI del almacenamiento
2. **Spark Jobs:** Referenciar `spark_script.py` desde el almacenamiento o copiarlo localmente

## Personalización

### Modificar qué archivos se copian

Edita `project/package.sh` en la sección "Packaging additional files":

```bash
# Copiar archivos adicionales necesarios
echo "Packaging additional files..."

# Tu archivo personalizado
if [ -f "$ROOT_DIR/mi_script.py" ]; then
    cp "$ROOT_DIR/mi_script.py" "$ROOT_DIR/$DIST_DIR_NAME"
    echo "  ✓ mi_script.py"
fi

# Directorio completo
if [ -d "$ROOT_DIR/config" ]; then
    cp -r "$ROOT_DIR/config" "$ROOT_DIR/$DIST_DIR_NAME/config"
    echo "  ✓ config/"
fi
```

### Modificar la detección del wheel

En `init_scripts/install_package.sh`, puedes cambiar cómo se detecta el wheel más reciente:

**Opción A (actual):** Por fecha de modificación (más reciente)
```bash
WHEEL_PATH=$(ls -t "$TARGET_DIR"/*.whl 2>/dev/null | head -n1)
```

**Opción B:** Por versión en el nombre (más alta)
```bash
WHEEL_PATH=$(find "$TARGET_DIR" -maxdepth 1 -type f -name "*.whl" | sort -V | tail -n1)
```

### Instalar dependencias adicionales

Si necesitas instalar dependencias adicionales, edita `init_scripts/install_package.sh` y agrega después de instalar el wheel:

```bash
# Instalar dependencias adicionales
echo "Installing additional dependencies..."
sudo $PIP install --no-cache-dir "otra-dependencia==1.0.0"
```

## Troubleshooting

### Error: "No wheel file found"

- Verifica que `package.sh` se haya ejecutado correctamente
- Revisa que el URI en `install_package.sh` sea correcto
- Asegúrate de que el almacenamiento y la ruta existan

### Error: "No se encontró pyproject.toml"

```bash
# Configura manualmente el nombre del directorio del proyecto
export PROJECT_DIR_NAME="tu-proyecto-project"
```

### Error: "AWS CLI no está instalado" (o similar para otros proveedores)

Instala el CLI correspondiente:
- **AWS:** `pip install awscli` o `brew install awscli`
- **Google Cloud:** `pip install gcloud` o seguir [guía oficial](https://cloud.google.com/sdk/docs/install)
- **Azure:** `pip install azure-cli` o seguir [guía oficial](https://docs.microsoft.com/cli/azure/install-azure-cli)
- O usa `DOWNLOAD_METHOD=custom` con un comando personalizado

### Error: "pip not found"

El script intenta instalar pip automáticamente, pero si falla:
- Verifica que Python esté instalado en la ruta especificada
- Revisa los permisos de sudo

## Notas Importantes

1. **Permisos:** Los scripts requieren permisos de ejecución:
   ```bash
   chmod +x iac-refs/project/package.sh
   chmod +x iac-refs/init_scripts/install_package.sh
   ```

2. **Cloud Provider CLIs:** Si usas subida/descarga automática, asegúrate de tener el CLI correspondiente instalado y configurado:
   - **AWS:** `aws configure`
   - **Google Cloud:** `gcloud auth login`
   - **Azure:** `az login`

3. **Sin dependencias de nube:** Los scripts funcionan sin subir a la nube. Solo empaqueta localmente si no configuras `UPLOAD_TO_CLOUD`.

4. **Testing:** Prueba los scripts localmente antes de usarlos en producción.

5. **Versionado:** El script detecta automáticamente el wheel más reciente. Si necesitas una versión específica, modifica la lógica de detección.

## Integración con Diferentes Frameworks y Proveedores

Estos scripts son agnósticos del framework de IaC y del proveedor de nube. Puedes usarlos con:

### Frameworks de IaC

- **CloudFormation:** Usa los scripts en BootstrapActions
- **Terraform:** Usa los scripts en `bootstrap_action` blocks
- **CDK:** Usa los scripts en `addBootstrapAction()`
- **Pulumi:** Usa los scripts en la configuración de bootstrap
- **Otros:** Cualquier framework que soporte bootstrap actions

### Proveedores de Nube

- **AWS:** S3 para almacenamiento, EMR para clusters
- **Google Cloud:** Cloud Storage para almacenamiento, Dataproc para clusters
- **Azure:** Blob Storage para almacenamiento, HDInsight/Synapse para clusters
- **Otros:** Usa `CUSTOM_DOWNLOAD_CMD` para cualquier otro método

### Flujo General

1. Ejecutar `package.sh` para empaquetar (opcionalmente subir a la nube)
2. Usar el URI resultante o la ruta local en tu configuración de IaC para el bootstrap action
3. El script `install_package.sh` detecta automáticamente el tipo de almacenamiento o usa el método configurado
