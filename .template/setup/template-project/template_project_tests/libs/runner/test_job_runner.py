import pytest

from template_project.libs.exceptions import MissingJobDependencyError
from template_project.libs.runner.job_runner import JobRunner
from template_project.libs.runner.types import JobDefinition, Status


def create_test_job_with_dependencies(spark, job_names, dependencies=None):
    """
    Helper function to create test jobs with dependencies.

    Args:
        spark: Spark session
        job_names: List of job names to create
        dependencies: Dict mapping job name to list of dependencies

    Returns:
        Tuple of (jobs, execution_order)
    """
    execution_order = []

    def test_job(name: str, spark_session=None) -> Status:
        assert spark_session is not None
        execution_order.append(name)
        return Status(status_value="OK", message=f"Job {name} completed")

    jobs = []
    for name in job_names:
        job_def = JobDefinition(
            name=name, job=test_job, args={"name": name, "spark_session": spark}
        )
        if dependencies and name in dependencies:
            job_def.depends_on = dependencies[name]
        jobs.append(job_def)

    return jobs, execution_order


def test_job_runner_initialization(spark):
    """Test para verificar la inicialización correcta del JobRunner"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark})
    ]

    runner = JobRunner(jobs)
    assert len(runner.jobs) == 1
    assert runner._job_map["job1"].name == "job1"
    assert runner._job_map["job1"].job is test_job


def test_job_runner_dict_initialization(spark):
    """Test para verificar la inicialización con diccionarios"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [{"name": "job1", "job": test_job, "args": {"x": 1, "spark_session": spark}}]

    runner = JobRunner(jobs)
    assert len(runner.jobs) == 1
    assert isinstance(runner.jobs[0], JobDefinition)
    assert runner._job_map["job1"].name == "job1"


def test_job_runner_invalid_job_definition(spark):
    """Test para verificar el manejo de definiciones de job inválidas"""
    with pytest.raises(ValueError):
        JobRunner([{"invalid": "job"}])

    with pytest.raises(TypeError):
        JobRunner([123])  # type: ignore


def test_job_runner_duplicate_job_names(spark):
    """Test para verificar el manejo de nombres de jobs duplicados"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark}),
        JobDefinition(
            name="job1", job=test_job, args={"x": 2, "spark_session": spark}
        ),  # nombre duplicado
    ]

    with pytest.raises(ValueError) as exc_info:
        JobRunner(jobs)
    assert "Job names must be unique" in str(exc_info.value)


def test_job_runner_parallel_execution(spark):
    """Test para verificar la ejecución paralela de jobs"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(
            name=f"job_{i}", job=test_job, args={"x": i, "spark_session": spark}
        )
        for i in range(3)
    ]

    runner = JobRunner(jobs)
    result = runner.run([f"job_{i}" for i in range(3)], executor="parallel")

    assert result.status_value == "OK"
    assert result.message == "All jobs completed successfully."
    assert result.code == 200  # skipcq: PYL-W0143


def test_job_runner_sequential_execution(spark):
    """Test para verificar la ejecución secuencial de jobs"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(
            name=f"job_{i}", job=test_job, args={"x": i, "spark_session": spark}
        )
        for i in range(3)
    ]

    runner = JobRunner(jobs)
    result = runner.run([f"job_{i}" for i in range(3)], executor="sequential")

    assert result.status_value == "OK"
    assert result.message == "All jobs completed successfully."
    assert result.code == 200  # skipcq: PYL-W0143


def test_job_runner_invalid_executor(spark):
    """Test para verificar el manejo de ejecutores inválidos"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark})
    ]
    runner = JobRunner(jobs)

    with pytest.raises(ValueError) as exc_info:
        runner.run(["job1"], executor="invalid")
    assert "Invalid executor" in str(exc_info.value)


def test_job_runner_missing_jobs(spark):
    """Test para verificar el manejo de jobs no existentes"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark})
    ]
    runner = JobRunner(jobs)

    with pytest.raises(ValueError) as exc_info:
        runner.run(["non_existent_job"])
    assert "Jobs not found" in str(exc_info.value)


def test_job_runner_single_job_string(spark):
    """Test para verificar la ejecución de un solo job pasado como string"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark})
    ]
    runner = JobRunner(jobs)

    result = runner.run("job1")
    assert result.status_value == "OK"
    assert result.code == 200  # skipcq: PYL-W0143


