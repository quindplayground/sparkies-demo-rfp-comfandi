from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.base import (
    IChangelogStrategy,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_date_filter import (
    CreateChangelogWithDateFilter,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_iceberg_sp import (
    CreateChangelogWithIcebergSP,
)


class StrategyFactory:
    """Factory class for creating changelog strategies."""

    MAP_STRATEGY: dict[str, type[IChangelogStrategy]] = {
        "iceberg_sp": CreateChangelogWithIcebergSP,
        "date_filter": CreateChangelogWithDateFilter,
    }

    @classmethod
    def get_strategy(cls, strategy_name: str) -> type[IChangelogStrategy]:
        """Get a changelog strategy by name.

        Args:
            strategy_name: Name of the strategy to create.

        Returns:
            The requested changelog strategy class.

        Raises:
            ValueError: If the strategy name is invalid.
        """
        if strategy_name not in cls.MAP_STRATEGY:
            raise ValueError(f"Invalid changelog strategy name: {strategy_name}")
        return cls.MAP_STRATEGY[strategy_name]

    def __getitem__(self, strategy_name: str) -> type[IChangelogStrategy]:
        """Get a changelog strategy by name using bracket notation.

        Args:
            strategy_name: Name of the strategy to create.

        Returns:
            The requested changelog strategy class.
        """
        return self.get_strategy(strategy_name)

    def __contains__(self, strategy_name: str) -> bool:
        """Check if a changelog strategy exists.

        Args:
            strategy_name: Name of the strategy to check.

        Returns:
            True if the strategy exists, False otherwise.
        """
        return strategy_name in self.MAP_STRATEGY
