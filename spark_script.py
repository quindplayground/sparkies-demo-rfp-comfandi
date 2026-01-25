import os

# Import your job functions here
# from demo_comfandi_project.flows.stage.your_flow.job import your_job_function

from demo_comfandi_project.libs.args import get_args
from demo_comfandi_project.libs.runner import JobRunner
from demo_comfandi_project.libs.resources import get_vars_resource, SparkResource
from demo_comfandi_project.libs.utils import get_package_resource_path
from demo_comfandi_project.libs.aws.s3 import download_s3_folder_to_local
from demo_comfandi_project.libs.validation import validate_json_parameters
from demo_comfandi_project.libs.exceptions import ValidationError


if __name__ == "__main__":
    # Set log level
    os.environ["LOG_LEVEL"] = "INFO"

    # Initialize Spark Resource
    # This resource manages the Spark session.
    spark = SparkResource(new_session=True)

    # Set checkpoint directory if needed
    spark.sparkContext.setCheckpointDir("hdfs:///tmp/local_checkpoints")

    # Parse command line arguments
    args = get_args()

    # Get the path to the package resources
    # Ensure 'demo_comfandi_project' matches your actual package name
    root_path = get_package_resource_path("demo_comfandi_project")

    # Initialize Variables Resources
    # Create a vars resource for each of your flows.
    # This loads configuration from the specified paths.

    # Example:
    # my_flow_vars = get_vars_resource(
    #     env=args.env,
    #     config_paths=[
    #         "flows/stage/my_flow/config",
    #         "parameters"
    #     ]
    # )

    # Define Jobs
    # List all the jobs you want to run.
    # Each job definition is a dictionary containing:
    # - name: Unique name for the job
    # - job: The job function to execute
    # - args: Arguments to pass to the job function (usually spark and vars_instance)
    # - depends_on: (Optional) List of job names that this job depends on

    job_defs = [
        # {
        #     "name": "my_flow_job",
        #     "job": your_job_function,
        #     "args": {
        #         "spark": spark,
        #         "vars_instance": my_flow_vars
        #     },
        #     # "depends_on": ["other_job"]
        # },
    ]

    # Initialize JobRunner
    runner = JobRunner(job_defs)

    # Run jobs
    # args.jobs specifies which jobs to run (or all if empty)
    # executor="sequential" runs jobs one after another based on dependencies
    result = runner.run(args.jobs, executor="sequential")

    # Print result
    print(result.model_dump_json())
