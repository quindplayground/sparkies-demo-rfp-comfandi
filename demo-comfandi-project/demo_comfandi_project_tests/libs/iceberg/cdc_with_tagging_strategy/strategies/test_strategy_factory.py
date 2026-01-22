import pytest

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.factory import (
    StrategyFactory,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_iceberg_sp import (
    CreateChangelogWithIcebergSP,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_date_filter import (
    CreateChangelogWithDateFilter,
)


def test_map_strategy_contains_correct_strategies():
    """Test that MAP_STRATEGY contains the correct strategies."""
    assert "iceberg_sp" in StrategyFactory.MAP_STRATEGY
    assert "date_filter" in StrategyFactory.MAP_STRATEGY
    assert StrategyFactory.MAP_STRATEGY["iceberg_sp"] == CreateChangelogWithIcebergSP
    assert StrategyFactory.MAP_STRATEGY["date_filter"] == CreateChangelogWithDateFilter


def test_get_strategy_valid_strategies():
    """Test get_strategy with valid strategy names."""
    assert StrategyFactory.get_strategy("iceberg_sp") == CreateChangelogWithIcebergSP
    assert StrategyFactory.get_strategy("date_filter") == CreateChangelogWithDateFilter


def test_get_strategy_invalid_strategy():
    """Test get_strategy with invalid strategy name."""
    with pytest.raises(ValueError) as exc_info:
        StrategyFactory.get_strategy("invalid_strategy")

    assert "Invalid changelog strategy name: invalid_strategy" in str(exc_info.value)


def test_getitem_valid_strategies():
    """Test __getitem__ with valid strategy names."""
    factory = StrategyFactory()

    assert factory["iceberg_sp"] == CreateChangelogWithIcebergSP
    assert factory["date_filter"] == CreateChangelogWithDateFilter


def test_getitem_invalid_strategy():
    """Test __getitem__ with invalid strategy name."""
    factory = StrategyFactory()

    with pytest.raises(ValueError) as exc_info:
        factory["invalid_strategy"]

    assert "Invalid changelog strategy name: invalid_strategy" in str(exc_info.value)


def test_contains_valid_strategies():
    """Test __contains__ with valid strategy names."""
    factory = StrategyFactory()

    assert "iceberg_sp" in factory
    assert "date_filter" in factory


def test_contains_invalid_strategy():
    """Test __contains__ with invalid strategy name."""
    factory = StrategyFactory()

    assert "invalid_strategy" not in factory


def test_contains_case_sensitive():
    """Test __contains__ is case sensitive."""
    factory = StrategyFactory()

    assert "iceberg_sp" in factory
    assert "Iceberg_SP" not in factory
    assert "ICEBERG_SP" not in factory


def test_factory_is_singleton_like():
    """Test that StrategyFactory behaves like a singleton (no state)."""
    factory1 = StrategyFactory()
    factory2 = StrategyFactory()

    # Both instances should behave the same way
    assert factory1["iceberg_sp"] == factory2["iceberg_sp"]
    assert factory1["date_filter"] == factory2["date_filter"]
    assert "iceberg_sp" in factory1
    assert "iceberg_sp" in factory2
