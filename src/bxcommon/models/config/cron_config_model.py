from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class CronConfigModel(AbstractConfigModel):
    throughput_stats_interval: int = None
    info_stats_interval: int = None
    memory_stats_interval: int = None
    ping_interval: int = None
    config_update_interval: int = None