def test_job_runner_with_dependencies(spark):
    """Test para verificar la ejecución de jobs con dependencias"""
    dependencies = {"job2": ["job1"], "job3": ["job2"]}
    jobs, execution_order = create_test_job_with_dependencies(
        spark, ["job1", "job2", "job3"], dependencies
    )

    runner = JobRunner(jobs)
    result = runner.run(["job3", "job1", "job2"], executor="sequential")

    assert result.status_value == "OK"
    assert result.code == 200  # skipcq: PYL-W0143
    # Verify that jobs were executed in the correct order
    assert execution_order == ["job1", "job2", "job3"]


def test_job_runner_missing_dependency(spark):
    """Test para verificar el manejo de dependencias faltantes"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(name="job1", job=test_job, args={"x": 1, "spark_session": spark}),
        JobDefinition(
            name="job2",
            job=test_job,
            args={"x": 2, "spark_session": spark},
            depends_on=["job3"],  # job3 is not in the job list
        ),
    ]

    runner = JobRunner(jobs)

    with pytest.raises(MissingJobDependencyError) as exc_info:
        runner.run(["job1", "job2"])

    assert "depends on 'job3'" in str(exc_info.value)


def test_job_runner_circular_dependency(spark):
    """Test para verificar el manejo de dependencias circulares"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(
            name="job1",
            job=test_job,
            args={"x": 1, "spark_session": spark},
            depends_on=["job3"],
        ),
        JobDefinition(
            name="job2",
            job=test_job,
            args={"x": 2, "spark_session": spark},
            depends_on=["job1"],
        ),
        JobDefinition(
            name="job3",
            job=test_job,
            args={"x": 3, "spark_session": spark},
            depends_on=["job2"],
        ),
    ]

    runner = JobRunner(jobs)

    with pytest.raises(ValueError) as exc_info:
        runner.run(["job1", "job2", "job3"])

    assert "Circular dependency" in str(exc_info.value)


def test_is_job_ready(spark):
    """Test para verificar el método _is_job_ready"""
    dependencies = {"job2": ["job1"], "job3": ["job1", "job2"]}
    jobs, _ = create_test_job_with_dependencies(
        spark, ["job1", "job2", "job3"], dependencies
    )

    runner = JobRunner(jobs)

    # job1 no tiene dependencias, siempre está listo
    assert runner._is_job_ready("job1", set())

    # job2 depende de job1
    assert not runner._is_job_ready("job2", set())
    assert runner._is_job_ready("job2", {"job1"})

    # job3 depende de job1 y job2
    assert not runner._is_job_ready("job3", set())
    assert not runner._is_job_ready("job3", {"job1"})
    assert not runner._is_job_ready("job3", {"job2"})
    assert runner._is_job_ready("job3", {"job1", "job2"})


def test_get_execution_order(spark):
    """Test para verificar el método get_execution_order"""
    dependencies = {"job2": ["job1"], "job3": ["job2"]}
    jobs, _ = create_test_job_with_dependencies(
        spark, ["job1", "job2", "job3"], dependencies
    )

    runner = JobRunner(jobs)

    # Verificar orden de ejecución para un solo job
    assert runner._get_execution_order("job1") == ["job1"]

    # Verificar orden de ejecución para múltiples jobs
    assert runner._get_execution_order(["job3", "job1", "job2"]) == [
        "job1",
        "job2",
        "job3",
    ]

    # Verificar que se lanza error para jobs no existentes
    with pytest.raises(ValueError) as exc_info:
        runner._get_execution_order("non_existent_job")
    assert "Jobs not found" in str(exc_info.value)

    # Verificar que se lanza error para dependencias circulares
    circular_dependencies = {"job1": ["job2"], "job2": ["job1"]}
    circular_jobs, _ = create_test_job_with_dependencies(
        spark, ["job1", "job2"], circular_dependencies
    )

    circular_runner = JobRunner(circular_jobs)
    with pytest.raises(ValueError) as exc_info:
        circular_runner._get_execution_order(["job1", "job2"])
    assert "Circular dependency" in str(exc_info.value)


