from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class StatsConfigModel(AbstractConfigModel):
    enable_block_stats: bool = None
    enable_tx_stats: bool = None
    tx_stats_percentage: float = None
    number_of_oldest_txs_in_cache_to_log: int = None
    calculate_actual_obj_size: bool = None
