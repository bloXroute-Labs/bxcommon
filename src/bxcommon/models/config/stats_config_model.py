from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class StatsConfigModel(AbstractConfigModel):
    # pyre-fixme[8]: Attribute has type `bool`; used as `None`.
    enable_block_stats: bool = None
    # pyre-fixme[8]: Attribute has type `bool`; used as `None`.
    enable_tx_stats: bool = None
    # pyre-fixme[8]: Attribute has type `float`; used as `None`.
    tx_stats_percentage: float = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    number_of_oldest_txs_in_cache_to_log: int = None
    # pyre-fixme[8]: Attribute has type `bool`; used as `None`.
    calculate_actual_obj_size: bool = None