def test_job_runner_auto_include_dependencies(spark):
    """Test para verificar que las dependencias se incluyen automáticamente"""
    dependencies = {"job2": ["job1"], "job3": ["job2"]}
    jobs, execution_order = create_test_job_with_dependencies(
        spark, ["job1", "job2", "job3"], dependencies
    )

    runner = JobRunner(jobs)
    # Solo pasamos job3, pero debería incluir automáticamente job1 y job2
    result = runner.run(["job3"], executor="sequential")

    assert result.status_value == "OK"
    assert result.code == 200  # skipcq: PYL-W0143
    # Verificar que todos los jobs se ejecutaron en el orden correcto
    assert execution_order == ["job1", "job2", "job3"]


def test_job_runner_auto_include_multiple_dependencies(spark):
    """Test para verificar la inclusión automática de múltiples dependencias"""
    execution_order = []

    def test_job(name: str, spark_session=None) -> Status:
        assert spark_session is not None
        execution_order.append(name)
        return Status(status_value="OK", message=f"Job {name} completed")

    jobs = [
        JobDefinition(
            name="base_job",
            job=test_job,
            args={"name": "base_job", "spark_session": spark},
        ),
        JobDefinition(
            name="dependent_job1",
            job=test_job,
            args={"name": "dependent_job1", "spark_session": spark},
            depends_on=["base_job"],
        ),
        JobDefinition(
            name="dependent_job2",
            job=test_job,
            args={"name": "dependent_job2", "spark_session": spark},
            depends_on=["base_job"],
        ),
        JobDefinition(
            name="final_job",
            job=test_job,
            args={"name": "final_job", "spark_session": spark},
            depends_on=["dependent_job1", "dependent_job2"],
        ),
    ]

    runner = JobRunner(jobs)
    # Solo pasamos final_job, pero debería incluir todas las dependencias
    result = runner.run(["final_job"], executor="sequential")

    assert result.status_value == "OK"
    assert result.code == 200  # skipcq: PYL-W0143
    # Verificar que base_job se ejecuta primero, seguido por dependent_job1 y dependent_job2
    # y finalmente final_job
    assert execution_order[0] == "base_job"
    assert set(execution_order[1:3]) == {"dependent_job1", "dependent_job2"}
    assert execution_order[3] == "final_job"


def test_job_runner_missing_dependency_in_definitions(spark):
    """Test para verificar el manejo de dependencias que no existen en las definiciones"""

    def test_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(
            name="job1",
            job=test_job,
            args={"x": 1, "spark_session": spark},
            depends_on=["non_existent_job"],  # job que no existe en las definiciones
        )
    ]

    runner = JobRunner(jobs)

    with pytest.raises(MissingJobDependencyError) as exc_info:
        runner.run(["job1"])

    assert "depends on 'non_existent_job'" in str(exc_info.value)


def test_job_runner_dependency_failure_handling(spark):
    """Test para verificar que cuando falla una dependencia, el job dependiente no se ejecuta"""
    execution_order = []

    def failing_job(name: str, spark_session=None) -> Status:
        """Job que siempre falla"""
        assert spark_session is not None
        execution_order.append(name)
        raise RuntimeError(f"Job {name} failed intentionally")

    def successful_job(name: str, spark_session=None) -> Status:
        """Job que siempre funciona"""
        assert spark_session is not None
        execution_order.append(name)
        return Status(status_value="OK", message="Success")

    def dependent_job(name: str, spark_session=None) -> Status:
        """Job que depende de otros"""
        assert spark_session is not None
        execution_order.append(name)
        return Status(status_value="OK", message="Dependent job completed")

    jobs = [
        JobDefinition(
            name="base_job",
            job=failing_job,  # Este job fallará
            args={"name": "base_job", "spark_session": spark},
        ),
        JobDefinition(
            name="dependent_job",
            job=dependent_job,
            args={"name": "dependent_job", "spark_session": spark},
            depends_on=["base_job"],  # Depende de base_job que fallará
        ),
        JobDefinition(
            name="successful_job",
            job=successful_job,
            args={"name": "successful_job", "spark_session": spark},
            depends_on=[
                "dependent_job"
            ],  # Depende de dependent_job que no debería ejecutarse
        ),
    ]

    runner = JobRunner(jobs)
    result = runner.run(["successful_job"], executor="sequential")

    # El resultado debe ser ERROR
    assert result.status_value == "ERROR"
    assert result.code == 500  # skipcq: PYL-W0143

    # Solo base_job debe haberse ejecutado (y fallado)
    # dependent_job y successful_job NO deben haberse ejecutado
    assert execution_order == ["base_job"]
    assert "dependent_job" not in execution_order
    assert "successful_job" not in execution_order


