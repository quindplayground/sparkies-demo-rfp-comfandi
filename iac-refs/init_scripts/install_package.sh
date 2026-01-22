#!/bin/bash
# Script de inicialización para instalar el paquete Python desde almacenamiento en la nube
#
# Este script se ejecuta durante la inicialización del cluster y:
# 1. Descarga el directorio dist/ desde almacenamiento en la nube
# 2. Detecta el archivo wheel más reciente
# 3. Instala el paquete usando pip
#
# Uso:
#   Este script se llama automáticamente durante la inicialización del cluster.
#   Recibe como argumento el URI del directorio dist/ en la nube
#
# Variables configurables:
# - TARGET_DIR: Directorio donde se descargan los archivos (default: /home/hadoop/working_dir)
# - PYTHON: Ruta al ejecutable de Python (default: /usr/bin/python3.11)
# - DOWNLOAD_METHOD: Método de descarga (auto, aws, gcp, azure, custom) (default: auto)
#
# Ejemplos de uso:
#   # AWS S3
#   ./install_package.sh s3://your-bucket/assets/your-project/dist/
#
#   # Google Cloud Storage
#   ./install_package.sh gs://your-bucket/assets/your-project/dist/
#
#   # Azure Blob Storage
#   ./install_package.sh https://your-account.blob.core.windows.net/container/path/
#
#   # Comando personalizado
#   DOWNLOAD_METHOD=custom CUSTOM_DOWNLOAD_CMD="curl -o" ./install_package.sh https://example.com/dist/

set -e

# Validar argumento
if [ -z "$1" ]; then
    echo "Error: URI del almacenamiento no especificado"
    echo "Uso: $0 <uri-del-almacenamiento>"
    echo "Ejemplos:"
    echo "  $0 s3://bucket/path/to/dist/"
    echo "  $0 gs://bucket/path/to/dist/"
    echo "  $0 https://account.blob.core.windows.net/container/path/"
    exit 1
fi

STORAGE_URI="$1"

# Configuración
TARGET_DIR="${TARGET_DIR:-/home/hadoop/working_dir}"
PYTHON="${PYTHON:-/usr/bin/python3.11}"
PIP="$PYTHON -m pip"
DOWNLOAD_METHOD="${DOWNLOAD_METHOD:-auto}"

echo "=========================================="
echo "Installing Python Package from Cloud Storage"
echo "Storage URI: $STORAGE_URI"
echo "Target Directory: $TARGET_DIR"
echo "Python: $PYTHON"
echo "=========================================="

# Crear directorio de destino
echo "Creating target directory..."
sudo mkdir -p "$TARGET_DIR"

# Detectar método de descarga automáticamente si es "auto"
if [ "$DOWNLOAD_METHOD" = "auto" ]; then
    if [[ "$STORAGE_URI" == s3://* ]]; then
        DOWNLOAD_METHOD="aws"
    elif [[ "$STORAGE_URI" == gs://* ]]; then
        DOWNLOAD_METHOD="gcp"
    elif [[ "$STORAGE_URI" == https://*.blob.core.windows.net/* ]] || [[ "$STORAGE_URI" == https://*.blob.core.chinacloudapi.cn/* ]]; then
        DOWNLOAD_METHOD="azure"
    else
        DOWNLOAD_METHOD="custom"
    fi
fi

# Descargar desde almacenamiento en la nube
echo "Downloading dist directory from cloud storage..."
case "$DOWNLOAD_METHOD" in
    aws)
        if ! command -v aws &> /dev/null; then
            echo "Error: AWS CLI no está instalado"
            exit 1
        fi
        echo "Using AWS S3..."
        sudo aws s3 cp --recursive "$STORAGE_URI" "$TARGET_DIR"
        ;;
    gcp)
        if ! command -v gsutil &> /dev/null; then
            echo "Error: gsutil no está instalado"
            exit 1
        fi
        echo "Using Google Cloud Storage..."
        sudo gsutil -m cp -r "$STORAGE_URI" "$TARGET_DIR"
        ;;
    azure)
        if ! command -v az &> /dev/null; then
            echo "Error: Azure CLI no está instalado"
            exit 1
        fi
        echo "Using Azure Blob Storage..."
        # Azure requiere parsear el URI y usar az storage blob download-batch
        sudo az storage blob download-batch \
            --source "$(echo "$STORAGE_URI" | sed 's|https://[^/]*/||')" \
            --destination "$TARGET_DIR" \
            --account-name "$(echo "$STORAGE_URI" | sed 's|https://\([^.]*\).*|\1|')"
        ;;
    custom)
        if [ -z "$CUSTOM_DOWNLOAD_CMD" ]; then
            echo "Error: CUSTOM_DOWNLOAD_CMD no está configurado para método custom"
            exit 1
        fi
        echo "Using custom download command..."
        eval "$CUSTOM_DOWNLOAD_CMD \"$STORAGE_URI\" \"$TARGET_DIR\""
        ;;
    *)
        echo "Error: Método de descarga desconocido: $DOWNLOAD_METHOD"
        echo "Métodos soportados: auto, aws, gcp, azure, custom"
        exit 1
        ;;
esac

# Detectar el archivo wheel más reciente (por fecha de modificación)
WHEEL_PATH=$(ls -t "$TARGET_DIR"/*.whl 2>/dev/null | head -n1)

# Alternativa: por orden de versión en el nombre (descomentar si prefieres esta opción)
# WHEEL_PATH=$(find "$TARGET_DIR" -maxdepth 1 -type f -name "*.whl" | sort -V | tail -n1)

if [[ -z "$WHEEL_PATH" ]]; then
  echo "Error: No wheel file found in $TARGET_DIR"
    echo "Please ensure the dist/ directory contains a .whl file"
  exit 1
fi

echo "Detected latest wheel: $WHEEL_PATH"

# Verificar e instalar pip si es necesario
if ! sudo $PYTHON -m pip --version &> /dev/null; then
    echo "pip not found for $PYTHON, installing via ensurepip..."
    sudo $PYTHON -m ensurepip --upgrade
fi

# Actualizar pip
echo "Upgrading pip..."
sudo $PIP install --upgrade pip

# Instalar el paquete
echo "Installing the wheel package..."
sudo $PIP install --no-cache-dir "$WHEEL_PATH"

echo "=========================================="
echo "✅ Wheel installed successfully!"
echo "Package: $WHEEL_PATH"
echo "=========================================="
