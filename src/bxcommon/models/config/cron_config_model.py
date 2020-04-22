from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class CronConfigModel(AbstractConfigModel):
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    throughput_stats_interval: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    info_stats_interval: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    memory_stats_interval: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    ping_interval: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    config_update_interval: int = None
