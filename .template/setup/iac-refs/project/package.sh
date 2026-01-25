#!/bin/bash
# Script para empaquetar el proyecto Python
# 
# Este script:
# 1. Construye el paquete wheel del proyecto
# 2. Copia archivos necesarios al directorio dist/
# 3. (Opcional) Sube todo a un almacenamiento en la nube
#
# Variables de entorno configurables:
# - PROJECT_DIR_NAME: Nombre del directorio del proyecto (default: se detecta automáticamente)
# - DIST_DIR_NAME: Nombre del directorio de distribución (default: dist)
# - UPLOAD_TO_CLOUD: Si está configurado, intenta subir a la nube (default: no)
# - CLOUD_UPLOAD_COMMAND: Comando personalizado para subir a la nube

set -e

# Configuración
DIST_DIR_NAME="${DIST_DIR_NAME:-dist}"

# Navegar al directorio raíz del proyecto
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

ROOT_DIR=$(pwd)

# Detectar nombre del proyecto (directorio que contiene pyproject.toml)
if [ -z "$PROJECT_DIR_NAME" ]; then
    PROJECT_DIR_NAME=$(find . -maxdepth 2 -name "pyproject.toml" -type f | head -1 | xargs dirname | xargs basename)
    if [ -z "$PROJECT_DIR_NAME" ]; then
        echo "Error: No se encontró pyproject.toml. Por favor, configura PROJECT_DIR_NAME manualmente."
        exit 1
    fi
fi

echo "=========================================="
echo "Packaging Project: $PROJECT_DIR_NAME"
echo "Distribution Directory: $DIST_DIR_NAME"
echo "=========================================="

# Limpiar y crear directorio de distribución
echo "Removing $DIST_DIR_NAME and intermediate config directories..."
rm -rf "$ROOT_DIR/$DIST_DIR_NAME"
mkdir -p "$ROOT_DIR/$DIST_DIR_NAME"

# Construir paquete wheel
echo "Building $PROJECT_DIR_NAME package..."
cd "$ROOT_DIR/$PROJECT_DIR_NAME" || exit 1

if ! command -v build &> /dev/null; then
    echo "Installing build package..."
    pip install build
fi

python -m build --wheel

# Copiar wheel al directorio de distribución
if [ ! -d "$ROOT_DIR/$PROJECT_DIR_NAME/dist" ]; then
    echo "Error: No se generó el directorio dist/ en $PROJECT_DIR_NAME"
    exit 1
fi

cp "$ROOT_DIR/$PROJECT_DIR_NAME/dist/"*.whl "$ROOT_DIR/$DIST_DIR_NAME/" || exit 1
echo "$PROJECT_DIR_NAME package built and copied to $DIST_DIR_NAME/."

cd "$ROOT_DIR" || exit 1

# Copiar archivos adicionales necesarios
echo "Packaging additional files..."

# Copiar spark_script.py si existe
if [ -f "$ROOT_DIR/spark_script.py" ]; then
    cp "$ROOT_DIR/spark_script.py" "$ROOT_DIR/$DIST_DIR_NAME"
    echo "  ✓ spark_script.py"
fi

# Copiar scripts adicionales si existen (ajustar según necesidades del proyecto)
if [ -d "$ROOT_DIR/deploy/scripts" ]; then
    if [ -f "$ROOT_DIR/deploy/scripts/add_package.sh" ]; then
        cp "$ROOT_DIR/deploy/scripts/add_package.sh" "$ROOT_DIR/$DIST_DIR_NAME"
        echo "  ✓ add_package.sh"
    fi
    
    if [ -d "$ROOT_DIR/deploy/scripts/cloudwatch" ]; then
        cp -r "$ROOT_DIR/deploy/scripts/cloudwatch" "$ROOT_DIR/$DIST_DIR_NAME/cloudwatch"
        echo "  ✓ cloudwatch/"
    fi
fi

echo "Packaging complete."
echo "Package location: $ROOT_DIR/$DIST_DIR_NAME/"

# Subida opcional a la nube
if [ -n "$UPLOAD_TO_CLOUD" ]; then
    echo ""
    echo "Uploading to cloud storage..."
    
    if [ -n "$CLOUD_UPLOAD_COMMAND" ]; then
        # Usar comando personalizado
        eval "$CLOUD_UPLOAD_COMMAND"
    elif command -v aws &> /dev/null && [ -n "$ARTIFACTS_BUCKET" ] && [ -n "$ARTIFACTS_PREFIX" ]; then
        # AWS S3 (si está disponible y configurado)
        echo "Uploading to AWS S3..."
        aws s3 cp "$ROOT_DIR/$DIST_DIR_NAME/" "s3://$ARTIFACTS_BUCKET/$ARTIFACTS_PREFIX/$DIST_DIR_NAME/" --recursive
        echo "✅ Package uploaded to s3://$ARTIFACTS_BUCKET/$ARTIFACTS_PREFIX/$DIST_DIR_NAME/"
    elif command -v gsutil &> /dev/null && [ -n "$ARTIFACTS_BUCKET" ] && [ -n "$ARTIFACTS_PREFIX" ]; then
        # Google Cloud Storage (si está disponible y configurado)
        echo "Uploading to Google Cloud Storage..."
        gsutil -m cp -r "$ROOT_DIR/$DIST_DIR_NAME/" "gs://$ARTIFACTS_BUCKET/$ARTIFACTS_PREFIX/$DIST_DIR_NAME/"
        echo "✅ Package uploaded to gs://$ARTIFACTS_BUCKET/$ARTIFACTS_PREFIX/$DIST_DIR_NAME/"
    elif command -v az &> /dev/null && [ -n "$ARTIFACTS_BUCKET" ] && [ -n "$ARTIFACTS_PREFIX" ]; then
        # Azure Blob Storage (si está disponible y configurado)
        echo "Uploading to Azure Blob Storage..."
        az storage blob upload-batch \
            --destination "$ARTIFACTS_PREFIX/$DIST_DIR_NAME" \
            --source "$ROOT_DIR/$DIST_DIR_NAME" \
            --account-name "$ARTIFACTS_BUCKET"
        echo "✅ Package uploaded to Azure"
    else
        echo "⚠️  Warning: Cloud upload requested but no suitable method found."
        echo "   Configure CLOUD_UPLOAD_COMMAND or install AWS CLI / gsutil / Azure CLI"
    fi
else
    echo ""
    echo "ℹ️  Cloud upload skipped. Set UPLOAD_TO_CLOUD=1 to enable."
    echo "   Package is available at: $ROOT_DIR/$DIST_DIR_NAME/"
fi

echo "=========================================="
echo "✅ Packaging complete!"
echo "=========================================="
