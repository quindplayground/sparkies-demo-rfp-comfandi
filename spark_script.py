import os
import argparse
import sys

# IMPORTAMOS TU JOB REAL
from demo_comfandi_project.flows.demo_comfandi.job import demo_comfandi_job

from demo_comfandi_project.libs.runner import JobRunner
from demo_comfandi_project.libs.resources import get_vars_resource, SparkResource
from demo_comfandi_project.libs.utils import get_package_resource_path

# Función auxiliar para parsear argumentos extra que manda Dataproc
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument("--jobs", default="demo_comfandi")
    # Estos son los nuevos argumentos que manda tu Cloud Function
    parser.add_argument("--input_file", required=False)
    parser.add_argument("--output_folder", required=False)
    
    # parse_known_args permite ignorar argumentos internos de Spark
    args, _ = parser.parse_known_args()
    return args

if __name__ == "__main__":
    os.environ["LOG_LEVEL"] = "INFO"

    # 1. Inicializar Spark
    spark = SparkResource(new_session=True)
    spark.sparkContext.setCheckpointDir("hdfs:///tmp/local_checkpoints")

    # 2. Obtener Argumentos
    args = parse_args()
    print(f"🚀 Iniciando Spark Script. Input recibido: {args.input_file}")

    # 3. Cargar Configuración Base (default.toml)
    # Ajusta la ruta "flows/demo_comfandi/config" si tu carpeta se llama distinto
    vars_instance = get_vars_resource(
        env=args.env,
        config_paths=["flows/demo_comfandi/config"] 
    )

    # 4. INYECCIÓN DE DEPENDENCIAS (El Truco)
    # Si recibimos un archivo, sobrescribimos la configuración en memoria
    if args.input_file:
        print(f"⚙️ Sobrescribiendo config input con: {args.input_file}")
        
        # Actualizamos el diccionario de configuración 'vars'
        # Esto hace que vars_instance.vars.input.path exista
        if "input" not in vars_instance.vars:
            vars_instance.vars["input"] = {}
            
        vars_instance.vars["input"]["path"] = args.input_file
        # Limpiamos table_id para que extract.py entre al IF correcto
        vars_instance.vars["input"]["table_id"] = None

    if args.output_folder:
        if "output" not in vars_instance.vars:
            vars_instance.vars["output"] = {}
        vars_instance.vars["output"]["path"] = args.output_folder

    # 5. Definir Jobs
    job_defs = [
        {
            "name": "demo_comfandi",  # Nombre del job
            "job": demo_comfandi_job, # Tu función importada de job.py
            "args": {
                "spark": spark,
                "vars_instance": vars_instance # Pasamos la config modificada
            },
        },
    ]

    # 6. Ejecutar
    runner = JobRunner(job_defs)
    
    # Si args.jobs viene vacío o es "all", ejecutamos el definido arriba
    jobs_to_run = [args.jobs] if args.jobs else ["demo_comfandi"]
    
    result = runner.run(jobs_to_run, executor="sequential")

    print(result.model_dump_json())