def test_job_runner_dependency_failure_handling_multithread(spark):
    """Test para verificar que el ejecutor multithread también maneja correctamente los fallos de dependencias"""
    execution_order = []

    def failing_job(name: str, spark_session=None) -> Status:
        """Job que siempre falla"""
        assert spark_session is not None
        execution_order.append(name)
        raise RuntimeError(f"Job {name} failed intentionally")

    def dependent_job(name: str, spark_session=None) -> Status:
        """Job que depende de otros"""
        assert spark_session is not None
        execution_order.append(name)
        return Status(status_value="OK", message="Dependent job completed")

    jobs = [
        JobDefinition(
            name="base_job",
            job=failing_job,  # Este job fallará
            args={"name": "base_job", "spark_session": spark},
        ),
        JobDefinition(
            name="dependent_job",
            job=dependent_job,
            args={"name": "dependent_job", "spark_session": spark},
            depends_on=["base_job"],  # Depende de base_job que fallará
        ),
    ]

    runner = JobRunner(jobs)
    # Usar multithread, pero debería cambiar automáticamente a secuencial
    result = runner.run(["dependent_job"], executor="parallel")

    # El resultado debe ser ERROR
    assert result.status_value == "ERROR"
    assert result.code == 500  # skipcq: PYL-W0143

    # Solo base_job debe haberse ejecutado (y fallado)
    # dependent_job NO debe haberse ejecutado
    assert execution_order == ["base_job"]
    assert "dependent_job" not in execution_order


def test_job_runner_dependency_failure_behavior_comparison(spark):
    """Test que demuestra la diferencia entre el comportamiento anterior y el nuevo"""
    execution_order = []

    def failing_job(name: str, spark_session=None) -> Status:
        """Job que siempre falla"""
        assert spark_session is not None
        execution_order.append(f"EXECUTED_{name}")
        raise RuntimeError(f"Job {name} failed intentionally")

    def dependent_job(name: str, spark_session=None) -> Status:
        """Job que depende de otros"""
        assert spark_session is not None
        execution_order.append(f"EXECUTED_{name}")
        return Status(status_value="OK", message="Dependent job completed")

    def final_job(name: str, spark_session=None) -> Status:
        """Job final que depende de dependent_job"""
        assert spark_session is not None
        execution_order.append(f"EXECUTED_{name}")
        return Status(status_value="OK", message="Final job completed")

    jobs = [
        JobDefinition(
            name="base_job",
            job=failing_job,  # Este job fallará
            args={"name": "base_job", "spark_session": spark},
        ),
        JobDefinition(
            name="dependent_job",
            job=dependent_job,
            args={"name": "dependent_job", "spark_session": spark},
            depends_on=["base_job"],  # Depende de base_job que fallará
        ),
        JobDefinition(
            name="final_job",
            job=final_job,
            args={"name": "final_job", "spark_session": spark},
            depends_on=[
                "dependent_job"
            ],  # Depende de dependent_job que no debería ejecutarse
        ),
    ]

    runner = JobRunner(jobs)

    result = runner.run(["final_job"], executor="sequential")

    # Verificar que el resultado es ERROR
    assert result.status_value == "ERROR"
    assert result.code == 500  # skipcq: PYL-W0143

    # Verificar que solo se ejecutó base_job (y falló)
    # dependent_job y final_job NO deben haberse ejecutado
    assert execution_order == ["EXECUTED_base_job"]
    assert "EXECUTED_dependent_job" not in execution_order
    assert "EXECUTED_final_job" not in execution_order

    # Verificar que el mensaje de error contiene información sobre los jobs que se saltaron
    assert (
        "Job 'dependent_job' cannot execute because some dependencies failed"
        in result.message
    )
    assert (
        "Job 'final_job' cannot execute because some dependencies failed"
        in result.message
    )
