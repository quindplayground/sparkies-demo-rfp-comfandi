"""Command line arguments handling module."""

import argparse


def get_args() -> argparse.Namespace:
    """Parses command line arguments for environment and jobs configuration.

    Returns:
        Object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, required=True, help="Environment name")
    parser.add_argument(
        "--jobs",
        required=True,
        help=(
            "Provide a comma-separated list of jobs. Each entity is a value "
            "to be passed as input to the job. This is a required argument."
        ),
        type=lambda entity: list(entity.split(",")),
    )
    return parser.parse_args()
