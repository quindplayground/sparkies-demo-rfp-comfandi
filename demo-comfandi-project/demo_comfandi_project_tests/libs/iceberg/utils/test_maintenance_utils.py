import re
from datetime import datetime, timedelta, timezone

import pytest

from demo_comfandi_project.libs.iceberg.utils.maintenance_utils import (
    run_daily_maintenance,
    run_weekly_maintenance,
)


class FakeDF:
    def __init__(self, rows: list[list[str]]):
        self._rows = rows

    def limit(self, n: int):
        return FakeDF(self._rows[:n])

    def collect(self):
        # Return list of simple row-like sequences
        return [tuple(r) for r in self._rows]

    # Needed for fallback SHOW TBLPROPERTIES (key, value)
    def filter(self, condition):  # pragma: no cover - simple passthrough not evaluated
        # Very small emulation for props_df.filter(props_df.key == prop)
        # We rely on rows stored as [key, value]
        # The call pattern is props_df.filter(props_df.key == prop)
        # So condition is a FakeDF already. Just return it when condition is FakeDF
        if isinstance(condition, FakeDF):
            return condition
        # Fallback: return self if unexpected
        return self


class FakeSpark:
    def __init__(self):
        # Simple in-memory table properties store: {table_id: {key: value}}
        self.props: dict[str, dict[str, str]] = {}
        self.queries: list[str] = []
        # Flags to simulate errors
        self.fail_direct_show: set[str] = (
            set()
        )  # tables for which direct SHOW TBLPROPERTIES(table('key')) fails

    def sql(self, query: str):
        self.queries.append(query)

        # ALTER TABLE ... SET TBLPROPERTIES ('k'='v')
        m = re.match(
            r"\s*ALTER\s+TABLE\s+([\w\.\-]+)\s+SET\s+TBLPROPERTIES\s*\(\s*'([^']+)'\s*=\s*'([^']+)'\s*\)\s*",
            query,
            re.I,
        )
        if m:
            table_id, key, value = m.group(1), m.group(2), m.group(3)
            self.props.setdefault(table_id, {})[key] = value
            return FakeDF([])

        # SHOW TBLPROPERTIES table('key')
        m = re.match(
            r"\s*SHOW\s+TBLPROPERTIES\s+([\w\.\-]+)\s*\(\s*'([^']+)'\s*\)\s*",
            query,
            re.I,
        )
        if m:
            table_id, key = m.group(1), m.group(2)
            if table_id in self.fail_direct_show:
                raise Exception("direct show failed")
            value = self.props.get(table_id, {}).get(key)
            return FakeDF([[value]] if value is not None else [])

        # SHOW TBLPROPERTIES table
        m = re.match(r"\s*SHOW\s+TBLPROPERTIES\s+([\w\.\-]+)\s*", query, re.I)
        if m:
            table_id = m.group(1)
            rows = [[k, v] for k, v in self.props.get(table_id, {}).items()]
            return FakeDF(rows)

        # CALL procedures → just record
        if re.search(r"CALL\s+\w+\.system\.expire_snapshots", query, re.I):
            return FakeDF([])
        if re.search(r"CALL\s+\w+\.system\.remove_orphan_files", query, re.I):
            return FakeDF([])
        if re.search(r"CALL\s+\w+\.system\.rewrite_manifests", query, re.I):
            return FakeDF([])
        if re.search(r"CALL\s+\w+\.system\.rewrite_data_files", query, re.I):
            return FakeDF([])
        if re.search(r"CALL\s+\w+\.system\.rewrite_position_delete_files", query, re.I):
            return FakeDF([])

        raise AssertionError(f"Unhandled query: {query}")


@pytest.fixture()
def spark():
    return FakeSpark()


def test_daily_runs_when_no_last_run_sets_property_and_calls_procedures(
    spark: FakeSpark,
):
    catalog = "local"
    table_id = "local.default.tbl"

    run_daily_maintenance(
        spark,
        catalog,
        table_id,
        num_snapshots_to_retain=2,
        orphan_files_older_than_days=1,
    )

    # Property should be written
    assert "maintenance.daily.last_run" in spark.props.get(table_id, {})
    # Procedures should be called
    assert any("expire_snapshots" in q for q in spark.queries)
    assert any("remove_orphan_files" in q for q in spark.queries)


def test_daily_skips_when_same_day(spark: FakeSpark):
    catalog = "local"
    table_id = "local.default.tbl"
    # set last_run to now
    now = datetime.now(timezone.utc).isoformat()
    spark.props.setdefault(table_id, {})["maintenance.daily.last_run"] = now
    spark.queries.clear()

    run_daily_maintenance(spark, catalog, table_id)

    # No procedures should run
    assert not any("expire_snapshots" in q for q in spark.queries)
    assert not any("remove_orphan_files" in q for q in spark.queries)


def test_weekly_runs_when_older_than_7_days_calls_procedures_and_sets_property(
    spark: FakeSpark,
):
    catalog = "local"
    table_id = "local.default.tbl"
    # last run 8 days ago
    eight_days_ago = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    spark.props.setdefault(table_id, {})["maintenance.weekly.last_run"] = eight_days_ago
    spark.queries.clear()

    run_weekly_maintenance(spark, catalog, table_id, target_file_size_mb=256)

    # Property should be updated
    assert "maintenance.weekly.last_run" in spark.props.get(table_id, {})
    # Procedures should be called
    assert any("rewrite_manifests" in q for q in spark.queries)
    assert any("rewrite_data_files" in q for q in spark.queries)
    assert any("rewrite_position_delete_files" in q for q in spark.queries)


def test_weekly_skips_within_same_week(spark: FakeSpark):
    catalog = "local"
    table_id = "local.default.tbl"
    # last run today
    spark.props.setdefault(table_id, {})["maintenance.weekly.last_run"] = datetime.now(
        timezone.utc
    ).isoformat()
    spark.queries.clear()

    run_weekly_maintenance(spark, catalog, table_id)

    assert not any("rewrite_manifests" in q for q in spark.queries)
    assert not any("rewrite_data_files" in q for q in spark.queries)
    assert not any("rewrite_position_delete_files" in q for q in spark.queries)


def test_get_table_property_direct_then_fallback(spark: FakeSpark):
    catalog = "local"
    table_id = "local.default.tbl"
    key = "maintenance.daily.last_run"

    # prepare property only in full listing map to force fallback
    spark.props.setdefault(table_id, {})[key] = "2025-01-01T00:00:00+00:00"
    spark.fail_direct_show.add(table_id)

    # Run daily, should read property via fallback and decide whether to run
    spark.queries.clear()
    run_daily_maintenance(spark, catalog, table_id)

    # Since last_run is in the past date, daily should run exactly once (procedures present)
    assert any("expire_snapshots" in q for q in spark.queries)
    assert any("remove_orphan_files" in q for q in spark.queries)
