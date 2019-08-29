from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class LogConfigModel(AbstractConfigModel):
    log_level: str = None
    log_flush_immediately: bool = None
